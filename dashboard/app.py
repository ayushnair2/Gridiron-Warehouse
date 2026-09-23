import sys
from pathlib import Path

import altair as alt
import pandas as pd
import statsmodels.api as sm
import streamlit as st
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

# ingest/ is a plain directory, not a package: put it on the path and reuse the
# key-pair connection from db.py rather than duplicating the auth here
sys.path.append(str(REPO_ROOT / "ingest"))
# db.py calls load_dotenv() with no path, which resolves against the working
# directory; load the repo .env explicitly so the app works from anywhere
load_dotenv(REPO_ROOT / ".env")

from db import connect  # noqa: E402


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    conn = connect()
    try:
        return conn.cursor().execute(sql).fetch_pandas_all()
    finally:
        conn.close()


st.title("Gridiron Warehouse")

SEASONS = query(
    "select distinct season from NFL_ANALYTICS.ANALYTICS.FCT_TEAM_GAME order by season desc"
)["SEASON"].tolist()

team_tab, qb_tab, reg_tab = st.tabs(
    ["Team EPA Rankings", "QB Efficiency", "Early vs Late EPA"]
)

with team_tab:
    season = st.selectbox("Season", SEASONS, index=0, key="season_team")

    # rates are weighted by plays, not averaged across games: a 40-play game and a
    # 75-play game are not equal evidence. success_rate is stored per game, so it is
    # multiplied back by plays to recover the underlying success count.
    teams = query(f"""
        select
            team,
            sum(total_epa) / sum(plays) as epa_per_play,
            sum(success_rate * plays) / sum(plays) as success_rate,
            count(*) as games
        from NFL_ANALYTICS.ANALYTICS.FCT_TEAM_GAME
        where season = {season}
          -- regular season only: playoff games would give contenders more games and
          -- grade them against a tougher field than non-playoff teams
          and season_type = 'REG'
        group by team
        order by epa_per_play desc
    """)
    st.dataframe(
        teams.round({"EPA_PER_PLAY": 3, "SUCCESS_RATE": 3}),
        hide_index=True,
    )

with qb_tab:
    season = st.selectbox("Season", SEASONS, index=0, key="season_qb")

    # cpoe is stored as a per-game mean, so it is reweighted by that game's attempts.
    # this is an approximation: cpoe is undefined on ~9% of dropbacks (sacks,
    # throwaways), so attempts is not exactly its denominator. measured against
    # play-level truth the error averages 0.12 cpoe points; a plain AVG is off by up to 8.
    # nflverse pass_attempt is a pass-PLAY flag, so pass_attempts already counts sacks:
    # it is dropbacks, and epa/dropback needs no adjustment. official attempts, which
    # completion pct is measured against, are dropbacks minus sacks.
    qbs = query(f"""
        select
            player_name,
            sum(passing_epa) / sum(pass_attempts) as epa_per_dropback,
            sum(cpoe * pass_attempts) / sum(pass_attempts) as cpoe,
            sum(completions) / (sum(pass_attempts) - sum(sacks)) * 100 as completion_pct,
            sum(pass_attempts) - sum(sacks) as attempts,
            sum(pass_attempts) as dropbacks,
            count(*) as games
        from NFL_ANALYTICS.ANALYTICS.FCT_PLAYER_GAME
        where season = {season}
          and season_type = 'REG'
        group by player_name
        having sum(pass_attempts) >= 200
        order by epa_per_dropback desc
    """)
    st.dataframe(
        qbs.round({"EPA_PER_DROPBACK": 3, "CPOE": 3, "COMPLETION_PCT": 1}),
        hide_index=True,
    )

with reg_tab:
    st.caption(
        "Does the first half of a season predict the second? One point per team-season, "
        "pooled across all nine seasons (2016-2024 regular season)."
    )

    # split at week 9 rather than at a fixed game count: regular seasons ran 17 weeks
    # before 2021 and 18 after, so <=9 / >9 halves both eras sensibly
    splits = query("""
        select
            team,
            season,
            sum(case when week <= 9 then total_epa end)
                / nullif(sum(case when week <= 9 then plays end), 0) as early_epa,
            sum(case when week >  9 then total_epa end)
                / nullif(sum(case when week >  9 then plays end), 0) as late_epa,
            count_if(week <= 9) as early_games,
            count_if(week >  9) as late_games
        from NFL_ANALYTICS.ANALYTICS.FCT_TEAM_GAME
        where season_type = 'REG'
        group by team, season
    """)
    splits.columns = [c.lower() for c in splits.columns]
    # a team with a nearly empty half would be a high-leverage point built on noise
    fit_df = splits[(splits.early_games >= 3) & (splits.late_games >= 3)].dropna(
        subset=["early_epa", "late_epa"]
    )

    model = sm.OLS(
        fit_df.late_epa, sm.add_constant(fit_df.early_epa)
    ).fit()
    slope = model.params["early_epa"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Slope", f"{slope:.3f}")
    c2.metric("R-squared", f"{model.rsquared:.3f}")
    c3.metric("p-value", f"{model.pvalues['early_epa']:.2e}")
    c4.metric("Team-seasons", f"{len(fit_df)}")

    plot_df = fit_df.assign(fitted=model.fittedvalues)
    base = alt.Chart(plot_df)
    points = base.mark_circle(size=60, opacity=0.55, color="#2a78d6").encode(
        x=alt.X("early_epa:Q", title="EPA per play, weeks 1-9",
                scale=alt.Scale(zero=False)),
        y=alt.Y("late_epa:Q", title="EPA per play, weeks 10-18",
                scale=alt.Scale(zero=False)),
        tooltip=["team:N", "season:O",
                 alt.Tooltip("early_epa:Q", format=".3f"),
                 alt.Tooltip("late_epa:Q", format=".3f")],
    )
    line = base.mark_line(color="#eb6834", size=2).encode(
        x="early_epa:Q", y="fitted:Q"
    )
    st.altair_chart((points + line).properties(height=420), use_container_width=True)
    st.caption("Blue: one team-season. Orange: fitted OLS line.")

    with st.expander("Full OLS summary"):
        st.text(model.summary())

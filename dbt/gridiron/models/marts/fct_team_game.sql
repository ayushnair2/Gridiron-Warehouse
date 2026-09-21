-- offensive team-game: one row per possessing team per game
-- two-point conversions excluded for consistency with fct_player_game; rows with no
-- possessing team (no_play, end-of-period) are dropped so the grain has no null key
select
    posteam as team,
    game_id,
    max(season) as season,
    max(week) as week,
    max(season_type) as season_type,
    max(defteam) as opponent,
    max(home_team) as home_team,
    max(away_team) as away_team,
    count(*) as plays,
    sum(yards_gained) as total_yards,
    sum(pass_attempt) as pass_attempts,
    sum(complete_pass) as completions,
    sum(passing_yards) as passing_yards,
    sum(rush_attempt) as rush_attempts,
    sum(rushing_yards) as rushing_yards,
    -- fumble_lost is flagged on the play, not the fumbling team: only count it when
    -- the possessing team is the one that lost it (laterals, punt returns)
    sum(interception) + sum(case when fumbled_1_team = posteam then fumble_lost else 0 end) as turnovers,
    sum(touchdown) as touchdowns,
    sum(first_down) as first_downs,
    sum(epa) as total_epa,
    avg(epa) as epa_per_play,
    sum(case when pass_attempt = 1 then epa end) as pass_epa,
    sum(case when rush_attempt = 1 then epa end) as rush_epa,
    avg(success) as success_rate
from {{ ref('stg_pbp') }}
where posteam is not null
  and play_type in ('pass', 'run')
  and coalesce(two_point_attempt, 0) = 0
group by 1, 2

-- two-point conversions are excluded from all three roles: the NFL does not count
-- them toward official passing/rushing/receiving stats, and parity with
-- RAW.PLAYER_STATS only holds once they are filtered out
with passing as (

    select
        passer_player_id as player_id,
        game_id,
        max(passer_player_name) as player_name,
        max(season) as season,
        max(week) as week,
        max(season_type) as season_type,
        max(posteam) as team,
        max(defteam) as opponent,
        sum(pass_attempt) as pass_attempts,
        sum(complete_pass) as completions,
        sum(passing_yards) as passing_yards,
        sum(pass_touchdown) as passing_tds,
        sum(interception) as interceptions,
        sum(sack) as sacks,
        sum(air_yards) as air_yards,
        avg(cpoe) as cpoe,
        sum(epa) as passing_epa,
        avg(epa) as passing_epa_per_play,
        avg(success) as passing_success_rate
    from {{ ref('stg_pbp') }}
    where passer_player_id is not null
      and coalesce(two_point_attempt, 0) = 0
    group by 1, 2

),

rushing as (

    select
        rusher_player_id as player_id,
        game_id,
        max(rusher_player_name) as player_name,
        max(season) as season,
        max(week) as week,
        max(season_type) as season_type,
        max(posteam) as team,
        max(defteam) as opponent,
        sum(rush_attempt) as carries,
        sum(rushing_yards) as rushing_yards,
        sum(rush_touchdown) as rushing_tds,
        sum(epa) as rushing_epa,
        avg(epa) as rushing_epa_per_play,
        avg(success) as rushing_success_rate
    from {{ ref('stg_pbp') }}
    where rusher_player_id is not null
      and coalesce(two_point_attempt, 0) = 0
    group by 1, 2

),

receiving as (

    select
        receiver_player_id as player_id,
        game_id,
        max(receiver_player_name) as player_name,
        max(season) as season,
        max(week) as week,
        max(season_type) as season_type,
        max(posteam) as team,
        max(defteam) as opponent,
        count(*) as targets,
        sum(complete_pass) as receptions,
        sum(receiving_yards) as receiving_yards,
        sum(pass_touchdown) as receiving_tds,
        sum(epa) as receiving_epa,
        avg(epa) as receiving_epa_per_play,
        avg(success) as receiving_success_rate
    from {{ ref('stg_pbp') }}
    where receiver_player_id is not null
      and coalesce(two_point_attempt, 0) = 0
    group by 1, 2

)

select
    coalesce(passing.player_id, rushing.player_id, receiving.player_id) as player_id,
    coalesce(passing.game_id, rushing.game_id, receiving.game_id) as game_id,
    coalesce(passing.player_name, rushing.player_name, receiving.player_name) as player_name,
    coalesce(passing.season, rushing.season, receiving.season) as season,
    coalesce(passing.week, rushing.week, receiving.week) as week,
    coalesce(passing.season_type, rushing.season_type, receiving.season_type) as season_type,
    coalesce(passing.team, rushing.team, receiving.team) as team,
    coalesce(passing.opponent, rushing.opponent, receiving.opponent) as opponent,

    passing.pass_attempts,
    passing.completions,
    passing.passing_yards,
    passing.passing_tds,
    passing.interceptions,
    passing.sacks,
    passing.air_yards,
    passing.cpoe,
    passing.passing_epa,
    passing.passing_epa_per_play,
    passing.passing_success_rate,

    rushing.carries,
    rushing.rushing_yards,
    rushing.rushing_tds,
    rushing.rushing_epa,
    rushing.rushing_epa_per_play,
    rushing.rushing_success_rate,

    receiving.targets,
    receiving.receptions,
    receiving.receiving_yards,
    receiving.receiving_tds,
    receiving.receiving_epa,
    receiving.receiving_epa_per_play,
    receiving.receiving_success_rate

from passing
full outer join rushing
    on passing.player_id = rushing.player_id
    and passing.game_id = rushing.game_id
full outer join receiving
    on coalesce(passing.player_id, rushing.player_id) = receiving.player_id
    and coalesce(passing.game_id, rushing.game_id) = receiving.game_id

-- rosters are per player-season; keep the most recent season's descriptive attributes.
-- team is deliberately excluded: it changes per season and the facts carry it per game
with ranked as (

    select
        gsis_id as player_id,
        full_name as player_name,
        position,
        birth_date,
        college,
        height,
        weight,
        entry_year,
        rookie_year,
        draft_club,
        draft_number,
        row_number() over (
            partition by gsis_id
            order by season desc, week desc nulls last, team
        ) as rn
    from {{ ref('stg_rosters') }}
    where gsis_id is not null

)

select
    player_id,
    player_name,
    position,
    birth_date,
    college,
    height,
    weight,
    entry_year,
    rookie_year,
    draft_club,
    draft_number
from ranked
where rn = 1

-- sourced from the facts so every team code used by a fact has a dim row.
-- relocations (OAK/LV, SD/LAC, STL/LAR) are separate codes and stay separate.
-- no full team names: nothing ingested from nflverse carries them
select team
from (

    select team from {{ ref('fct_player_game') }}
    union
    select team from {{ ref('fct_team_game') }}

)
where team is not null

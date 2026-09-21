-- a receiver cannot catch more passes than were thrown their way
select
    player_id,
    game_id,
    receptions,
    targets
from {{ ref('fct_player_game') }}
where receptions > targets

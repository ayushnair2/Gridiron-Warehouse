-- a passer cannot complete more passes than they attempted
select
    player_id,
    game_id,
    completions,
    pass_attempts
from {{ ref('fct_player_game') }}
where completions > pass_attempts

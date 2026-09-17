import nflreadpy as nfl
from snowflake.connector.pandas_tools import write_pandas
from db import connect

SEASONS = list(range(2016, 2025))


def write(conn, df, table_name, **kwargs):
    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name=table_name,
        database="NFL_ANALYTICS",
        schema="RAW",
        auto_create_table=True,
        overwrite=True,
        # unquoted so Snowflake uppercases columns and dbt can reference them without quotes
        quote_identifiers=False,
        **kwargs,
    )
    print(f"{table_name}: success={success} nrows={nrows}")


def load_pbp(conn):
    write(conn, nfl.load_pbp(SEASONS).to_pandas(), "PBP")


def load_player_stats(conn):
    write(conn, nfl.load_player_stats(SEASONS).to_pandas(), "PLAYER_STATS")


def load_rosters(conn):
    write(conn, nfl.load_rosters(SEASONS).to_pandas(), "ROSTERS", use_logical_type=True)


def load_schedules(conn):
    write(conn, nfl.load_schedules(SEASONS).to_pandas(), "SCHEDULES")


if __name__ == "__main__":
    conn = connect()
    load_pbp(conn)
    load_player_stats(conn)
    load_rosters(conn)
    load_schedules(conn)
    conn.close()

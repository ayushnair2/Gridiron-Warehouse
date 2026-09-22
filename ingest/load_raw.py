import nflreadpy as nfl
import polars as pl
from snowflake.connector.pandas_tools import write_pandas
from db import connect

SEASONS = list(range(2016, 2025))


def write(conn, df, table_name, overwrite=True, **kwargs):
    # a String column that is all-null in this batch converts to object-of-None, which
    # Snowflake types as NUMBER; carry Polars' String dtype through so it lands as TEXT
    str_cols = [c for c, t in zip(df.columns, df.dtypes) if t == pl.String]
    pdf = df.to_pandas()
    pdf[str_cols] = pdf[str_cols].astype("string")

    success, nchunks, nrows, _ = write_pandas(
        conn,
        pdf,
        table_name=table_name,
        database="NFL_ANALYTICS",
        schema="RAW",
        auto_create_table=True,
        overwrite=overwrite,
        # unquoted so Snowflake uppercases columns and dbt can reference them without quotes
        quote_identifiers=False,
        **kwargs,
    )
    print(f"{table_name}: success={success} nrows={nrows}")
    return nrows


def load_pbp(conn):
    total = 0
    for season in SEASONS:
        # overwrite on the first season only, append after: a rerun's first write
        # clears any partial state left by a failed prior run, keeping reruns idempotent
        total += write(
            conn,
            nfl.load_pbp([season]),
            "PBP",
            overwrite=(season == SEASONS[0]),
        )
        print(f"  PBP {season} done, running total={total}")
    print(f"PBP: total nrows={total}")


def load_player_stats(conn):
    write(conn, nfl.load_player_stats(SEASONS), "PLAYER_STATS")


def load_rosters(conn):
    write(conn, nfl.load_rosters(SEASONS), "ROSTERS", use_logical_type=True)


def load_schedules(conn):
    write(conn, nfl.load_schedules(SEASONS), "SCHEDULES")


if __name__ == "__main__":
    conn = connect()
    load_pbp(conn)
    load_player_stats(conn)
    load_rosters(conn)
    load_schedules(conn)
    conn.close()

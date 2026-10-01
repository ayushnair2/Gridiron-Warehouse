from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

DBT_PROJECT_DIR = "/usr/local/airflow/dbt_project"

default_args = {
    "owner": "ayush",
    "retries": 0,
    "depends_on_past": False,
}

with DAG(
    dag_id="gridiron_pipeline",
    description="Weekly nflverse ELT: load raw, then build and test dbt models",
    # Tuesday 09:00 — after Monday night games have settled into the nflverse feed
    schedule="0 9 * * 2",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # one run at a time: ingest rewrites whole tables with overwrite=True, so two
    # concurrent runs race on the same Snowflake tables (and exhaust container memory)
    max_active_runs=1,
    default_args=default_args,
    tags=["gridiron", "elt"],
) as dag:

    ingest = BashOperator(
        task_id="ingest",
        bash_command="python /usr/local/airflow/ingest/load_raw.py",
    )

    # dbt build runs each model's tests before building its dependents, so a failed
    # test skips everything downstream and those marts keep their last good version
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps && dbt build",
    )

    ingest >> dbt_build

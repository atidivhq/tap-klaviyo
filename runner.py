"""Module providing a main method to orchestrate klaviyo data ingestion."""

import argparse
import json
import os
import os.path
import sys
from datetime import datetime

import pendulum

sys.path.insert(0, ".")

from secrets_manager import get_secret

snowflake_creds = get_secret("snowflake")
klaviyo_creds = get_secret("klaviyo")


def pretty(*ag):
    """Function for pretty printing."""
    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{d} - {ag[0]}")


def main():
    """Function to orchestrate klaviyo tap and target"""
    parser = argparse.ArgumentParser(description="klaviyo pipeline")
    parser.add_argument(
        "-s",
        "--start_date",
        help="start date",
        default=pendulum.now().subtract(days=7).to_date_string(),
    )
    parser.add_argument(
        "-e", "--end_date", help="end date", default=pendulum.now().to_date_string()
    )

    args = parser.parse_args()
    started = datetime.now()
    sf_account = snowflake_creds.get("account")
    sf_username = snowflake_creds.get("username")
    sf_password = snowflake_creds.get("password")
    sf_database = snowflake_creds.get("database")
    sf_warehouse = snowflake_creds.get("warehouse")
    sf_role = snowflake_creds.get("role")
    sf_schema = os.environ["KLAVIYO_TARGET_SCHEMA"]

    api_key = klaviyo_creds.get("klaviyo_auth_key")

    conf = {
        "auth_token": api_key,
        "flattening_enabled": False,
        "revision": "2025-01-25",
        "start_date": args.start_date,
    }

    tap = "tap-klaviyo"
    target = "target-snowflake"
    tap_config = "klaviyo_config.json"
    target_config = "snowflake_config.json"

    with open(tap_config, "w", encoding="utf-8") as out:
        json.dump(conf, out)

    snowflake_conf = {
        "user": sf_username,
        "password": sf_password,
        "account": sf_account,
        "database": sf_database,
        "role": sf_role,
        "schema": sf_schema,
        "warehouse": sf_warehouse,
    }

    with open(target_config, "w", encoding="utf-8") as out:
        json.dump(snowflake_conf, out)

    r = os.system(
        f" venv/.venv-klaviyo-tap/bin/{tap}  --config {tap_config}  --catalog klaviyo_catalog.json| venv/.venv-target-sf/bin/{target} --config {target_config}"
    )

    if r != 0:
        raise Exception("error occurred!")

    if os.path.exists(tap_config):
        os.remove(tap_config)

    if os.path.exists(target_config):
        os.remove(target_config)

    ended = datetime.now()
    pretty(f"execution time : {ended - started}")


if __name__ == "__main__":
    main()

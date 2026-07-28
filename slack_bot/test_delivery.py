"""
Standalone script and importable module for Profit Sentinel alert delivery.

As a script:  python slack_bot/test_delivery.py
As a module:  from test_delivery import post_latest_alert

Spec deviation: uses LIMIT 5 (not LIMIT 2) to ensure all unactioned alerts
from both confirmed test dates are delivered, satisfying the "3 distinct
alert_types" success criterion. LIMIT 2 ordered by fired_at DESC would return
two alerts from the same date and miss that criterion.
"""
import os
import subprocess
import sys

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from alert_formatter import format_alert_as_blocks

CLIENT_ID = "client_azure_co"
TEST_DATES = ["2025-10-15", "2025-01-11"]
AGENT_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "agents", "agent_a.py"
)


def _get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "SOURCE: test_delivery | ERROR: DATABASE_URL not set in .env"
        )
    return psycopg2.connect(url, sslmode="require")


def _run_agent(date_str: str) -> None:
    print(f"\n--- Running Agent A for {date_str} ---")
    result = subprocess.run(
        [sys.executable, AGENT_SCRIPT, "--client", CLIENT_ID, "--date", date_str],
        text=True,
    )
    if result.returncode != 0:
        print(f"  WARNING: Agent A exited with code {result.returncode} for {date_str}")


def post_latest_alert(channel_id: str, slack_client) -> None:
    # Ensure both confirmed test dates have run so alert_log is populated
    for d in TEST_DATES:
        _run_agent(d)

    # Fetch all unactioned alerts (LIMIT 5 to cover both test dates)
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM public.alert_log
                WHERE client_id = %s
                  AND action_taken IS NULL
                ORDER BY fired_at DESC
                LIMIT 5
                """,
                (CLIENT_ID,),
            )
            alerts = cur.fetchall()
    finally:
        conn.close()

    if not alerts:
        print(
            "No unactioned alerts found after Agent A run. "
            "Check agent output above for errors."
        )
        return

    for alert_row in alerts:
        row = dict(alert_row)
        blocks = format_alert_as_blocks(row)
        response = slack_client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"Profit Sentinel Alert: {row['alert_type']}",
        )
        print(f"Posted alert {row['alert_type']} — ts: {response['ts']}")

    print("\nDelivery complete. Check Slack.")


if __name__ == "__main__":
    from slack_sdk import WebClient

    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token.startswith("xoxb-"):
        print(
            "ERROR: SLACK_BOT_TOKEN not set or invalid in .env "
            "(must start with xoxb-). Complete Step 10A first."
        )
        sys.exit(1)

    channel_id = os.environ.get("SLACK_TEST_CHANNEL_ID", "")
    if not channel_id:
        print("ERROR: SLACK_TEST_CHANNEL_ID not set in .env")
        sys.exit(1)

    client = WebClient(token=token)
    post_latest_alert(channel_id, client)

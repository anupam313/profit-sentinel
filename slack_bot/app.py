"""
Profit Sentinel Slack Bot — Socket Mode entry point.
Run: python slack_bot/app.py
"""
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from action_handlers import (
    handle_approve,
    handle_dismiss,
    handle_dismiss_reason,
    handle_snooze,
)
from test_delivery import post_latest_alert

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

# ── Action handlers ───────────────────────────────────────────────────────────
app.action("alert_approve")(handle_approve)
app.action("alert_snooze")(handle_snooze)
app.action("alert_dismiss")(handle_dismiss)
app.action("dismiss_capacity")(handle_dismiss_reason)
app.action("dismiss_data_wrong")(handle_dismiss_reason)


# ── Slash command ─────────────────────────────────────────────────────────────
@app.command("/sentinel-test")
def handle_sentinel_test(ack, body, client):
    ack()
    channel = body["channel_id"]
    post_latest_alert(channel, client)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    token = os.environ.get("SLACK_APP_TOKEN", "")
    if not token.startswith("xapp-"):
        print(
            "ERROR: SLACK_APP_TOKEN not set or invalid in .env "
            "(must start with xapp-). Complete Step 10A first."
        )
        sys.exit(1)
    handler = SocketModeHandler(app, token)
    handler.start()

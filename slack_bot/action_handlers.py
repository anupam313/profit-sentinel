"""
Slack action handlers for Profit Sentinel alert buttons.
All DB writes use psycopg2 + DATABASE_URL from .env.
Agent A owns the `suppressed` column — handlers never touch it.
"""
import json
import logging
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


def _get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "SOURCE: Slack action_handlers | ERROR: DATABASE_URL not set"
        )
    return psycopg2.connect(url, sslmode="require")


def _parse_value(body: dict) -> dict:
    return json.loads(body["actions"][0]["value"])


def _channel_and_user(body: dict) -> tuple[str, str]:
    channel = (
        body.get("container", {}).get("channel_id")
        or body.get("channel", {}).get("id", "")
    )
    user = body.get("user", {}).get("id", "")
    return channel, user


# ── Approve ───────────────────────────────────────────────────────────────────

def handle_approve(body, ack, client):
    ack()
    try:
        payload = _parse_value(body)
        alert_id = payload["alert_id"]
        client_id = payload["client_id"]

        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE public.alert_log
                           SET action_taken    = 'approve',
                               action_taken_at = now()
                         WHERE id = %s AND client_id = %s
                        """,
                        (alert_id, client_id),
                    )
        finally:
            conn.close()

        channel, user = _channel_and_user(body)
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text="✅ Marked as approved. Outcome will be checked in 7 and 14 days.",
        )
    except Exception as e:
        logger.error(
            "SOURCE: Slack handle_approve | ERROR: %s | CONTEXT: body=%s",
            str(e),
            body.get("actions"),
        )


# ── Snooze ────────────────────────────────────────────────────────────────────

def handle_snooze(body, ack, client):
    ack()
    try:
        payload = _parse_value(body)
        alert_id = payload["alert_id"]
        client_id = payload["client_id"]

        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE public.alert_log
                           SET action_taken    = 'snooze',
                               action_taken_at = now()
                         WHERE id = %s AND client_id = %s
                        """,
                        (alert_id, client_id),
                    )
        finally:
            conn.close()

        channel, user = _channel_and_user(body)
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text="⏸ Snoozed for 48 hours.",
        )
    except Exception as e:
        logger.error(
            "SOURCE: Slack handle_snooze | ERROR: %s | CONTEXT: body=%s",
            str(e),
            body.get("actions"),
        )


# ── Dismiss (step 1 — ask reason) ────────────────────────────────────────────

def handle_dismiss(body, ack, say):
    ack()
    try:
        payload = _parse_value(body)
        alert_id = payload["alert_id"]
        client_id = payload["client_id"]

        thread_ts = body["message"]["ts"]

        say(
            thread_ts=thread_ts,
            text=(
                "Before I note this as dismissed — was it: "
                "(a) not actionable right now, or (b) the data doesn't look right?"
            ),
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Before I note this as dismissed — was it:",
                    },
                },
                {
                    "type": "actions",
                    "block_id": "dismiss_reason_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Not actionable right now",
                            },
                            "action_id": "dismiss_capacity",
                            "value": json.dumps(
                                {
                                    "alert_id": alert_id,
                                    "client_id": client_id,
                                    "reason": "capacity_constrained",
                                }
                            ),
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Data doesn't look right",
                            },
                            "action_id": "dismiss_data_wrong",
                            "value": json.dumps(
                                {
                                    "alert_id": alert_id,
                                    "client_id": client_id,
                                    "reason": "data_wrong",
                                }
                            ),
                        },
                    ],
                },
            ],
        )
    except Exception as e:
        logger.error(
            "SOURCE: Slack handle_dismiss | ERROR: %s | CONTEXT: body=%s",
            str(e),
            body.get("actions"),
        )


# ── Dismiss reason (step 2 — write reason) ────────────────────────────────────

def handle_dismiss_reason(body, ack, client):
    ack()
    try:
        payload = _parse_value(body)
        alert_id = payload["alert_id"]
        client_id = payload["client_id"]
        reason = payload["reason"]

        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE public.alert_log
                           SET action_taken    = 'dismiss',
                               action_taken_at = now(),
                               dismissal_reason = %s
                         WHERE id = %s AND client_id = %s
                        """,
                        (reason, alert_id, client_id),
                    )
        finally:
            conn.close()

        channel, user = _channel_and_user(body)
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text="Noted. Dismiss reason recorded.",
        )
    except Exception as e:
        logger.error(
            "SOURCE: Slack handle_dismiss_reason | ERROR: %s | CONTEXT: body=%s",
            str(e),
            body.get("actions"),
        )

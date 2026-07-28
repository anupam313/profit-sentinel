"""
Builds a Slack Block Kit blocks array from one alert_log row.
No LLM calls. Uses live schema column names.

Live schema deviations from spec:
  evidence_stack       -> evidence_stack_json
  signal_values (jsonb)-> signal_value (numeric) + threshold_value (numeric)
  projected_impact     -> absent; Block 6 always skipped
  alert_message        -> absent; Block 3 uses signal_value/threshold instead
"""
import json

ALERT_TITLES = {
    "A1": "Channel ROAS Gap Detected",
    "A2": "ROAS Drop — Meta CPM Root Cause",
    "B1": "Creative Fatigue Signal",
    "B4": "CPM Spike Alert",
    "C1": "Sizing Complaint Velocity Rising",
    "D1": "Contribution Margin Compression",
    "E2": "Repeat Purchase Rate Declining",
    "F2": "Checkout Error Spike",
}


def format_alert_as_blocks(row: dict) -> list:
    alert_type = row.get("alert_type", "")
    title = ALERT_TITLES.get(alert_type, alert_type)

    # ── Block 1 — Header ─────────────────────────────────────────────────────
    header_block = {
        "type": "header",
        "text": {"type": "plain_text", "text": title, "emoji": True},
    }

    # ── Block 2 — Context bar: signal date + sources ──────────────────────────
    signal_date = row.get("signal_date")
    fired_at = row.get("fired_at")
    if signal_date and hasattr(signal_date, "strftime"):
        date_str = signal_date.strftime("%b %d %Y")
    elif fired_at and hasattr(fired_at, "strftime"):
        date_str = fired_at.strftime("%b %d %Y")
    else:
        date_str = str(signal_date or fired_at or "Unknown date")[:10]

    sources = row.get("sources_used") or []
    sources_str = ", ".join(sources) if sources else "unknown"

    context_block = {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"*{date_str}*"},
            {"type": "mrkdwn", "text": f"Sources: {sources_str}"},
        ],
    }

    # ── Block 3 — Layer 0: confidence + signal context ────────────────────────
    confidence = row.get("confidence_score")
    confidence_pct = (
        f"{round(float(confidence) * 100)}%" if confidence is not None else "N/A"
    )
    signal_value = row.get("signal_value")
    threshold_value = row.get("threshold_value")
    if signal_value is not None and threshold_value is not None:
        signal_context = (
            f"Signal: `{float(signal_value):.4f}` "
            f"vs threshold: `{float(threshold_value):.4f}`"
        )
    else:
        signal_context = "Signal values not available."

    confidence_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Confidence:* {confidence_pct}\n{signal_context}",
        },
    }

    # ── Block 4 — Divider ─────────────────────────────────────────────────────
    divider = {"type": "divider"}

    # ── Block 5 — Evidence Stack ──────────────────────────────────────────────
    evidence_text = _build_evidence_text(row)
    evidence_block = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": evidence_text},
    }

    # ── Block 6 — Projected impact ────────────────────────────────────────────
    # projected_impact column does not exist in live schema — skipped per spec:
    # "If None, skip this block entirely."

    # ── Block 7 — Divider ─────────────────────────────────────────────────────
    divider2 = {"type": "divider"}

    # ── Block 8 — Actions ─────────────────────────────────────────────────────
    alert_id = row.get("id")
    client_id = row.get("client_id")

    actions_block = {
        "type": "actions",
        "block_id": "alert_actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✅ Approve", "emoji": True},
                "style": "primary",
                "action_id": "alert_approve",
                "value": json.dumps(
                    {"alert_id": alert_id, "client_id": client_id, "action": "approve"}
                ),
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "⏸ Snooze 48h", "emoji": True},
                "action_id": "alert_snooze",
                "value": json.dumps(
                    {"alert_id": alert_id, "client_id": client_id, "action": "snooze_48h"}
                ),
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "❌ Dismiss", "emoji": True},
                "style": "danger",
                "action_id": "alert_dismiss",
                "value": json.dumps(
                    {"alert_id": alert_id, "client_id": client_id, "action": "dismiss"}
                ),
            },
        ],
    }

    return [
        header_block,
        context_block,
        confidence_block,
        divider,
        evidence_block,
        divider2,
        actions_block,
    ]


def _build_evidence_text(row: dict) -> str:
    # Priority 1: evidence_stack_json (populated by Agent D in Step 13)
    evidence_json = row.get("evidence_stack_json")
    if evidence_json and isinstance(evidence_json, dict):
        layer_map = [
            ("layer_1", "Layer 1 — Observation"),
            ("layer_2", "Layer 2 — Context"),
            ("layer_3", "Layer 3 — Precedent"),
            ("layer_4", "Layer 4 — Recommendation"),
        ]
        parts = []
        for key, label in layer_map:
            if key in evidence_json:
                parts.append(f"*{label}*\n{evidence_json[key]}")
        if parts:
            return "\n\n".join(parts)

    # Priority 2: individual layer columns
    parts = []
    if row.get("layer1_headline"):
        parts.append(f"*Layer 1 — Observation*\n{row['layer1_headline']}")
    if row.get("layer2_context"):
        parts.append(f"*Layer 2 — Context*\n{row['layer2_context']}")
    if row.get("layer3_precedent"):
        parts.append(f"*Layer 3 — Precedent*\n{row['layer3_precedent']}")
    if parts:
        return "\n\n".join(parts)

    return "Evidence stack not available for this alert."

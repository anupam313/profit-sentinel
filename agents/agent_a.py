"""
Agent A — Signal Scanner
Reads mart_causal_chain_daily, runs pure-Python threshold checks,
writes confirmed signals to public.alert_log for Agent B.
No LLM calls anywhere in this file.
"""
import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any, TypedDict

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

MART_SCHEMA = "client_azure_co_marts"
MART_TABLE = "mart_causal_chain_daily"

# Meta attribution window break date and ±30-day caveat range
META_BREAK_DATE = date(2026, 1, 12)
META_CAVEAT_START = date(2025, 12, 13)
META_CAVEAT_END = date(2026, 2, 11)
META_CAVEAT_ALERT_TYPES = {"A2", "B4"}


# ── State ────────────────────────────────────────────────────────────────────

class AgentAState(TypedDict):
    client_id: str
    scan_date: date
    mart_rows: list[dict]
    client_config: dict
    calendar_events: list[dict]
    signals_detected: list[dict]
    signals_suppressed: list[dict]
    alerts_written: list[dict]
    scan_summary: dict


# ── DB connection ─────────────────────────────────────────────────────────────

def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "SOURCE: Agent A | ERROR: DATABASE_URL not set in environment"
        )
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


# ── Column availability cache ─────────────────────────────────────────────────

def _discover_mart_columns(conn) -> set[str]:
    """Return the set of column names that actually exist in mart_causal_chain_daily."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (MART_SCHEMA, MART_TABLE),
        )
        rows = cur.fetchall()
    cols = {r["column_name"] for r in rows}
    if not cols:
        logger.warning(
            "SOURCE: Agent A | WARNING: No columns found for %s.%s — "
            "mart may not exist yet",
            MART_SCHEMA,
            MART_TABLE,
        )
    return cols


# ── Node 1: load_context ──────────────────────────────────────────────────────

def load_context(state: AgentAState) -> AgentAState:
    client_id = state["client_id"]
    scan_date = state["scan_date"]

    try:
        conn = get_connection()
    except Exception as e:
        logger.error(
            "SOURCE: Agent A load_context | CLIENT: %s | ERROR: %s | CONTEXT: db_connect",
            client_id, str(e),
        )
        state["scan_summary"] = {
            "status": "error",
            "error": str(e),
            "scan_date": str(scan_date),
        }
        return state

    try:
        with conn:
            # ── client_config ─────────────────────────────────────────────
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM public.client_config WHERE client_id = %s",
                    (client_id,),
                )
                cfg_row = cur.fetchone()
            if not cfg_row:
                logger.error(
                    "SOURCE: Agent A load_context | CLIENT: %s | "
                    "ERROR: client_config row not found",
                    client_id,
                )
                state["scan_summary"] = {
                    "status": "error",
                    "error": "client_config not found",
                    "scan_date": str(scan_date),
                }
                return state
            client_config = dict(cfg_row)

            # ── brand_event_calendar (active events for scan_date) ────────
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM public.brand_event_calendar
                    WHERE client_id = %s
                      AND start_date <= %s
                      AND (end_date IS NULL OR end_date >= %s)
                    """,
                    (client_id, scan_date, scan_date),
                )
                calendar_events = [dict(r) for r in cur.fetchall()]

            # ── mart_causal_chain_daily for scan_date ─────────────────────
            # Discover available columns first
            mart_cols = _discover_mart_columns(conn)
            if not mart_cols:
                state["scan_summary"] = {
                    "status": "no_data",
                    "reason": "mart_table_missing",
                    "date": str(scan_date),
                }
                return state

            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT *
                    FROM {MART_SCHEMA}.{MART_TABLE}
                    WHERE date = %s
                    """,
                    (scan_date,),
                )
                mart_rows = [dict(r) for r in cur.fetchall()]

    except Exception as e:
        logger.error(
            "SOURCE: Agent A load_context | CLIENT: %s | ERROR: %s | "
            "CONTEXT: scan_date=%s",
            client_id, str(e), scan_date,
        )
        state["scan_summary"] = {
            "status": "error",
            "error": str(e),
            "scan_date": str(scan_date),
        }
        return state
    finally:
        conn.close()

    if not mart_rows:
        logger.warning(
            "SOURCE: Agent A load_context | CLIENT: %s | "
            "WARNING: No mart rows for %s",
            client_id, scan_date,
        )
        state["scan_summary"] = {"status": "no_data", "date": str(scan_date)}
        state["mart_rows"] = []
        state["client_config"] = client_config
        state["calendar_events"] = calendar_events
        return state

    state["mart_rows"] = mart_rows
    state["client_config"] = client_config
    state["calendar_events"] = calendar_events
    return state


# ── Node 2: run_threshold_checks ──────────────────────────────────────────────

def _get(row: dict, col: str, default=None):
    """Safe column getter — returns default if column absent or value is None."""
    return row.get(col, default)


def _col_missing(col: str, mart_cols: set[str], check_name: str) -> bool:
    if col not in mart_cols:
        logger.warning(
            "SOURCE: Agent A run_threshold_checks | "
            "WARNING: Column '%s' missing from mart — skipping %s check",
            col, check_name,
        )
        return True
    return False


def _cfg(config: dict, key: str, default=None):
    """Safe client_config getter with missing-key warning."""
    val = config.get(key, default)
    if val is None and default is None:
        logger.warning(
            "SOURCE: Agent A run_threshold_checks | "
            "WARNING: Threshold '%s' not in client_config — check will be skipped",
            key,
        )
    return val


def run_threshold_checks(state: AgentAState) -> AgentAState:
    client_id = state["client_id"]
    mart_rows = state["mart_rows"]
    cfg = state["client_config"]
    scan_date = state["scan_date"]
    signals_detected: list[dict] = []

    # Discover available columns from the first row keys as a proxy
    mart_cols: set[str] = set(mart_rows[0].keys()) if mart_rows else set()

    # E2 requires a 30-day baseline — load it separately
    e2_baseline = _load_e2_baseline(client_id, scan_date)

    for row in mart_rows:
        mart_date_raw = row.get("date")
        mart_date: date = (
            mart_date_raw if isinstance(mart_date_raw, date) else scan_date
        )

        # ── A2: ROAS Drop Root Cause (Meta CPM) ──────────────────────────
        roas_drop_thr = _cfg(cfg, "roas_drop_threshold_pct")
        cpm_spike_thr = _cfg(cfg, "cpm_spike_threshold_pct")
        if roas_drop_thr is not None and cpm_spike_thr is not None:
            need_a2 = ["roas_yoy_index", "meta_cpm_change_pct"]
            missing_a2 = [c for c in need_a2 if c not in mart_cols]
            if missing_a2:
                for mc in missing_a2:
                    logger.warning(
                        "SOURCE: Agent A | WARNING: Column '%s' missing — "
                        "skipping A2 check", mc
                    )
            else:
                roas_idx = _get(row, "roas_yoy_index")
                cpm_chg = _get(row, "meta_cpm_change_pct")
                if roas_idx is not None and cpm_chg is not None:
                    roas_chg_pct = float(roas_idx) * 100
                    if (
                        roas_chg_pct < -float(roas_drop_thr)
                        and float(cpm_chg) > float(cpm_spike_thr)
                    ):
                        signals_detected.append({
                            "alert_type": "A2",
                            "signal_value": round(roas_chg_pct, 4),
                            "threshold_value": float(roas_drop_thr),
                            "confidence_score": 0.70,
                            "verification_category": "A",
                            "sources_used": ["meta_ad_performance", "shopify_orders"],
                            "mart_date": mart_date,
                            "raw_mart_row": row,
                        })

        # ── B1: Creative Fatigue ──────────────────────────────────────────
        need_b1 = ["meta_ctr_7d_avg", "meta_ctr_prior_7d_avg", "meta_cpm_change_pct"]
        if not any(_col_missing(c, mart_cols, "B1") for c in need_b1):
            ctr_7d = _get(row, "meta_ctr_7d_avg")
            ctr_prior = _get(row, "meta_ctr_prior_7d_avg")
            cpm_chg = _get(row, "meta_cpm_change_pct")
            if ctr_7d is not None and ctr_prior is not None and cpm_chg is not None:
                if (
                    float(ctr_prior) > 0
                    and float(ctr_7d) < float(ctr_prior) * 0.85
                    and float(cpm_chg) > 0
                ):
                    signals_detected.append({
                        "alert_type": "B1",
                        "signal_value": round(float(ctr_7d), 6),
                        "threshold_value": round(float(ctr_prior) * 0.85, 6),
                        "confidence_score": 0.70,
                        "verification_category": "B",
                        "sources_used": ["meta_ad_performance"],
                        "mart_date": mart_date,
                        "raw_mart_row": row,
                    })

        # ── B4: CPM Spike ─────────────────────────────────────────────────
        cpm_spike_thr = _cfg(cfg, "cpm_spike_threshold_pct")
        if cpm_spike_thr is not None and not _col_missing(
            "meta_cpm_change_pct", mart_cols, "B4"
        ):
            cpm_chg = _get(row, "meta_cpm_change_pct")
            if cpm_chg is not None and float(cpm_chg) > float(cpm_spike_thr):
                signals_detected.append({
                    "alert_type": "B4",
                    "signal_value": round(float(cpm_chg), 4),
                    "threshold_value": float(cpm_spike_thr),
                    "confidence_score": 0.70,
                    "verification_category": "A",
                    "sources_used": ["meta_ad_performance"],
                    "mart_date": mart_date,
                    "raw_mart_row": row,
                })

        # ── C1: Sizing Complaint Velocity ─────────────────────────────────
        gorgias_thr = _cfg(cfg, "gorgias_sentiment_threshold")
        if gorgias_thr is not None and not _col_missing(
            "sizing_complaint_velocity_pct", mart_cols, "C1"
        ):
            vel = _get(row, "sizing_complaint_velocity_pct")
            if vel is not None and float(vel) > float(gorgias_thr):
                signals_detected.append({
                    "alert_type": "C1",
                    "signal_value": round(float(vel), 4),
                    "threshold_value": float(gorgias_thr),
                    "confidence_score": 0.70,
                    "verification_category": "A",
                    "sources_used": ["gorgias_tickets", "loop_returns"],
                    "mart_date": mart_date,
                    "raw_mart_row": row,
                })

        # ── D1: Contribution Margin Compression ───────────────────────────
        margin_floor = _cfg(cfg, "margin_floor_pct")
        cm_drop_thr = _cfg(cfg, "contribution_margin_drop_threshold")
        need_d1 = ["contribution_margin_pct", "contribution_margin_chg_pct"]
        d1_cols_present = all(c in mart_cols for c in need_d1)
        if not d1_cols_present:
            for c in need_d1:
                if c not in mart_cols:
                    logger.warning(
                        "SOURCE: Agent A | WARNING: Column '%s' missing from mart "
                        "— skipping D1 check", c
                    )
        elif margin_floor is not None and cm_drop_thr is not None:
            cm_pct = _get(row, "contribution_margin_pct")
            cm_chg = _get(row, "contribution_margin_chg_pct")
            if cm_pct is not None and cm_chg is not None:
                if (
                    float(cm_pct) < float(margin_floor)
                    and float(cm_chg) < -float(cm_drop_thr)
                ):
                    signals_detected.append({
                        "alert_type": "D1",
                        "signal_value": round(float(cm_pct), 4),
                        "threshold_value": float(margin_floor),
                        "confidence_score": 0.70,
                        "verification_category": "B",
                        "sources_used": ["shopify_orders", "meta_ad_performance"],
                        "mart_date": mart_date,
                        "raw_mart_row": row,
                    })

        # ── F2: Checkout Error Spike ──────────────────────────────────────
        sentry_thr = _cfg(cfg, "sentry_error_threshold_pct")
        if sentry_thr is not None:
            # Use sentry_error_rate_pct if it exists; otherwise compute proxy
            if "sentry_error_rate_pct" in mart_cols:
                err_rate = _get(row, "sentry_error_rate_pct")
            elif "sentry_error_count" in mart_cols and "total_sessions" in mart_cols:
                err_cnt = _get(row, "sentry_error_count", 0)
                sessions = _get(row, "total_sessions", 0)
                err_rate = (
                    float(err_cnt) / float(sessions) * 100
                    if sessions and float(sessions) > 0
                    else None
                )
            else:
                logger.warning(
                    "SOURCE: Agent A | WARNING: No sentry error rate columns in mart "
                    "— skipping F2 check"
                )
                err_rate = None

            if err_rate is not None and float(err_rate) > float(sentry_thr):
                signals_detected.append({
                    "alert_type": "F2",
                    "signal_value": round(float(err_rate), 4),
                    "threshold_value": float(sentry_thr),
                    "confidence_score": 0.70,
                    "verification_category": "A",
                    "sources_used": ["sentry_errors", "ga4_sessions"],
                    "mart_date": mart_date,
                    "raw_mart_row": row,
                })

        # ── A1: Channel ROAS Gap ──────────────────────────────────────────
        need_a1 = ["blended_roas", "tiktok_roas"]
        if not any(_col_missing(c, mart_cols, "A1") for c in need_a1):
            blended = _get(row, "blended_roas")
            tiktok = _get(row, "tiktok_roas")
            if blended is not None and tiktok is not None:
                if (
                    float(blended) > 0
                    and (float(blended) - float(tiktok)) > float(blended) * 0.40
                ):
                    signals_detected.append({
                        "alert_type": "A1",
                        "signal_value": round(float(tiktok), 4),
                        "threshold_value": round(float(blended) * 0.60, 4),
                        "confidence_score": 0.70,
                        "verification_category": "A",
                        "sources_used": [
                            "meta_ad_performance",
                            "shopify_orders",
                            "tiktok_ad_performance",
                        ],
                        "mart_date": mart_date,
                        "raw_mart_row": row,
                    })

        # ── E2: Repeat Purchase Rate Drop ─────────────────────────────────
        if not _col_missing("rolling_repeat_purchase_rate_90d", mart_cols, "E2"):
            rpr = _get(row, "rolling_repeat_purchase_rate_90d")
            if rpr is None:
                pass  # NULL = no data for this day
            elif e2_baseline is None:
                logger.info(
                    "SOURCE: Agent A | CLIENT: %s | INFO: E2 skipped — "
                    "insufficient_history (fewer than 30 days of baseline data)",
                    client_id,
                )
            else:
                if float(rpr) < float(e2_baseline) * 0.80:
                    signals_detected.append({
                        "alert_type": "E2",
                        "signal_value": round(float(rpr), 6),
                        "threshold_value": round(float(e2_baseline) * 0.80, 6),
                        "confidence_score": 0.70,
                        "verification_category": "B",
                        "sources_used": ["shopify_orders", "klaviyo"],
                        "mart_date": mart_date,
                        "raw_mart_row": row,
                    })

    # ── Meta attribution break annotation ────────────────────────────────
    for sig in signals_detected:
        if sig["alert_type"] in META_CAVEAT_ALERT_TYPES:
            sig_date = sig["mart_date"]
            if isinstance(sig_date, date) and META_CAVEAT_START <= sig_date <= META_CAVEAT_END:
                sig["attribution_break_caveat"] = True

    state["signals_detected"] = signals_detected
    return state


def _load_e2_baseline(client_id: str, scan_date: date) -> float | None:
    """
    Returns the 30-day avg of rolling_repeat_purchase_rate_90d ending the day
    before scan_date. Returns None if the column is absent or fewer than 30
    prior days of data exist.
    """
    try:
        conn = get_connection()
        try:
            # Check column exists before querying
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = %s
                      AND table_name = %s
                      AND column_name = 'rolling_repeat_purchase_rate_90d'
                    """,
                    (MART_SCHEMA, MART_TABLE),
                )
                if not cur.fetchone():
                    logger.warning(
                        "SOURCE: Agent A _load_e2_baseline | CLIENT: %s | "
                        "WARNING: rolling_repeat_purchase_rate_90d not in mart — E2 skipped",
                        client_id,
                    )
                    return None

            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        AVG(rolling_repeat_purchase_rate_90d) AS baseline_avg,
                        COUNT(*) FILTER (
                            WHERE rolling_repeat_purchase_rate_90d IS NOT NULL
                        ) AS day_count
                    FROM {MART_SCHEMA}.{MART_TABLE}
                    WHERE date >= %s AND date < %s
                      AND rolling_repeat_purchase_rate_90d IS NOT NULL
                    """,
                    (scan_date - timedelta(days=30), scan_date),
                )
                result = cur.fetchone()
            if result and result["day_count"] and int(result["day_count"]) >= 30:
                return float(result["baseline_avg"])
            return None
        finally:
            conn.close()
    except Exception as e:
        logger.error(
            "SOURCE: Agent A _load_e2_baseline | CLIENT: %s | ERROR: %s",
            client_id, str(e),
        )
        return None


# ── Node 3: apply_suppression ─────────────────────────────────────────────────

def apply_suppression(state: AgentAState) -> AgentAState:
    client_id = state["client_id"]
    signals_in = state["signals_detected"]
    calendar = state["calendar_events"]
    signals_out: list[dict] = []
    suppressed: list[dict] = []

    # Collect suppression_log writes; flush in one DB round-trip
    suppression_writes: list[dict] = []

    for sig in signals_in:
        alert_type = sig["alert_type"]
        raw_row = sig.get("raw_mart_row", {})

        # State 4: stale source data overrides everything
        any_stale = raw_row.get("any_source_stale", False)
        if any_stale:
            suppressed.append(sig)
            suppression_writes.append({
                "client_id": client_id,
                "alert_type": alert_type,
                "suppression_state": 4,
                "suppression_reason": "stale_source_data",
                "brand_event_calendar_id": None,
                "signal_value": sig["signal_value"],
                "threshold_value": sig["threshold_value"],
                "variance_explained_pct": None,
                "context_explanation": "Source data stale at scan time — DQ flag applied",
            })
            continue

        # Match against calendar events
        matched_state: int = 1
        matched_event: dict | None = None

        for event in calendar:
            suppress_list: list = event.get("suppress_alerts") or []
            context_list: list = event.get("context_alerts") or []
            if alert_type in suppress_list:
                matched_state = 3
                matched_event = event
                break  # State 3 is definitive
            if alert_type in context_list:
                matched_state = 2
                matched_event = event
                # Don't break — a later event might have State 3

        if matched_state == 1:
            sig_copy = dict(sig)
            sig_copy["suppression_state"] = 1
            signals_out.append(sig_copy)

        elif matched_state == 2:
            residual_thr = matched_event.get("residual_threshold_pct") if matched_event else None
            if residual_thr is not None:
                excess = abs(sig["signal_value"]) - abs(sig["threshold_value"])
                if excess > float(residual_thr):
                    sig_copy = dict(sig)
                    sig_copy["suppression_state"] = 2
                    sig_copy["context_explanation"] = (
                        matched_event.get("context_explanation", "") if matched_event else ""
                    )
                    signals_out.append(sig_copy)
                    suppression_writes.append({
                        "client_id": client_id,
                        "alert_type": alert_type,
                        "suppression_state": 2,
                        "suppression_reason": f"calendar_event:{matched_event.get('event_name','')}",
                        "brand_event_calendar_id": matched_event.get("id") if matched_event else None,
                        "signal_value": sig["signal_value"],
                        "threshold_value": sig["threshold_value"],
                        "variance_explained_pct": residual_thr,
                        "context_explanation": matched_event.get("context_explanation", "") if matched_event else "",
                    })
                else:
                    # Within residual threshold → upgrade to State 3
                    suppressed.append(sig)
                    suppression_writes.append({
                        "client_id": client_id,
                        "alert_type": alert_type,
                        "suppression_state": 3,
                        "suppression_reason": f"within_residual_threshold:{matched_event.get('event_name','')}",
                        "brand_event_calendar_id": matched_event.get("id") if matched_event else None,
                        "signal_value": sig["signal_value"],
                        "threshold_value": sig["threshold_value"],
                        "variance_explained_pct": residual_thr,
                        "context_explanation": matched_event.get("context_explanation", "") if matched_event else "",
                    })
            else:
                # No residual threshold defined — fire with context
                sig_copy = dict(sig)
                sig_copy["suppression_state"] = 2
                sig_copy["context_explanation"] = (
                    matched_event.get("context_explanation", "") if matched_event else ""
                )
                signals_out.append(sig_copy)

        elif matched_state == 3:
            suppressed.append(sig)
            suppression_writes.append({
                "client_id": client_id,
                "alert_type": alert_type,
                "suppression_state": 3,
                "suppression_reason": f"calendar_suppress:{matched_event.get('event_name','') if matched_event else ''}",
                "brand_event_calendar_id": matched_event.get("id") if matched_event else None,
                "signal_value": sig["signal_value"],
                "threshold_value": sig["threshold_value"],
                "variance_explained_pct": None,
                "context_explanation": matched_event.get("context_explanation", "") if matched_event else "",
            })

    # ── Flush suppression_log writes ──────────────────────────────────────
    if suppression_writes:
        _write_suppression_log(client_id, suppression_writes)

    state["signals_detected"] = signals_out
    state["signals_suppressed"] = suppressed
    return state


def _write_suppression_log(client_id: str, rows: list[dict]) -> None:
    """
    Writes to the live suppression_log schema.
    Uses suppression_explanation (live column name) not context_explanation.
    brand_event_calendar_id not present in live schema — stored in suppression_source.
    """
    try:
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    for row in rows:
                        cur.execute(
                            """
                            INSERT INTO public.suppression_log (
                                client_id,
                                alert_type,
                                suppression_state,
                                suppression_reason,
                                signal_value,
                                threshold_value,
                                variance_explained_pct,
                                suppression_explanation,
                                suppression_source,
                                founder_queryable
                            ) VALUES (
                                %(client_id)s,
                                %(alert_type)s,
                                %(suppression_state)s,
                                %(suppression_reason)s,
                                %(signal_value)s,
                                %(threshold_value)s,
                                %(variance_explained_pct)s,
                                %(suppression_explanation)s,
                                %(suppression_source)s,
                                true
                            )
                            """,
                            {
                                "client_id": row["client_id"],
                                "alert_type": row["alert_type"],
                                "suppression_state": row["suppression_state"],
                                "suppression_reason": row["suppression_reason"],
                                "signal_value": row.get("signal_value"),
                                "threshold_value": row.get("threshold_value"),
                                "variance_explained_pct": row.get("variance_explained_pct"),
                                "suppression_explanation": row.get("context_explanation", ""),
                                "suppression_source": (
                                    f"brand_event_calendar:{row.get('brand_event_calendar_id')}"
                                    if row.get("brand_event_calendar_id")
                                    else row.get("suppression_reason", "agent_a")
                                ),
                            },
                        )
        finally:
            conn.close()
    except Exception as e:
        logger.error(
            "SOURCE: Agent A _write_suppression_log | CLIENT: %s | ERROR: %s | "
            "CONTEXT: %s rows not written",
            client_id, str(e), len(rows),
        )


# ── Node 4: write_alerts ──────────────────────────────────────────────────────

def write_alerts(state: AgentAState) -> AgentAState:
    client_id = state["client_id"]
    signals = state["signals_detected"]
    alerts_written: list[dict] = []
    duplicates_skipped = 0
    failures = 0

    try:
        conn = get_connection()
    except Exception as e:
        logger.error(
            "SOURCE: Agent A write_alerts | CLIENT: %s | ERROR: %s | "
            "CONTEXT: cannot open db connection",
            client_id, str(e),
        )
        state["scan_summary"] = state.get("scan_summary", {})
        state["scan_summary"]["write_alerts_error"] = str(e)
        return state

    try:
        for sig in signals:
            signal_date = sig["mart_date"]
            alert_type = sig["alert_type"]

            try:
                with conn:
                    with conn.cursor() as cur:
                        # Deduplication check
                        cur.execute(
                            """
                            SELECT id FROM public.alert_log
                            WHERE client_id = %s
                              AND alert_type = %s
                              AND signal_date = %s
                            LIMIT 1
                            """,
                            (client_id, alert_type, signal_date),
                        )
                        existing = cur.fetchone()

                    if existing:
                        logger.info(
                            "SOURCE: Agent A write_alerts | CLIENT: %s | "
                            "INFO: Duplicate skipped — %s on %s",
                            client_id, alert_type, signal_date,
                        )
                        duplicates_skipped += 1
                        continue

                    suppression_type = None
                    sup_state = sig.get("suppression_state", 1)
                    if sup_state == 2:
                        suppression_type = "state_2"

                    sources_used = sig.get("sources_used", [])

                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO public.alert_log (
                                client_id,
                                alert_type,
                                signal_date,
                                signal_value,
                                threshold_value,
                                confidence_score,
                                verification_category,
                                sources_used,
                                suppression_type,
                                escalation_level,
                                alert_instance_number,
                                fired_at,
                                is_synthetic
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s,
                                %s::text[], %s, %s, %s, now(), false
                            )
                            RETURNING id, fired_at
                            """,
                            (
                                client_id,
                                alert_type,
                                signal_date,
                                sig["signal_value"],
                                sig["threshold_value"],
                                sig["confidence_score"],
                                sig["verification_category"],
                                sources_used,
                                suppression_type,
                                1,
                                1,
                            ),
                        )
                        inserted = cur.fetchone()

                    alerts_written.append({
                        "id": inserted["id"],
                        "alert_type": alert_type,
                        "signal_date": str(signal_date),
                        "fired_at": str(inserted["fired_at"]),
                        "signal_value": sig["signal_value"],
                        "confidence_score": sig["confidence_score"],
                        "suppression_type": suppression_type,
                        "attribution_break_caveat": sig.get("attribution_break_caveat", False),
                    })

            except Exception as e:
                failures += 1
                logger.error(
                    "SOURCE: Agent A write_alerts | CLIENT: %s | ERROR: %s | "
                    "CONTEXT: alert_type=%s signal_date=%s",
                    client_id, str(e), alert_type, signal_date,
                )

    finally:
        conn.close()

    state["alerts_written"] = alerts_written
    state["scan_summary"] = state.get("scan_summary", {})
    state["scan_summary"]["alerts_skipped_duplicate"] = duplicates_skipped
    state["scan_summary"]["alerts_write_failures"] = failures
    return state


# ── Node 5: build_summary ─────────────────────────────────────────────────────

def build_summary(state: AgentAState) -> AgentAState:
    mart_rows = state.get("mart_rows", [])
    signals_detected = state.get("signals_detected", [])
    signals_suppressed = state.get("signals_suppressed", [])
    alerts_written = state.get("alerts_written", [])
    calendar_events = state.get("calendar_events", [])
    scan_date = state["scan_date"]
    partial = state.get("scan_summary", {})

    any_stale = any(
        r.get("any_source_stale", False) for r in mart_rows
    )

    # 8 signals attempted (A1, A2, B1, B4, C1, D1, E2, F2)
    signals_checked = 8

    summary: dict[str, Any] = {
        "status": "complete",
        "scan_date": str(scan_date),
        "client_id": state["client_id"],
        "mart_rows_loaded": len(mart_rows),
        "signals_checked": signals_checked,
        "signals_detected": len(signals_detected),
        "signals_suppressed": len(signals_suppressed),
        "alerts_written": len(alerts_written),
        "alerts_skipped_duplicate": partial.get("alerts_skipped_duplicate", 0),
        "alerts_write_failures": partial.get("alerts_write_failures", 0),
        "calendar_events_active": len(calendar_events),
        "any_source_stale": any_stale,
    }

    if alerts_written:
        summary["alert_types_written"] = [a["alert_type"] for a in alerts_written]
        summary["attribution_break_caveats"] = [
            a["alert_type"]
            for a in alerts_written
            if a.get("attribution_break_caveat")
        ]

    state["scan_summary"] = summary
    print(json.dumps(summary, indent=2, default=str))
    return state


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_load(state: AgentAState) -> str:
    status = state.get("scan_summary", {}).get("status", "")
    if status in ("no_data", "error"):
        return END
    if not state.get("mart_rows"):
        return END
    return "run_threshold_checks"


# ── Graph ─────────────────────────────────────────────────────────────────────

graph = StateGraph(AgentAState)
graph.add_node("load_context", load_context)
graph.add_node("run_threshold_checks", run_threshold_checks)
graph.add_node("apply_suppression", apply_suppression)
graph.add_node("write_alerts", write_alerts)
graph.add_node("build_summary", build_summary)

graph.set_entry_point("load_context")
graph.add_conditional_edges(
    "load_context",
    _route_after_load,
    {
        "run_threshold_checks": "run_threshold_checks",
        END: END,
    },
)
graph.add_edge("run_threshold_checks", "apply_suppression")
graph.add_edge("apply_suppression", "write_alerts")
graph.add_edge("write_alerts", "build_summary")
graph.add_edge("build_summary", END)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent A — Profit Sentinel Signal Scanner")
    parser.add_argument("--date", type=str, help="Scan date YYYY-MM-DD (default: today)")
    parser.add_argument("--client", type=str, default="client_azure_co")
    args = parser.parse_args()

    scan_date = date.fromisoformat(args.date) if args.date else date.today()

    app = graph.compile()
    app.invoke({
        "client_id": args.client,
        "scan_date": scan_date,
        "mart_rows": [],
        "client_config": {},
        "calendar_events": [],
        "signals_detected": [],
        "signals_suppressed": [],
        "alerts_written": [],
        "scan_summary": {},
    })
    # build_summary already prints scan_summary as JSON

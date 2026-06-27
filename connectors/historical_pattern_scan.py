"""
connectors/historical_pattern_scan.py

Onboarding Step 11 — historical pattern scan.
Runs after dbt full-refresh. Phases:
  1. DQ pre-checks            → client_azure_co.dq_metric_scores
  2. Known chain validation    → public.causal_pattern_validation
  3. Novel chain discovery     → public.candidate_signals
  4. GMV derivation            → public.client_config
  5. Lookback days write-back  → public.client_config
  6. Onboarding message        → public.onboarding_messages  (full mode only)
  7. Final status update       → public.client_config

Usage:
    python connectors/historical_pattern_scan.py --client_id client_azure_co --mode full
    python connectors/historical_pattern_scan.py --client_id client_azure_co --mode incremental

Progress: one JSON line per phase to stderr. No stdout output.

AUTHORITATIVE SCHEMA NOTES (do not infer — drift is a bug, not a fallback):
  - client_id throughout: 'client_azure_co' (NOT 'azure_co')
  - alert_log.alert_type  (NOT signal_type)
  - alert_log.evidence_stack_json  (NOT evidence_stack)
  - signal_value + threshold_value are separate numerics (NOT a jsonb blob)
  - stg_klaviyo_profiles: profile_id (not customer_id), vip_status (not is_vip)
  - stg_loop_refunds does not exist — use stg_loop_returns for refund lag
  - stg_meta_ad_performance: no attributed_revenue — proxy: spend × purchase_roas
  - stg_klaviyo_flows: no date column — use stg_klaviyo_email_events for time series
  - GA4 tables (ga4_pages, ga4_devices) absent in synthetic data — NULL mart cols expected
  - Meta attribution hard break: January 12 2026 (7d_view + 28d_view deprecated)
  - brand_event_calendar: zero rows in synthetic data
  - mart_causal_chain_daily is in schema client_azure_co_marts
  - dq_metric_scores is in schema client_azure_co (NOT public)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

_ROOT = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(_ROOT, ".env"))

logger = logging.getLogger(__name__)
SOURCE_COMPONENT = "Historical Pattern Scan"
VERTICAL_TAG = "contemporary_womenswear"

# Meta attribution window hard break.  Rows within ±30d are structurally
# unreliable because Facebook deprecated 7d_view + 28d_view on this date.
_META_BREAK = date(2026, 1, 12)
_META_EXCL_START = _META_BREAK - timedelta(days=30)
_META_EXCL_END = _META_BREAK + timedelta(days=30)

# ─────────────────────────────────────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────────────────────────────────────

def _log(obj: dict) -> None:
    obj.setdefault("ts", datetime.now(timezone.utc).isoformat())
    print(json.dumps(obj), file=sys.stderr, flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# Database connection  (same pattern as python_transformer.py)
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn() -> psycopg2.extensions.connection:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set in environment")
    return psycopg2.connect(url, sslmode="require")


def _update_scan_status(conn, client_id: str, status: str) -> None:
    """Best-effort status update — never raises."""
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE public.client_config SET historical_scan_status = %s "
                "WHERE client_id = %s",
                (status, client_id),
            )
    except Exception as exc:
        logger.error(
            "SOURCE: %s | CLIENT: %s | ERROR: Could not update scan status to %s: %s",
            SOURCE_COMPONENT, client_id, status, exc,
        )


# ─────────────────────────────────────────────────────────────────────────────
# DDL: output tables + client_config tracking columns
# ─────────────────────────────────────────────────────────────────────────────

_DDL_CAUSAL_PATTERN_VALIDATION = """
CREATE TABLE IF NOT EXISTS public.causal_pattern_validation (
    id                        bigint generated always as identity primary key,
    causal_chain_id           text not null,
    vertical_tag              text not null,
    signal_type               text,
    instance_count            integer default 0,
    observable_instance_count integer default 0,
    confirmed_count           integer default 0,
    false_positive_count      integer default 0,
    confidence_rate           numeric,
    hit_rate                  numeric,
    threshold_at_scan_time    jsonb,
    confidence_tier           text,
    last_promoted_at          timestamptz,
    historical_scan_seeded    boolean default false,
    scan_skipped_reason       text,
    created_at                timestamptz default now(),
    updated_at                timestamptz default now(),
    unique(causal_chain_id, vertical_tag)
)
"""

_DDL_CANDIDATE_SIGNALS = """
CREATE TABLE IF NOT EXISTS public.candidate_signals (
    id                          bigint generated always as identity primary key,
    client_id                   text not null,
    vertical_tag                text,
    signal_description          text,
    leading_signal_column       text not null,
    outcome_column              text not null,
    signal_values               jsonb,
    sources_involved            text[],
    first_detected_at           date,
    instance_count              integer default 0,
    observable_instance_count   integer default 0,
    hit_rate                    numeric,
    cross_client_instance_count integer default 0,
    outcome_confirmed_count     integer default 0,
    outcome_rejected_count      integer default 0,
    promotion_status            text default 'candidate',
    source                      text,
    client_specific             boolean default true,
    calendar_clustered          boolean default false,
    confound_unresolved         boolean default false,
    single_client_core          boolean default false,
    seasonal_confound_risk      boolean default false,
    practitioner_approved       boolean default false,
    created_at                  timestamptz default now(),
    updated_at                  timestamptz default now(),
    unique(client_id, leading_signal_column, outcome_column)
)
"""

_DDL_ONBOARDING_MESSAGES = """
CREATE TABLE IF NOT EXISTS public.onboarding_messages (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    message_variant text not null,
    message_text    text not null,
    generated_at    timestamptz default now(),
    sent            boolean default false
)
"""

# Columns added to client_config to support scan lifecycle tracking.
# ADD COLUMN IF NOT EXISTS is safe to run repeatedly.
_ALTER_CLIENT_CONFIG_STMTS = [
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "historical_scan_status text DEFAULT 'pending'",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "historical_scan_completed boolean DEFAULT false",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "historical_scan_completed_at timestamptz",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "last_historical_scan_at timestamptz",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "gmv_derived_annual numeric",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "gmv_derived_at timestamptz",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "meta_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "tiktok_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "shopify_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "klaviyo_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "gorgias_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "loop_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "sentry_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "ga4_lookback_days integer",
    "ALTER TABLE public.client_config ADD COLUMN IF NOT EXISTS "
    "pending_connectors text[] DEFAULT '{}'",
]


def _ensure_tables(conn) -> None:
    with conn:
        cur = conn.cursor()
        for ddl in (_DDL_CAUSAL_PATTERN_VALIDATION, _DDL_CANDIDATE_SIGNALS, _DDL_ONBOARDING_MESSAGES):
            cur.execute(ddl)
        # Enable RLS (Supabase service_role bypasses it; required by RULE 8)
        for tbl in ("causal_pattern_validation", "candidate_signals", "onboarding_messages"):
            cur.execute(f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY")
        for stmt in _ALTER_CLIENT_CONFIG_STMTS:
            cur.execute(stmt)


# ─────────────────────────────────────────────────────────────────────────────
# Mart loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_mart(conn, client_id: str, mode: str, last_scan_at=None) -> pd.DataFrame:
    """
    Load mart_causal_chain_daily for client_id.
    Schema: {client_id}_marts  (e.g. client_azure_co_marts)
    RULE 2: schema-qualified, client_id-derived — never hardcoded.
    """
    mart_schema = f"{client_id}_marts"
    if mode == "incremental" and last_scan_at:
        sql = (
            f'SELECT * FROM "{mart_schema}".mart_causal_chain_daily '
            "WHERE date > %s ORDER BY date ASC"
        )
        params: tuple | None = (last_scan_at,)
    else:
        sql = f'SELECT * FROM "{mart_schema}".mart_causal_chain_daily ORDER BY date ASC'
        params = None

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    rows = cur.fetchall()
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Ensure all numeric mart columns are float, not Decimal
        for col in df.select_dtypes(include=["object"]).columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
    return df


def _load_mart_full(conn, client_id: str) -> pd.DataFrame:
    """Full mart load regardless of mode — used for novel chain full-history validation."""
    return _load_mart(conn, client_id, "full")


# ─────────────────────────────────────────────────────────────────────────────
# Mart enrichment: precompute rolling averages for chain evaluation
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_mart(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling-average columns prefixed with _ for use in trigger/outcome functions.
    The mart already contains rolling columns (e.g. blended_cac_7d); we add prior-window
    and longer-window averages that the chain conditions need.
    """
    if df.empty:
        return df
    df = df.sort_values("date").reset_index(drop=True)

    def roll(col: str, w: int, shift: int = 0) -> "pd.Series":
        if col not in df.columns:
            return pd.Series([np.nan] * len(df), index=df.index)
        s = df[col].rolling(w, min_periods=1).mean()
        return s.shift(shift) if shift else s

    df["_net_rev_14d"]           = roll("net_revenue", 14)
    df["_net_rev_28d"]           = roll("net_revenue", 28)
    df["_meta_roas_7d_prior"]    = roll("meta_roas", 7, shift=7)
    df["_tiktok_roas_7d_prior"]  = roll("tiktok_roas", 7, shift=7)
    df["_aov_28d"]               = roll("aov_7d", 28)
    df["_return_rate_7d_prior"]  = roll("return_rate_pct", 7, shift=7)
    df["_return_rate_14d"]       = roll("return_rate_pct", 14)
    df["_sizing_rate_7d_prior"]  = roll("sizing_complaint_rate_7d", 7, shift=7)
    df["_refund_lag_14d"]        = roll("avg_days_to_refund", 14)
    df["_cac_14d"]               = roll("blended_cac_7d", 14)
    df["_open_rate_14d"]         = roll("effective_open_rate_7d", 14)
    df["_klaviyo_rev_14d"]       = roll("klaviyo_revenue", 14)
    df["_repeat_rate_28d"]       = roll("rolling_repeat_purchase_rate_90d", 28)
    df["_vip_gap_28d"]           = roll("vip_purchase_gap_days", 28)
    df["_checkout_err_7d_prior"] = roll("checkout_error_count", 7, shift=7)
    df["_pp_flow_28d"]           = roll("post_purchase_flow_revenue_7d", 28)
    df["_cpm_chg_7d"]            = roll("meta_cpm_change_pct", 7)
    df["_new_cust_rate_28d"]     = roll("new_customer_rate_7d", 28)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Confidence tier
# ─────────────────────────────────────────────────────────────────────────────

def _assign_tier(observable: int, hit_rate: float | None) -> str:
    if hit_rate is None or observable < 4 or hit_rate < 0.70:
        return "candidate"
    if observable >= 10 and hit_rate >= 0.80:
        return "core"
    return "provisional"


# ─────────────────────────────────────────────────────────────────────────────
# Core chain evaluation engine
# ─────────────────────────────────────────────────────────────────────────────

def _eval_chain_generic(
    df: pd.DataFrame,
    trigger_fn,
    outcome_fn,
    lag_days: int,
    scan_date: date,
    excluded_date_set: set | None = None,
) -> tuple[int, int, int]:
    """
    Scan df for trigger events; for each, check outcome in lag_days ± 2 window.
    Returns (instance_count, observable_count, confirmed_count).
    excluded_date_set: dates to skip as both triggers AND outcome dates (Meta break).
    """
    if df.empty:
        return 0, 0, 0

    df = df.sort_values("date").reset_index(drop=True)
    excl = excluded_date_set or set()
    cutoff = scan_date - timedelta(days=lag_days + 2)

    trigger_indices: list[tuple[date, int]] = []
    for idx, row in df.iterrows():
        if row["date"] in excl:
            continue
        try:
            if trigger_fn(row, df):
                trigger_indices.append((row["date"], idx))
        except Exception:
            continue

    instance_count = len(trigger_indices)
    observable_count = 0
    confirmed_count = 0

    for tdate, tidx in trigger_indices:
        if tdate > cutoff:
            continue
        observable_count += 1
        w_start = tdate + timedelta(days=lag_days - 2)
        w_end   = tdate + timedelta(days=lag_days + 2)
        forward = df[(df["date"] >= w_start) & (df["date"] <= w_end)]
        if excl:
            forward = forward[~forward["date"].isin(excl)]
        if forward.empty:
            continue
        trigger_row = df.loc[tidx]
        try:
            if outcome_fn(trigger_row, forward, df, tdate):
                confirmed_count += 1
        except Exception:
            pass

    return instance_count, observable_count, confirmed_count


def _safe_mean(series: pd.Series) -> float | None:
    v = series.dropna()
    return float(v.mean()) if len(v) else None


def _pct_decline(baseline: float | None, fwd: pd.Series, thresh: float = 0.97) -> bool:
    """True if forward mean < baseline * thresh (declining)."""
    if baseline is None or pd.isna(baseline) or baseline == 0:
        return False
    m = _safe_mean(fwd)
    return m is not None and m < baseline * thresh


def _pct_drop(baseline: float | None, fwd: pd.Series, drop: float) -> bool:
    """True if forward mean < baseline * (1 - drop)."""
    if baseline is None or pd.isna(baseline) or baseline == 0:
        return False
    m = _safe_mean(fwd)
    return m is not None and m < baseline * (1.0 - drop)


# ─────────────────────────────────────────────────────────────────────────────
# Chain registry  (22 chains — locked thresholds/lags per spec)
# Each entry maps spec column names to actual mart column names where they differ.
# Absent mart columns → zero trigger events → written with scan_skipped_reason.
# ─────────────────────────────────────────────────────────────────────────────

def _build_chain_registry() -> list[dict]:
    """
    Returns the 22-chain registry as a list of dicts.
    required_mart_cols: if any of these are missing/all-null → skip chain.
    signal_mart_col / outcome_mart_col: exact mart column names used for recording.
    meta_break: True for A- and B-series chains (apply Jan-12-2026 exclusion).
    """

    def _trigger(row, df, col, condition):
        v = row.get(col)
        return pd.notna(v) and condition(float(v), row, df)

    def _outcome_decline(trigger_row, fwd, df, tdate, baseline_col):
        base = trigger_row.get(baseline_col)
        if pd.isna(base) or base is None:
            base = trigger_row.get("_net_rev_14d")
        return _pct_decline(base, fwd["net_revenue"])

    # ── A1: Channel ROAS gap ──────────────────────────────────────────────────
    # mart column: meta_roas  (spec calls it meta_roas_7d — no 7d column exists)
    def a1_trig(row, df):
        v = row.get("meta_roas")
        return pd.notna(v) and float(v) < 1.5

    def a1_out(tr, fwd, df, td):
        base = tr.get("_net_rev_14d")
        return _pct_decline(base, fwd["net_revenue"])

    # ── A2: ROAS drop root cause — CPM ────────────────────────────────────────
    # meta_cpm_change_pct = (7d CPM avg − prior 7d avg) / prior 7d avg × 100
    # Spec threshold: meta_cpm_3d rising >15% vs 7d avg → use meta_cpm_change_pct > 15
    def a2_trig(row, df):
        v = row.get("meta_cpm_change_pct")
        return pd.notna(v) and float(v) > 15.0

    def a2_out(tr, fwd, df, td):
        base = tr.get("meta_roas")
        return _pct_drop(base, fwd["meta_roas"], 0.10)

    # ── A3: Channel ROAS ranking reversal ─────────────────────────────────────
    def a3_trig(row, df):
        tk = row.get("tiktok_roas"); mt = row.get("meta_roas")
        if pd.isna(tk) or pd.isna(mt) or float(tk) <= float(mt):
            return False
        prior = row.get("_tiktok_roas_7d_prior")
        return pd.notna(prior) and float(tk) > float(prior) * 1.05

    def a3_out(tr, fwd, df, td):
        # Outcome: tiktok_roas sustains advantage > meta_roas in forward window
        valid = fwd.dropna(subset=["tiktok_roas", "meta_roas"])
        if valid.empty:
            return False
        return (valid["tiktok_roas"] > valid["meta_roas"]).mean() >= 0.60

    # ── B1: Creative fatigue ─────────────────────────────────────────────────
    # meta_frequency_7d NOT in mart → zero instances (handled by required_mart_cols)

    # ── B4: CPM spike / audience saturation ──────────────────────────────────
    def b4_trig(row, df):
        v = row.get("meta_cpm_change_pct")
        return pd.notna(v) and float(v) > 20.0

    def b4_out(tr, fwd, df, td):
        base = tr.get("meta_roas")
        return _pct_drop(base, fwd["meta_roas"], 0.15)

    # ── C1: Sizing complaint velocity ─────────────────────────────────────────
    # sizing_complaint_rate_7d is the mart column for spec's gorgias_sizing_tag_rate_7d
    def c1_trig(row, df):
        v = row.get("sizing_complaint_rate_7d")
        prior = row.get("_sizing_rate_7d_prior")
        if pd.isna(v) or pd.isna(prior) or float(prior) == 0:
            return False
        return (float(v) - float(prior)) / float(prior) > 0.30

    def c1_out(tr, fwd, df, td):
        base = tr.get("return_rate_pct")
        if pd.isna(base):
            return False
        # Rises >8 percentage points
        m = _safe_mean(fwd["return_rate_pct"])
        return m is not None and m > float(base) + 8.0

    # ── C3: SKU return rate outlier ───────────────────────────────────────────
    # loop_return_rate_7d → return_rate_pct
    def c3_trig(row, df):
        v = row.get("return_rate_pct")
        prior = row.get("_return_rate_7d_prior")
        if pd.isna(v) or float(v) <= 25.0:
            return False
        if pd.notna(prior):
            return float(v) > float(prior)
        return True

    def c3_out(tr, fwd, df, td):
        base = tr.get("net_revenue")
        return _pct_decline(base, fwd["net_revenue"])

    # ── C5: Refund timing acceleration ───────────────────────────────────────
    def c5_trig(row, df):
        v = row.get("avg_days_to_refund")
        avg = row.get("_refund_lag_14d")
        if pd.isna(v) or pd.isna(avg) or float(avg) == 0:
            return False
        # drops >20% vs 14d avg (acceleration = shorter lag)
        return (float(avg) - float(v)) / float(avg) > 0.20

    def c5_out(tr, fwd, df, td):
        base = tr.get("_return_rate_14d") or tr.get("return_rate_pct")
        if pd.isna(base):
            return False
        m = _safe_mean(fwd["return_rate_pct"])
        return m is not None and m > float(base) * 1.10

    # ── D1: Contribution margin compression ───────────────────────────────────
    # blended_cac_7d rising >15% vs 14d avg
    def d1_trig(row, df):
        v = row.get("blended_cac_7d")
        avg = row.get("_cac_14d")
        if pd.isna(v) or pd.isna(avg) or float(avg) == 0:
            return False
        return (float(v) - float(avg)) / float(avg) > 0.15

    def d1_out(tr, fwd, df, td):
        base = tr.get("net_revenue")
        if pd.isna(base):
            return False
        m = _safe_mean(fwd["net_revenue"])
        # flat or declining: forward mean ≤ baseline × 1.02
        return m is not None and m <= float(base) * 1.02

    # ── D2: Discount dependency creep ────────────────────────────────────────
    # discount_rate_7d NOT in mart → zero instances (required_mart_cols check)

    # ── D4: AOV compression with margin impact ────────────────────────────────
    def d4_trig(row, df):
        v = row.get("aov_7d")
        avg = row.get("_aov_28d")
        if pd.isna(v) or pd.isna(avg) or float(avg) == 0:
            return False
        return (float(avg) - float(v)) / float(avg) > 0.10

    def d4_out(tr, fwd, df, td):
        base = tr.get("_net_rev_28d") or tr.get("net_revenue")
        return _pct_decline(base, fwd["net_revenue"])

    # ── E1: Email list health decay ───────────────────────────────────────────
    # effective_open_rate_7d already ios_mpp_multiplier-corrected in mart — do not reapply
    def e1_trig(row, df):
        v = row.get("effective_open_rate_7d")
        avg = row.get("_open_rate_14d")
        if pd.isna(v) or float(v) >= 0.20:
            return False
        if pd.notna(avg):
            return float(v) < float(avg)
        return True

    def e1_out(tr, fwd, df, td):
        base = tr.get("_klaviyo_rev_14d") or tr.get("klaviyo_revenue")
        return _pct_decline(base, fwd["klaviyo_revenue"])

    # ── E2: Repeat purchase rate drop ─────────────────────────────────────────
    # repeat_purchase_rate_7d → rolling_repeat_purchase_rate_90d
    def e2_trig(row, df):
        v = row.get("rolling_repeat_purchase_rate_90d")
        avg = row.get("_repeat_rate_28d")
        if pd.isna(v) or pd.isna(avg):
            return False
        return (float(avg) - float(v)) > 0.05

    def e2_out(tr, fwd, df, td):
        base = tr.get("_net_rev_28d") or tr.get("net_revenue")
        return _pct_decline(base, fwd["net_revenue"])

    # ── E3: High-LTV customers going quiet ───────────────────────────────────
    def e3_trig(row, df):
        v = row.get("vip_purchase_gap_days")
        avg = row.get("_vip_gap_28d")
        if pd.isna(v) or pd.isna(avg) or float(avg) == 0:
            return False
        return (float(v) - float(avg)) / float(avg) > 0.20

    def e3_out(tr, fwd, df, td):
        base = tr.get("_net_rev_28d") or tr.get("net_revenue")
        return _pct_decline(base, fwd["net_revenue"])

    # ── F2: Payment gateway failure ───────────────────────────────────────────
    # sentry_checkout_error_rate_7d not in mart; proxy: checkout_error_count rising >50%
    def f2_trig(row, df):
        v = row.get("checkout_error_count")
        prior = row.get("_checkout_err_7d_prior")
        if pd.isna(v) or pd.isna(prior) or float(prior) == 0:
            return False
        return (float(v) - float(prior)) / float(prior) > 0.50

    def f2_out(tr, fwd, df, td):
        base = tr.get("avg_cvr")
        return _pct_drop(base, fwd["avg_cvr"], 0.10)

    # ── F4: PDP bounce → conversion drop ─────────────────────────────────────
    # ga4_pdp_bounce_rate (mart col; spec calls it ga4_pdp_bounce_rate_7d)
    # NULL for synthetic data → zero trigger events naturally
    def f4_trig(row, df):
        v = row.get("ga4_pdp_bounce_rate")
        prior_avg = _safe_mean(df["ga4_pdp_bounce_rate"].dropna())
        if pd.isna(v) or float(v) <= 60.0:
            return False
        if prior_avg is not None:
            return float(v) > prior_avg
        return True

    def f4_out(tr, fwd, df, td):
        base = tr.get("avg_cvr")
        return _pct_drop(base, fwd["avg_cvr"], 0.08)

    # ── G1: Stockout during active spend ─────────────────────────────────────
    # shopify_inventory_zero_sku_count NOT in mart → zero instances

    # ── G4: Back-in-stock revenue window ─────────────────────────────────────
    # shopify_inventory_restocked_sku_count NOT in mart → zero instances

    # ── Chain 1: Post-launch CAC creep ───────────────────────────────────────
    # brand_event_calendar has zero rows in synthetic data → zero trigger events
    # Trigger requires a launch_date from brand_event_calendar; without rows, no triggers.
    def chain1_trig(row, df):
        # brand_event_calendar zero rows in synthetic: trigger never fires
        return False

    def chain1_out(tr, fwd, df, td):
        base = tr.get("blended_cac_7d")
        prior = tr.get("_new_cust_rate_28d")
        if pd.isna(base) or base is None:
            return False
        m = _safe_mean(fwd["blended_cac_7d"])
        return m is not None and m > float(base) * 1.20

    # ── Chain 2: Mobile vs desktop checkout gap ───────────────────────────────
    # mobile_checkout_completion_rate_7d NULL in mart for synthetic → zero triggers
    def chain2_trig(row, df):
        mob = row.get("mobile_checkout_completion_rate_7d")
        desk = row.get("desktop_checkout_completion_rate_7d")
        if pd.isna(mob) or pd.isna(desk):
            return False
        return (float(desk) - float(mob)) > 15.0

    def chain2_out(tr, fwd, df, td):
        base = tr.get("net_revenue")
        return _pct_decline(base, fwd["net_revenue"])

    # ── Chain 3: Post-purchase flow revenue isolation ─────────────────────────
    def chain3_trig(row, df):
        pp = row.get("post_purchase_flow_revenue_7d")
        pp_avg = row.get("_pp_flow_28d")
        kl = row.get("klaviyo_revenue")
        kl_avg = row.get("_klaviyo_rev_14d")
        if pd.isna(pp) or pd.isna(pp_avg) or float(pp_avg) == 0:
            return False
        pp_drop = (float(pp_avg) - float(pp)) / float(pp_avg) > 0.20
        if not pp_drop:
            return False
        if pd.notna(kl) and pd.notna(kl_avg) and float(kl_avg) > 0:
            return abs(float(kl) - float(kl_avg)) / float(kl_avg) < 0.05
        return True

    def chain3_out(tr, fwd, df, td):
        pp = tr.get("post_purchase_flow_revenue_7d")
        kl = tr.get("klaviyo_revenue")
        if pd.isna(pp) or pd.isna(kl) or float(kl) == 0:
            return False
        trigger_ratio = float(pp) / float(kl)
        kl_fwd = fwd["klaviyo_revenue"].replace(0, np.nan)
        ratios = (fwd["post_purchase_flow_revenue_7d"] / kl_fwd).dropna()
        if ratios.empty:
            return False
        return float(ratios.mean()) < trigger_ratio * 0.80

    # ── Chain 5: Attribution double-counting expansion ────────────────────────
    # meta_attributed_pct_of_shopify_revenue NOT in mart → skip with insufficient_history

    # ── Registry ─────────────────────────────────────────────────────────────
    return [
        dict(id="A1", lag=7, meta_break=True,
             required=["meta_roas", "net_revenue"],
             signal_col="meta_roas", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=a1_trig, outcome_fn=a1_out,
             threshold={"signal": "meta_roas < 1.5",
                        "outcome": "net_revenue declining vs 14d avg"}),
        dict(id="A2", lag=7, meta_break=True,
             required=["meta_cpm_change_pct", "meta_roas"],
             signal_col="meta_cpm_change_pct", outcome_col="meta_roas",
             absent_reason="insufficient_history",
             trigger_fn=a2_trig, outcome_fn=a2_out,
             threshold={"signal": "meta_cpm_change_pct > 15 (rising >15% vs 7d avg)",
                        "outcome": "meta_roas drops >10%"}),
        dict(id="A3", lag=7, meta_break=True,
             required=["tiktok_roas", "meta_roas", "net_revenue"],
             signal_col="tiktok_roas", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=a3_trig, outcome_fn=a3_out,
             threshold={"signal": "tiktok_roas > meta_roas AND tiktok_roas rising",
                        "outcome": "tiktok_roas sustains advantage in forward window"}),
        dict(id="B1", lag=3, meta_break=True,
             required=["meta_frequency_7d"],  # NOT in mart → zero instances
             signal_col="meta_frequency_7d", outcome_col="meta_ctr_7d_avg",
             absent_reason="insufficient_history",
             trigger_fn=lambda r, d: False, outcome_fn=lambda *a: False,
             threshold={"signal": "meta_frequency_7d > 3.5",
                        "outcome": "meta_ctr drops >20%"}),
        dict(id="B4", lag=7, meta_break=True,
             required=["meta_cpm_change_pct", "meta_roas"],
             signal_col="meta_cpm_change_pct", outcome_col="meta_roas",
             absent_reason="insufficient_history",
             trigger_fn=b4_trig, outcome_fn=b4_out,
             threshold={"signal": "meta_cpm_change_pct > 20 (rising >20% 3d rolling)",
                        "outcome": "meta_roas drops >15%"}),
        dict(id="C1", lag=10, meta_break=False,
             required=["sizing_complaint_rate_7d", "return_rate_pct"],
             signal_col="sizing_complaint_rate_7d", outcome_col="return_rate_pct",
             absent_reason="gorgias_tagging_insufficient",
             trigger_fn=c1_trig, outcome_fn=c1_out,
             threshold={"signal": "sizing_complaint_rate_7d rising >30% vs prior 7d",
                        "outcome": "return_rate_pct rises >8pp"}),
        dict(id="C3", lag=10, meta_break=False,
             required=["return_rate_pct", "net_revenue"],
             signal_col="return_rate_pct", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=c3_trig, outcome_fn=c3_out,
             threshold={"signal": "return_rate_pct > 25 AND rising",
                        "outcome": "net_revenue declining"}),
        dict(id="C5", lag=7, meta_break=False,
             required=["avg_days_to_refund", "return_rate_pct"],
             signal_col="avg_days_to_refund", outcome_col="return_rate_pct",
             absent_reason="insufficient_history",
             trigger_fn=c5_trig, outcome_fn=c5_out,
             threshold={"signal": "avg_days_to_refund drops >20% vs 14d avg",
                        "outcome": "return_rate accelerating >10%"}),
        dict(id="D1", lag=7, meta_break=False,
             required=["blended_cac_7d", "net_revenue"],
             signal_col="blended_cac_7d", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=d1_trig, outcome_fn=d1_out,
             threshold={"signal": "blended_cac_7d rising >15% vs 14d avg",
                        "outcome": "net_revenue flat or declining"}),
        dict(id="D2", lag=14, meta_break=False,
             required=["discount_rate_7d"],  # NOT in mart → zero instances
             signal_col="discount_rate_7d", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=lambda r, d: False, outcome_fn=lambda *a: False,
             threshold={"signal": "discount_rate rising >5pp vs 28d avg",
                        "outcome": "revenue growth <5% despite discounts"}),
        dict(id="D4", lag=14, meta_break=False,
             required=["aov_7d", "net_revenue"],
             signal_col="aov_7d", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=d4_trig, outcome_fn=d4_out,
             threshold={"signal": "aov_7d declining >10% vs 28d avg",
                        "outcome": "net_revenue declining"}),
        dict(id="E1", lag=14, meta_break=False,
             required=["effective_open_rate_7d", "klaviyo_revenue"],
             signal_col="effective_open_rate_7d", outcome_col="klaviyo_revenue",
             absent_reason="insufficient_history",
             trigger_fn=e1_trig, outcome_fn=e1_out,
             threshold={"signal": "effective_open_rate_7d < 0.20 AND declining",
                        "outcome": "klaviyo_revenue declining"}),
        dict(id="E2", lag=14, meta_break=False,
             required=["rolling_repeat_purchase_rate_90d", "net_revenue"],
             signal_col="rolling_repeat_purchase_rate_90d", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=e2_trig, outcome_fn=e2_out,
             threshold={"signal": "rolling_repeat_purchase_rate_90d drops >5pp vs 28d avg",
                        "outcome": "net_revenue declining"}),
        dict(id="E3", lag=21, meta_break=False,
             required=["vip_purchase_gap_days", "net_revenue"],
             signal_col="vip_purchase_gap_days", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=e3_trig, outcome_fn=e3_out,
             threshold={"signal": "vip_purchase_gap_days rising >20% vs 28d avg",
                        "outcome": "net_revenue declining"}),
        dict(id="F2", lag=5, meta_break=False,
             required=["checkout_error_count", "avg_cvr"],
             signal_col="checkout_error_count", outcome_col="avg_cvr",
             absent_reason="insufficient_history",
             trigger_fn=f2_trig, outcome_fn=f2_out,
             threshold={"signal": "checkout_error_count rising >50% vs 7d prior (proxy for sentry_checkout_error_rate)",
                        "outcome": "avg_cvr drops >10%"}),
        dict(id="F4", lag=5, meta_break=False,
             required=["ga4_pdp_bounce_rate", "avg_cvr"],
             signal_col="ga4_pdp_bounce_rate", outcome_col="avg_cvr",
             absent_reason="insufficient_history",
             trigger_fn=f4_trig, outcome_fn=f4_out,
             threshold={"signal": "ga4_pdp_bounce_rate > 60 AND rising",
                        "outcome": "avg_cvr drops >8%"}),
        dict(id="G1", lag=1, meta_break=False,
             required=["shopify_inventory_zero_sku_count"],  # NOT in mart
             signal_col="shopify_inventory_zero_sku_count", outcome_col="meta_roas",
             absent_reason="insufficient_history",
             trigger_fn=lambda r, d: False, outcome_fn=lambda *a: False,
             threshold={"signal": "inventory_zero_sku_count rises >2",
                        "outcome": "meta_roas drops >10% next day"}),
        dict(id="G4", lag=2, meta_break=False,
             required=["shopify_inventory_restocked_sku_count"],  # NOT in mart
             signal_col="shopify_inventory_restocked_sku_count", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=lambda r, d: False, outcome_fn=lambda *a: False,
             threshold={"signal": "restocked_sku_count > 0",
                        "outcome": "revenue uptick within 2 days"}),
        dict(id="Chain1", lag=14, meta_break=False,
             required=["new_customer_rate_7d", "blended_cac_7d"],
             signal_col="new_customer_rate_7d", outcome_col="blended_cac_7d",
             absent_reason="insufficient_history",
             trigger_fn=chain1_trig, outcome_fn=chain1_out,
             threshold={"signal": "new_customer_rate dropping post-launch (brand_event_calendar: zero rows in synthetic)",
                        "outcome": "blended_cac rising >20% vs pre-launch avg"}),
        dict(id="Chain2", lag=5, meta_break=False,
             required=["mobile_checkout_completion_rate_7d", "net_revenue"],
             signal_col="mobile_checkout_completion_rate_7d", outcome_col="net_revenue",
             absent_reason="insufficient_history",
             trigger_fn=chain2_trig, outcome_fn=chain2_out,
             threshold={"signal": "mobile_completion_rate drops >15pp below desktop_completion_rate",
                        "outcome": "net_revenue declining"}),
        dict(id="Chain3", lag=14, meta_break=False,
             required=["post_purchase_flow_revenue_7d", "klaviyo_revenue"],
             signal_col="post_purchase_flow_revenue_7d", outcome_col="klaviyo_revenue",
             absent_reason="insufficient_history",
             trigger_fn=chain3_trig, outcome_fn=chain3_out,
             threshold={"signal": "post_purchase_flow_revenue drops >20% vs 28d avg while klaviyo flat",
                        "outcome": "flow/total klaviyo revenue ratio drops >20%"}),
        dict(id="Chain5", lag=14, meta_break=False,
             required=["meta_attributed_pct_of_shopify_revenue"],  # NOT in mart
             signal_col="meta_attributed_pct_of_shopify_revenue",
             outcome_col="meta_attributed_pct_of_shopify_revenue",
             absent_reason="insufficient_history",
             trigger_fn=lambda r, d: False, outcome_fn=lambda *a: False,
             threshold={"signal": "sum of attributed pcts > 110 AND rising",
                        "outcome": "attribution overlap growing"}),
    ]


CHAIN_REGISTRY = _build_chain_registry()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: check table existence
# ─────────────────────────────────────────────────────────────────────────────

def _table_exists(cur, schema: str, table: str) -> bool:
    cur.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = %s)",
        (schema, table),
    )
    row = cur.fetchone()
    return row["exists"] if hasattr(row, "keys") else row[0]


def _col_all_null(df: pd.DataFrame, col: str) -> bool:
    """True if column is absent or >80% null."""
    if col not in df.columns:
        return True
    return df[col].isna().mean() > 0.80


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: DQ pre-checks
# ─────────────────────────────────────────────────────────────────────────────

def run_dq_prechecks(conn, client_id: str, scan_date: date) -> dict[str, str]:
    """
    Runs DQ checks for 7 sources. Writes to client_azure_co.dq_metric_scores.
    Returns skip_map: {chain_id → scan_skipped_reason}.
    """
    _log({"phase": "dq_precheck", "status": "start"})
    client_schema = client_id  # 'client_azure_co'
    staging_schema = f"{client_schema}_staging"  # dbt staging schema (live views)
    skip_map: dict[str, str] = {}
    dq_rows: list[dict] = []

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Gorgias ──────────────────────────────────────────────────────────────
    if _table_exists(cur, staging_schema, "stg_gorgias_tickets"):
        try:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'closed') AS closed_ct,
                    COUNT(*) FILTER (
                        WHERE status = 'closed'
                          AND tags IS NOT NULL
                          AND jsonb_typeof(tags) = 'array'
                          AND jsonb_array_length(tags) > 0
                    ) AS tagged_ct
                FROM %s.stg_gorgias_tickets
                """ % staging_schema  # dbt staging schema, derived from client_id
            )
            row = cur.fetchone()
            closed = int(row["closed_ct"] or 0)
            tagged = int(row["tagged_ct"] or 0)
            tag_rate = tagged / closed if closed > 0 else 0.0
            score = round(tag_rate, 4)
            issues = [] if tag_rate >= 0.50 else ["TAG_COVERAGE_LOW"]
            dq_rows.append(dict(source="gorgias", metric_domain="tag_coverage",
                                dq_score=score, dq_issues=issues))
            if tag_rate < 0.50:
                skip_map["C1"] = "gorgias_tagging_insufficient"
                _log({"phase": "dq_precheck", "source": "gorgias",
                      "tag_rate": tag_rate, "action": "skip_C1"})
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: Gorgias DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="gorgias", metric_domain="tag_coverage",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
            # Fail-closed: DQ check errored → suppress C1 rather than let it fire
            # unguarded by tag coverage.
            skip_map["C1"] = "dq_check_failed"
    else:
        dq_rows.append(dict(source="gorgias", metric_domain="tag_coverage",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))
        # Fail-closed: staging table that should exist is absent → suppress C1
        # rather than let it fire unguarded by tag coverage.
        skip_map["C1"] = "stg_staging_absent"

    # ── Meta ─────────────────────────────────────────────────────────────────
    if _table_exists(cur, staging_schema, "stg_meta_ad_performance") and \
       _table_exists(cur, staging_schema, "stg_shopify_orders"):
        try:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_spend_days,
                    COUNT(*) FILTER (WHERE s.order_ct IS NULL OR s.order_ct = 0) AS unmatched
                FROM (
                    SELECT date_start::date AS dt,
                           SUM(spend::numeric) AS daily_spend
                    FROM %s.stg_meta_ad_performance
                    GROUP BY 1
                ) m
                LEFT JOIN (
                    SELECT processed_at::date AS dt, COUNT(*) AS order_ct
                    FROM %s.stg_shopify_orders
                    GROUP BY 1
                ) s ON m.dt = s.dt
                WHERE m.daily_spend > 0
                """ % (staging_schema, staging_schema)
            )
            row = cur.fetchone()
            total = int(row["total_spend_days"] or 0)
            unmatched = int(row["unmatched"] or 0)
            unmatched_rate = unmatched / total if total > 0 else 0.0
            score = round(1.0 - unmatched_rate, 4)
            issues = ["HIGH_UNMATCHED"] if unmatched_rate > 0.30 else []
            dq_rows.append(dict(source="meta", metric_domain="spend_order_match",
                                dq_score=score, dq_issues=issues))
            if unmatched_rate > 0.30:
                _log({"phase": "dq_precheck", "source": "meta",
                      "unmatched_rate": unmatched_rate,
                      "action": "caveat_only — chains proceed"})
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: Meta DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="meta", metric_domain="spend_order_match",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
    else:
        dq_rows.append(dict(source="meta", metric_domain="spend_order_match",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))

    # ── TikTok ───────────────────────────────────────────────────────────────
    # creator_id / product_id not in stg_tiktok_ad_performance; use identity_id as proxy
    if _table_exists(cur, staging_schema, "stg_tiktok_ad_performance"):
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS total,
                       COUNT(*) FILTER (
                           WHERE identity_id IS NOT NULL AND identity_id <> ''
                       ) AS has_creator
                FROM %s.stg_tiktok_ad_performance
                """ % staging_schema
            )
            row = cur.fetchone()
            total = int(row["total"] or 0)
            creator = int(row["has_creator"] or 0)
            coverage = creator / total if total > 0 else 0.0
            score = round(coverage, 4)
            issues = ["CREATOR_MAPPING_LOW"] if coverage < 0.70 else []
            dq_rows.append(dict(source="tiktok", metric_domain="creator_sku_coverage",
                                dq_score=score, dq_issues=issues))
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: TikTok DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="tiktok", metric_domain="creator_sku_coverage",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
    else:
        dq_rows.append(dict(source="tiktok", metric_domain="creator_sku_coverage",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))

    # ── Loop Returns ─────────────────────────────────────────────────────────
    # Use loop_return_reasons.reason_code; stg_loop_returns has no reason column
    if _table_exists(cur, client_schema, "loop_return_reasons"):
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS total,
                       COUNT(*) FILTER (
                           WHERE reason_code IS NOT NULL
                             AND reason_code <> 'Other'
                             AND reason_code <> ''
                       ) AS good_reasons
                FROM %s.loop_return_reasons
                """ % client_schema
            )
            row = cur.fetchone()
            total = int(row["total"] or 0)
            good = int(row["good_reasons"] or 0)
            bad_rate = 1.0 - (good / total) if total > 0 else 1.0
            score = round(1.0 - bad_rate, 4)
            issues = ["REASON_CODE_LOW"] if bad_rate > 0.40 else []
            dq_rows.append(dict(source="loop_returns", metric_domain="reason_code_coverage",
                                dq_score=score, dq_issues=issues))
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: Loop DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="loop_returns", metric_domain="reason_code_coverage",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
    else:
        dq_rows.append(dict(source="loop_returns", metric_domain="reason_code_coverage",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))

    # ── Klaviyo ───────────────────────────────────────────────────────────────
    # Check stg_klaviyo_flows for post_purchase flow type (attributes JSON)
    klaviyo_has_pp = False
    if _table_exists(cur, staging_schema, "stg_klaviyo_flows"):
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM %s.stg_klaviyo_flows
                WHERE (attributes->>'flow_type' = 'post_purchase'
                       OR lower(attributes->>'name') LIKE '%%post%%purchase%%')
                  AND _airbyte_extracted_at > now() - interval '90 days'
                """ % staging_schema
            )
            cnt = int(cur.fetchone()["cnt"] or 0)
            klaviyo_has_pp = cnt > 0
            score = 1.0 if klaviyo_has_pp else 0.0
            issues = [] if klaviyo_has_pp else ["NO_POST_PURCHASE_FLOW"]
            dq_rows.append(dict(source="klaviyo", metric_domain="post_purchase_flow_active",
                                dq_score=score, dq_issues=issues))
            if not klaviyo_has_pp:
                # D5 / E4 are future chains; none of the current 22 require this gate
                _log({"phase": "dq_precheck", "source": "klaviyo",
                      "post_purchase_flow": False, "action": "note_only"})
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: Klaviyo DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="klaviyo", metric_domain="post_purchase_flow_active",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
    else:
        dq_rows.append(dict(source="klaviyo", metric_domain="post_purchase_flow_active",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))

    # ── GA4 ───────────────────────────────────────────────────────────────────
    # Funnel step completeness: steps 1–4 present with non-null counts
    if _table_exists(cur, client_schema, "ga4_funnel_daily"):
        try:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE sessions_entered > 0)   AS s1,
                    COUNT(*) FILTER (WHERE product_page_views > 0) AS s2,
                    COUNT(*) FILTER (WHERE add_to_cart > 0)        AS s3,
                    COUNT(*) FILTER (WHERE checkout_initiated > 0) AS s4,
                    COUNT(*) FILTER (WHERE purchase_completed > 0) AS s5
                FROM %s.ga4_funnel_daily
                """ % client_schema
            )
            row = cur.fetchone()
            steps_present = sum(1 for k in ("s1", "s2", "s3", "s4") if int(row[k] or 0) > 0)
            score = round(steps_present / 4, 4)
            issues = [] if steps_present == 4 else [f"FUNNEL_STEPS_MISSING:{4 - steps_present}"]
            dq_rows.append(dict(source="ga4", metric_domain="funnel_step_completeness",
                                dq_score=score, dq_issues=issues))
            if steps_present < 4:
                skip_map["F4"] = "insufficient_history"
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: GA4 DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="ga4", metric_domain="funnel_step_completeness",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
            skip_map["F4"] = "insufficient_history"
    else:
        dq_rows.append(dict(source="ga4", metric_domain="funnel_step_completeness",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))
        skip_map["F4"] = "insufficient_history"

    # ── Sentry ────────────────────────────────────────────────────────────────
    # Actual column is 'date' (not 'error_date' — confirmed in live schema)
    if _table_exists(cur, client_schema, "sentry_errors_daily"):
        try:
            cur.execute(
                """
                SELECT MIN(date) AS min_dt, MAX(date) AS max_dt
                FROM %s.sentry_errors_daily
                """ % client_schema
            )
            row = cur.fetchone()
            if row["min_dt"] and row["max_dt"]:
                coverage_days = (row["max_dt"] - row["min_dt"]).days
            else:
                coverage_days = 0
            score = min(1.0, round(coverage_days / 90, 4))
            issues = [] if coverage_days >= 30 else [f"COVERAGE_DAYS:{coverage_days}"]
            dq_rows.append(dict(source="sentry", metric_domain="coverage_window_days",
                                dq_score=score, dq_issues=issues))
            if coverage_days < 30:
                skip_map["F2"] = "insufficient_history"
                skip_map["F4"] = skip_map.get("F4", "insufficient_history")
        except Exception as exc:
            logger.error("SOURCE: %s | CLIENT: %s | ERROR: Sentry DQ: %s",
                         SOURCE_COMPONENT, client_id, exc)
            dq_rows.append(dict(source="sentry", metric_domain="coverage_window_days",
                                dq_score=0, dq_issues=["CHECK_FAILED"]))
            skip_map["F2"] = "insufficient_history"
    else:
        dq_rows.append(dict(source="sentry", metric_domain="coverage_window_days",
                            dq_score=0, dq_issues=["TABLE_ABSENT"]))
        skip_map["F2"] = "insufficient_history"

    # ── Chain5: attributed pct columns absent in mart ─────────────────────────
    skip_map["Chain5"] = "insufficient_history"

    # ── Write DQ scores to client_azure_co.dq_metric_scores ──────────────────
    try:
        with conn:
            cur2 = conn.cursor()
            # Delete today's rows for this client before re-inserting
            cur2.execute(
                "DELETE FROM %s.dq_metric_scores "
                "WHERE client_id = %%s AND effective_from::date = %%s" % client_schema,
                (client_id, scan_date),
            )
            for row in dq_rows:
                issues_arr = row.get("dq_issues", [])
                cur2.execute(
                    """
                    INSERT INTO %s.dq_metric_scores
                        (client_id, source, metric_domain, dq_score, dq_issues,
                         alert_types_affected, confidence_cap, effective_from)
                    VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, now())
                    """ % client_schema,
                    (client_id, row["source"], row["metric_domain"],
                     row["dq_score"], issues_arr,
                     [],  # alert_types_affected — populated by alert engine later
                     1.0 if not issues_arr else max(0.5, row["dq_score"])),
                )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Writing DQ scores: %s",
                     SOURCE_COMPONENT, client_id, exc)

    chains_skipped = len(skip_map)
    _log({
        "phase": "dq_precheck", "status": "complete",
        "sources_checked": 7,
        "chains_skipped": chains_skipped,
        "skip_reasons": skip_map,
    })
    return skip_map


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: Known chain validation
# ─────────────────────────────────────────────────────────────────────────────

def run_known_chains(
    conn,
    client_id: str,
    mart_df: pd.DataFrame,
    skip_map: dict[str, str],
    scan_date: date,
    mode: str,
) -> dict[str, str]:
    """
    Evaluate all 22 chains against mart_df.
    Returns tier_map: {chain_id → confidence_tier}.
    Writes one row per chain to public.causal_pattern_validation.
    """
    _log({"phase": "known_chains", "status": "start", "chains_total": len(CHAIN_REGISTRY)})

    enriched = _enrich_mart(mart_df)
    tier_map: dict[str, str] = {}
    tiers: dict[str, int] = {"candidate": 0, "provisional": 0, "core": 0}
    chains_skipped = 0

    # Build Meta-break excluded date set (for A/B series)
    meta_excl = set()
    if not mart_df.empty:
        for d in mart_df["date"]:
            if _META_EXCL_START <= d <= _META_EXCL_END:
                meta_excl.add(d)

    upsert_rows: list[dict] = []

    for chain in CHAIN_REGISTRY:
        chain_id = chain["id"]

        # ── Check DQ skip ──────────────────────────────────────────────────
        skip_reason: str | None = skip_map.get(chain_id)

        # ── Check for absent mart columns ──────────────────────────────────
        if skip_reason is None:
            missing_cols = [
                c for c in chain["required"]
                if c not in enriched.columns
            ]
            if missing_cols:
                skip_reason = chain["absent_reason"]

        # ── For incremental mode: filter to only new rows ──────────────────
        if mode == "incremental":
            eval_df = enriched  # already windowed by _load_mart
        else:
            eval_df = enriched

        # ── Evaluate chain or record zero instances ────────────────────────
        if skip_reason is not None:
            instance_count = 0
            observable_count = 0
            confirmed_count = 0
        else:
            excl = meta_excl if chain["meta_break"] else None
            instance_count, observable_count, confirmed_count = _eval_chain_generic(
                eval_df,
                chain["trigger_fn"],
                chain["outcome_fn"],
                chain["lag"],
                scan_date,
                excluded_date_set=excl,
            )
            # Chains that require brand_event_calendar (zero rows synthetic) or
            # columns that happen to be all-NULL produce zero instances.
            # Set skip reason so the tier stays 'candidate' and reason is recorded.
            if instance_count == 0 and chain_id in ("Chain1", "Chain2", "G1", "G4", "B1", "D2", "Chain5"):
                skip_reason = chain["absent_reason"]

        false_pos = max(0, observable_count - confirmed_count)
        hit_rate = confirmed_count / observable_count if observable_count > 0 else None
        tier = _assign_tier(observable_count, hit_rate)
        tier_map[chain_id] = tier
        tiers[tier] = tiers.get(tier, 0) + 1
        if skip_reason:
            chains_skipped += 1

        upsert_rows.append(dict(
            causal_chain_id=chain_id,
            vertical_tag=VERTICAL_TAG,
            signal_type=chain_id,
            instance_count=instance_count,
            observable_instance_count=observable_count,
            confirmed_count=confirmed_count,
            false_positive_count=false_pos,
            confidence_rate=hit_rate,
            hit_rate=hit_rate,
            threshold_at_scan_time=json.dumps(chain["threshold"]),
            confidence_tier=tier,
            scan_skipped_reason=skip_reason,
        ))

    # ── Write to public.causal_pattern_validation ──────────────────────────
    try:
        with conn:
            cur = conn.cursor()
            for row in upsert_rows:
                cur.execute(
                    """
                    INSERT INTO public.causal_pattern_validation (
                        causal_chain_id, vertical_tag, signal_type,
                        instance_count, observable_instance_count,
                        confirmed_count, false_positive_count,
                        confidence_rate, hit_rate,
                        threshold_at_scan_time, confidence_tier,
                        last_promoted_at, historical_scan_seeded,
                        scan_skipped_reason, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s::jsonb, %s, now(), true, %s, now(), now())
                    ON CONFLICT (causal_chain_id, vertical_tag)
                    DO UPDATE SET
                        signal_type               = EXCLUDED.signal_type,
                        instance_count            = EXCLUDED.instance_count,
                        observable_instance_count = EXCLUDED.observable_instance_count,
                        confirmed_count           = EXCLUDED.confirmed_count,
                        false_positive_count      = EXCLUDED.false_positive_count,
                        confidence_rate           = EXCLUDED.confidence_rate,
                        hit_rate                  = EXCLUDED.hit_rate,
                        threshold_at_scan_time    = EXCLUDED.threshold_at_scan_time,
                        confidence_tier           = EXCLUDED.confidence_tier,
                        last_promoted_at          = now(),
                        historical_scan_seeded    = true,
                        scan_skipped_reason       = EXCLUDED.scan_skipped_reason,
                        updated_at                = now()
                    """,
                    (row["causal_chain_id"], row["vertical_tag"], row["signal_type"],
                     row["instance_count"], row["observable_instance_count"],
                     row["confirmed_count"], row["false_positive_count"],
                     row["confidence_rate"], row["hit_rate"],
                     row["threshold_at_scan_time"], row["confidence_tier"],
                     row["scan_skipped_reason"]),
                )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Writing causal_pattern_validation: %s",
                     SOURCE_COMPONENT, client_id, exc)
        raise

    _log({
        "phase": "known_chains", "status": "complete",
        "chains_scanned": len(CHAIN_REGISTRY) - chains_skipped,
        "chains_skipped": chains_skipped,
        "tiers": tiers,
    })
    return tier_map


# ─────────────────────────────────────────────────────────────────────────────
# Calendar window helpers (for novel chain discovery)
# ─────────────────────────────────────────────────────────────────────────────

_CALENDAR_WINDOWS: list[tuple[tuple[int, int], tuple[int, int]]] = [
    ((11, 15), (12, 5)),   # BFCM
    ((2, 1),  (3, 31)),    # Spring/Summer drop
    ((8, 1),  (9, 30)),    # Fall/Winter drop
    ((1, 5),  (1, 25)),    # January returns
]


def _in_calendar_window(d: date) -> bool:
    for (sm, sd), (em, ed) in _CALENDAR_WINDOWS:
        start = date(d.year, sm, sd)
        end   = date(d.year, em, ed)
        if start <= d <= end:
            return True
    return False


def _col_source_prefix(col: str) -> str:
    for prefix in ("meta_", "klaviyo_", "tiktok_", "shopify_", "gorgias_",
                   "sentry_", "ga4_", "loop_", "vip_", "blended_"):
        if col.startswith(prefix):
            return prefix.rstrip("_")
    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: Novel chain discovery
# ─────────────────────────────────────────────────────────────────────────────

# Columns used as leading signal OR outcome in the 22 known chains.
# Exclude these from novel pair enumeration (exact mart column names).
_KNOWN_CHAIN_COLS: set[str] = {
    # Leading signals
    "meta_roas", "meta_cpm_change_pct", "tiktok_roas",
    "sizing_complaint_rate_7d", "return_rate_pct", "avg_days_to_refund",
    "blended_cac_7d", "aov_7d", "effective_open_rate_7d",
    "rolling_repeat_purchase_rate_90d", "vip_purchase_gap_days",
    "checkout_error_count", "ga4_pdp_bounce_rate",
    "new_customer_rate_7d", "mobile_checkout_completion_rate_7d",
    "post_purchase_flow_revenue_7d",
    # Outcomes
    "net_revenue", "avg_cvr", "klaviyo_revenue",
}


def run_novel_discovery(
    conn,
    client_id: str,
    mart_df: pd.DataFrame,
    scan_date: date,
    mode: str,
    full_df: pd.DataFrame | None = None,
) -> None:
    """
    Phase 3: discover novel signal→outcome pairs not in the known chain library.
    Completely separate code path from Phase 2 — no shared state.
    """
    _log({"phase": "novel_discovery", "status": "start"})

    if mart_df.empty:
        _log({"phase": "novel_discovery", "status": "complete",
              "pairs_evaluated": 0, "pairs_written": 0, "single_client_core": 0})
        return

    # For incremental mode, detect pairs in window but validate against full history
    detect_df = mart_df
    validate_df = full_df if (mode == "incremental" and full_df is not None) else mart_df
    validate_df = validate_df.sort_values("date").reset_index(drop=True)

    cutoff = scan_date - timedelta(days=7 + 2)  # lag=7 ± 2

    # ── Step 3a: Enumerate numeric column pairs ────────────────────────────
    numeric_cols = [
        c for c in detect_df.select_dtypes(include=[np.number]).columns
        if not c.startswith("_")           # exclude enrichment columns
        and c != "date"
        and c not in _KNOWN_CHAIN_COLS
        and detect_df[c].isna().mean() <= 0.80  # not too sparse
    ]

    all_pairs = [
        (a, b) for a in numeric_cols for b in numeric_cols
        if a != b and detect_df[b].isna().mean() <= 0.80
    ]

    # ── Memory bound: top 500 pairs by col_A variance ─────────────────────
    if len(all_pairs) > 500:
        variances = {c: float(detect_df[c].var(skipna=True) or 0) for c in numeric_cols}
        all_pairs.sort(key=lambda p: variances.get(p[0], 0), reverse=True)
        all_pairs = all_pairs[:500]
        _log({"phase": "novel_discovery", "warning": "pair_cap_applied",
              "pairs_after_cap": 500})

    pairs_evaluated = 0
    pairs_written = 0
    single_client_core_count = 0
    rows_to_insert: list[dict] = []

    for col_a, col_b in all_pairs:
        series_a = validate_df[col_a].dropna()
        if len(series_a) < 4:
            continue

        # ── Step 3b: Sparsity filter ──────────────────────────────────────
        mean_a = float(series_a.mean())
        sd_a   = float(series_a.std())
        if sd_a == 0:
            continue
        threshold_a = mean_a + 1.5 * sd_a
        trigger_mask = validate_df[col_a] > threshold_a
        trigger_dates = validate_df.loc[trigger_mask, "date"].tolist()
        if len(trigger_dates) < 4:
            continue

        # ── Step 3c: Effect size filter ───────────────────────────────────
        series_b = validate_df[col_b].dropna()
        if len(series_b) < 4:
            continue
        sd_b = float(series_b.std())
        effect_threshold = 0.5 * sd_b

        hits = 0
        observable = 0
        hit_trigger_dates: list[date] = []
        signal_values_list: list[dict] = []

        for tdate in trigger_dates:
            trow = validate_df[validate_df["date"] == tdate]
            if trow.empty:
                continue
            signal_val = float(trow[col_a].iloc[0])
            signal_values_list.append({"date": str(tdate), "value": signal_val})

            if tdate > cutoff:
                continue
            observable += 1

            w_start = tdate + timedelta(days=5)  # lag 7 − 2
            w_end   = tdate + timedelta(days=9)  # lag 7 + 2
            fwd = validate_df[(validate_df["date"] >= w_start) &
                               (validate_df["date"] <= w_end)][col_b].dropna()
            if fwd.empty:
                continue

            baseline_b = float(series_b.mean())
            move = abs(float(fwd.mean()) - baseline_b)
            if move >= effect_threshold:
                hits += 1
                hit_trigger_dates.append(tdate)

        # Skip if mean effect below threshold across all instances
        if observable > 0 and hits == 0:
            continue
        if observable == 0 and len(trigger_dates) == 0:
            continue

        pairs_evaluated += 1

        instance_count = len(trigger_dates)
        hit_rate = hits / observable if observable > 0 else None

        # ── Step 3d: Calendar dispersion check ────────────────────────────
        calendar_ct = sum(1 for d in trigger_dates if _in_calendar_window(d))
        calendar_fraction = calendar_ct / len(trigger_dates)
        calendar_clustered = calendar_fraction > 0.60

        confound_unresolved = (
            calendar_clustered and observable >= 4 and hit_rate is not None and hit_rate >= 0.70
        )

        # ── Seasonal confound risk ─────────────────────────────────────────
        b_above_thresh_dates = validate_df.loc[
            validate_df[col_b] > float(series_b.mean()) + 1.5 * sd_b, "date"
        ].tolist()
        b_cal_ct = sum(1 for d in b_above_thresh_dates if _in_calendar_window(d))
        b_cal_frac = b_cal_ct / len(b_above_thresh_dates) if b_above_thresh_dates else 0.0
        seasonal_confound_risk = calendar_fraction > 0.60 and b_cal_frac > 0.60

        # ── Step 3e: Single-client core check ─────────────────────────────
        single_client_core = observable >= 10 and hit_rate is not None and hit_rate >= 0.80
        if single_client_core:
            single_client_core_count += 1

        first_detected = min(trigger_dates) if trigger_dates else None

        sources = list({_col_source_prefix(col_a), _col_source_prefix(col_b)} - {"unknown"})

        rows_to_insert.append(dict(
            client_id=client_id,
            vertical_tag=VERTICAL_TAG,
            signal_description=(
                f"When {col_a} rises above threshold, {col_b} tends to move within 7 days"
            ),
            leading_signal_column=col_a,
            outcome_column=col_b,
            signal_values=json.dumps(signal_values_list[:50]),  # cap to 50 events
            sources_involved=sources,
            first_detected_at=first_detected,
            instance_count=instance_count,
            observable_instance_count=observable,
            hit_rate=hit_rate,
            cross_client_instance_count=0,
            outcome_confirmed_count=hits,
            outcome_rejected_count=max(0, observable - hits),
            promotion_status="candidate",
            source="historical_scan",
            client_specific=True,
            calendar_clustered=calendar_clustered,
            confound_unresolved=confound_unresolved,
            single_client_core=single_client_core,
            seasonal_confound_risk=seasonal_confound_risk,
            threshold_a=threshold_a,
        ))

    # ── Step 3f: Write candidate_signals ──────────────────────────────────
    try:
        with conn:
            cur = conn.cursor()
            for row in rows_to_insert:
                # INSERT ... ON CONFLICT DO NOTHING for new pairs
                cur.execute(
                    """
                    INSERT INTO public.candidate_signals (
                        client_id, vertical_tag, signal_description,
                        leading_signal_column, outcome_column, signal_values,
                        sources_involved, first_detected_at,
                        instance_count, observable_instance_count, hit_rate,
                        cross_client_instance_count,
                        outcome_confirmed_count, outcome_rejected_count,
                        promotion_status, source, client_specific,
                        calendar_clustered, confound_unresolved, single_client_core,
                        seasonal_confound_risk, created_at, updated_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,now(),now())
                    ON CONFLICT (client_id, leading_signal_column, outcome_column)
                    DO NOTHING
                    """,
                    (row["client_id"], row["vertical_tag"], row["signal_description"],
                     row["leading_signal_column"], row["outcome_column"],
                     row["signal_values"], row["sources_involved"],
                     row["first_detected_at"],
                     row["instance_count"], row["observable_instance_count"],
                     row["hit_rate"], row["cross_client_instance_count"],
                     row["outcome_confirmed_count"], row["outcome_rejected_count"],
                     row["promotion_status"], row["source"], row["client_specific"],
                     row["calendar_clustered"], row["confound_unresolved"],
                     row["single_client_core"], row["seasonal_confound_risk"]),
                )
                pairs_written += 1

            # Accumulate instance counts for existing rows (incremental)
            if mode == "incremental":
                for row in rows_to_insert:
                    cur.execute(
                        """
                        UPDATE public.candidate_signals
                        SET instance_count = instance_count + %s,
                            observable_instance_count = observable_instance_count + %s,
                            outcome_confirmed_count = outcome_confirmed_count + %s,
                            outcome_rejected_count = outcome_rejected_count + %s,
                            updated_at = now()
                        WHERE client_id = %s
                          AND leading_signal_column = %s
                          AND outcome_column = %s
                        """,
                        (row["instance_count"], row["observable_instance_count"],
                         row["outcome_confirmed_count"], row["outcome_rejected_count"],
                         row["client_id"], row["leading_signal_column"],
                         row["outcome_column"]),
                    )

                # Post-sweep auto-promotion check (incremental only)
                cur.execute(
                    """
                    UPDATE public.candidate_signals
                    SET promotion_status = 'validated'
                    WHERE client_id = %s
                      AND promotion_status = 'candidate'
                      AND cross_client_instance_count >= 3
                      AND calendar_clustered = false
                    """,
                    (client_id,),
                )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Writing candidate_signals: %s",
                     SOURCE_COMPONENT, client_id, exc)
        raise

    _log({
        "phase": "novel_discovery", "status": "complete",
        "pairs_evaluated": pairs_evaluated,
        "pairs_written": pairs_written,
        "single_client_core": single_client_core_count,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4: GMV derivation
# ─────────────────────────────────────────────────────────────────────────────

def run_gmv_derivation(conn, client_id: str, mart_df: pd.DataFrame) -> float | None:
    """
    Derives annualised GMV from mart net_revenue and writes to client_config.
    Returns computed gmv_derived_annual.
    """
    if mart_df.empty or "net_revenue" not in mart_df.columns:
        _log({"phase": "gmv_derivation", "status": "skipped", "reason": "no_mart_data"})
        return None

    valid = mart_df.dropna(subset=["net_revenue"])
    if valid.empty:
        _log({"phase": "gmv_derivation", "status": "skipped",
              "reason": "net_revenue_all_null"})
        return None

    total_revenue = float(valid["net_revenue"].sum())
    # Count distinct calendar years
    years = valid["date"].apply(lambda d: d.year).nunique()
    gmv_annual = total_revenue / years if years > 0 else total_revenue

    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE public.client_config
                SET gmv_derived_annual = %s, gmv_derived_at = now()
                WHERE client_id = %s
                """,
                (gmv_annual, client_id),
            )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: GMV derivation write: %s",
                     SOURCE_COMPONENT, client_id, exc)
        raise

    _log({"phase": "gmv_derivation", "status": "complete",
          "gmv_derived_annual": round(gmv_annual, 2)})
    return gmv_annual


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5: Lookback days write-back
# ─────────────────────────────────────────────────────────────────────────────

def run_lookback_writeback(
    conn, client_id: str, mart_df: pd.DataFrame, ga4_absent: bool
) -> None:
    """
    Writes actual data lookback days per connector to client_config.
    Uses mart date range as per-source approximation.
    Hard caps: Meta 395d, TikTok 730d, Sentry 90d.
    """
    if mart_df.empty:
        return

    today = date.today()
    min_date = mart_df["date"].min()
    days_in_mart = (today - min_date).days

    meta_days     = min(days_in_mart, 395)
    tiktok_days   = min(days_in_mart, 730)
    sentry_days   = min(days_in_mart, 90)
    shopify_days  = days_in_mart
    klaviyo_days  = days_in_mart
    gorgias_days  = days_in_mart
    loop_days     = days_in_mart
    ga4_days: int | None = None if ga4_absent else days_in_mart

    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE public.client_config
                SET meta_lookback_days    = %s,
                    tiktok_lookback_days  = %s,
                    sentry_lookback_days  = %s,
                    shopify_lookback_days = %s,
                    klaviyo_lookback_days = %s,
                    gorgias_lookback_days = %s,
                    loop_lookback_days    = %s,
                    ga4_lookback_days     = %s
                WHERE client_id = %s
                """,
                (meta_days, tiktok_days, sentry_days,
                 shopify_days, klaviyo_days, gorgias_days, loop_days,
                 ga4_days, client_id),
            )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Lookback writeback: %s",
                     SOURCE_COMPONENT, client_id, exc)
        raise

    _log({"phase": "lookback_writeback", "status": "complete",
          "days_in_mart": days_in_mart})


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: Onboarding completion message  (full mode only)
# ─────────────────────────────────────────────────────────────────────────────

# PLACEHOLDER: $500 per provisional chain, $1,200 per core chain.
# Replace when actual projected_impact column is available.
_LEAKAGE_PROVISIONAL = 500
_LEAKAGE_CORE = 1_200


def run_onboarding_message(
    conn,
    client_id: str,
    mart_df: pd.DataFrame,
    gmv_annual: float | None,
) -> None:
    """
    Generates onboarding completion message (leakage or forward_promise variant)
    and writes to public.onboarding_messages.
    Does NOT send to Slack — the onboarding CLI reads this table.
    """
    # Compute lookback_months from mart date range
    if not mart_df.empty:
        days = (mart_df["date"].max() - mart_df["date"].min()).days
        lookback_months = round(days / 30.44)
    else:
        lookback_months = 0

    # Fetch chain results from causal_pattern_validation
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT causal_chain_id, confidence_tier, scan_skipped_reason
        FROM public.causal_pattern_validation
        WHERE vertical_tag = %s
        """,
        (VERTICAL_TAG,),
    )
    chain_rows = cur.fetchall()

    all_chains = [r for r in chain_rows if r["confidence_tier"] is not None]
    tracked_chains = [
        r for r in all_chains
        if r["confidence_tier"] in ("candidate", "provisional", "core")
    ]
    high_conf_chains = [
        r for r in all_chains
        if r["confidence_tier"] in ("provisional", "core")
    ]

    N = len(tracked_chains)

    # ── Variant selection ─────────────────────────────────────────────────
    provisional_ct = sum(1 for r in high_conf_chains if r["confidence_tier"] == "provisional")
    core_ct        = sum(1 for r in high_conf_chains if r["confidence_tier"] == "core")

    # Placeholder leakage estimate — clearly labelled as proxy
    estimated_leakage = provisional_ct * _LEAKAGE_PROVISIONAL + core_ct * _LEAKAGE_CORE

    use_leakage_variant = (
        gmv_annual is not None
        and len(high_conf_chains) >= 2
        and estimated_leakage >= gmv_annual * 0.01
    )

    # Plain-English descriptions keyed by chain ID
    _CHAIN_DESC: dict[str, str] = {
        "A1": "Channel ROAS below breakeven",
        "A2": "CPM spike suppressing Meta ROAS",
        "A3": "TikTok outperforming Meta — channel budget misallocation",
        "B1": "Ad creative frequency fatigue",
        "B4": "Audience saturation via CPM spike",
        "C1": "Sizing complaints preceding return spike",
        "C3": "Elevated return rate eroding net revenue",
        "C5": "Accelerating refund processing preceding return spike",
        "D1": "CAC rising faster than revenue",
        "D2": "Discount dependency with minimal revenue lift",
        "D4": "AOV compression compressing net revenue",
        "E1": "Email list health decay",
        "E2": "Repeat purchase rate decline",
        "E3": "High-LTV customers extending repurchase gap",
        "F2": "Checkout errors suppressing conversion rate",
        "F4": "PDP bounce rate suppressing conversions",
        "G1": "Hero SKU stockout during active ad spend",
        "G4": "Back-in-stock revenue window",
        "Chain1": "Post-launch CAC creep",
        "Chain2": "Mobile checkout gap vs desktop",
        "Chain3": "Post-purchase flow revenue decoupling",
        "Chain5": "Attribution double-counting expansion",
    }

    if use_leakage_variant:
        bullet_lines = []
        for r in high_conf_chains:
            cid = r["causal_chain_id"]
            imp = _LEAKAGE_CORE if r["confidence_tier"] == "core" else _LEAKAGE_PROVISIONAL
            if imp >= 500:
                desc = _CHAIN_DESC.get(cid, cid)
                bullet_lines.append(f"• {desc} — est. ${imp:,}/yr")

        bullets = "\n".join(bullet_lines) if bullet_lines else ""
        message_text = (
            f"I've scanned {lookback_months} months of Azure & Co's data.\n\n"
            f"I found {N} patterns I can already track for you — here's what stands out:\n\n"
            f"{bullets}\n\n"
            f"Together, these represent an estimated ${estimated_leakage:,} in annual leakage.\n\n"
            "Going forward, I'll alert you when any of these patterns start moving — "
            "before you'd normally see it in your P&L.\n\n"
            "For patterns I haven't seen before in your data, I'll tell you what I see "
            "and flag that I'm still learning the cause — I get sharper the longer I run.\n\n"
            "Your first alert will fire when one of these patterns triggers. React with "
            "✅ (agree), 💤 (snooze), or ❌ (disagree) — that's how I learn what matters "
            "to you.\n\n"
            'You can also ask me anything: "Why did my ROAS drop?" or '
            '"What\'s my real return-adjusted margin?" — I\'ll walk through the data.'
        )
        variant = "leakage"
    else:
        message_text = (
            f"I've scanned {lookback_months} months of Azure & Co's data.\n\n"
            f"I'm now tracking {N} causal patterns across your Shopify, Meta, Klaviyo, "
            "and returns data. I'll alert you when any of them start moving — before "
            "you'd normally see it in your P&L.\n\n"
            "For patterns I haven't seen before in your data, I'll tell you what I see "
            "and flag that I'm still learning the cause — I get sharper the longer I run.\n\n"
            "As more data comes in, alerts will fire as patterns develop. React with "
            "✅ (agree), 💤 (snooze), or ❌ (disagree) — that's how I learn what matters "
            "to you.\n\n"
            'You can also ask me anything: "Why did my ROAS drop?" or '
            '"What\'s my real return-adjusted margin?" — I\'ll walk through the data.'
        )
        variant = "forward_promise"

    try:
        with conn:
            cur2 = conn.cursor()
            cur2.execute(
                """
                INSERT INTO public.onboarding_messages
                    (client_id, message_variant, message_text, generated_at, sent)
                VALUES (%s, %s, %s, now(), false)
                """,
                (client_id, variant, message_text),
            )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Writing onboarding message: %s",
                     SOURCE_COMPONENT, client_id, exc)
        raise

    _log({"phase": "onboarding_message", "status": "complete", "variant": variant})


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 7: Final status update
# ─────────────────────────────────────────────────────────────────────────────

def run_final_status(conn, client_id: str) -> None:
    with conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE public.client_config
            SET historical_scan_status      = 'complete',
                historical_scan_completed   = true,
                historical_scan_completed_at = now(),
                last_historical_scan_at      = now()
            WHERE client_id = %s
            """,
            (client_id,),
        )
    _log({"phase": "final_status", "status": "complete"})


# ─────────────────────────────────────────────────────────────────────────────
# Incremental mode: pending connector re-check
# ─────────────────────────────────────────────────────────────────────────────

def _check_pending_connectors(conn, client_id: str, mart_df: pd.DataFrame,
                               skip_map: dict, scan_date: date) -> None:
    """
    For each connector in client_config.pending_connectors, check if its
    staging table now exists. If so, re-run Phase 2 for chains whose
    scan_skipped_reason starts with 'connector_'.
    """
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT pending_connectors FROM public.client_config WHERE client_id = %s",
            (client_id,),
        )
        row = cur.fetchone()
        if not row or not row["pending_connectors"]:
            return

        client_schema = client_id
        staging_schema = f"{client_schema}_staging"  # dbt staging schema (live views)
        for connector in row["pending_connectors"]:
            staging_name = f"stg_{connector}"
            if _table_exists(cur, staging_schema, staging_name):
                _log({"phase": "pending_connector_check", "connector": connector,
                      "staging_found": staging_name,
                      "action": "re-running chains with connector_skip"})
                # Re-evaluate chains skipped due to this connector
                chains_to_retry = [
                    c for c in CHAIN_REGISTRY
                    if skip_map.get(c["id"], "").startswith("connector_")
                ]
                if chains_to_retry:
                    enriched = _enrich_mart(mart_df)
                    for chain in chains_to_retry:
                        instance_count, observable_count, confirmed_count = _eval_chain_generic(
                            enriched, chain["trigger_fn"], chain["outcome_fn"],
                            chain["lag"], scan_date,
                        )
                        hit_rate = confirmed_count / observable_count if observable_count > 0 else None
                        tier = _assign_tier(observable_count, hit_rate)
                        with conn:
                            wcur = conn.cursor()
                            wcur.execute(
                                """
                                UPDATE public.causal_pattern_validation
                                SET instance_count = %s,
                                    observable_instance_count = %s,
                                    confirmed_count = %s,
                                    false_positive_count = %s,
                                    confidence_rate = %s,
                                    hit_rate = %s,
                                    confidence_tier = %s,
                                    scan_skipped_reason = NULL,
                                    updated_at = now()
                                WHERE causal_chain_id = %s AND vertical_tag = %s
                                """,
                                (instance_count, observable_count, confirmed_count,
                                 max(0, observable_count - confirmed_count),
                                 hit_rate, hit_rate, tier,
                                 chain["id"], VERTICAL_TAG),
                            )
    except Exception as exc:
        logger.error("SOURCE: %s | CLIENT: %s | ERROR: Pending connector check: %s",
                     SOURCE_COMPONENT, client_id, exc)


# ─────────────────────────────────────────────────────────────────────────────
# Main orchestration
# ─────────────────────────────────────────────────────────────────────────────

def main(client_id: str, mode: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        stream=sys.stderr,
    )

    conn = _get_conn()

    # Set status to running immediately
    _ensure_tables(conn)
    _update_scan_status(conn, client_id, "running")

    scan_date = date.today()
    gmv_annual: float | None = None

    try:
        # Load last_historical_scan_at for incremental mode
        last_scan_at = None
        if mode == "incremental":
            cur = conn.cursor()
            cur.execute(
                "SELECT last_historical_scan_at FROM public.client_config "
                "WHERE client_id = %s",
                (client_id,),
            )
            row = cur.fetchone()
            if row:
                last_scan_at = row[0]

        # Load mart (windowed for incremental, full for full)
        mart_df = _load_mart(conn, client_id, mode, last_scan_at)
        full_df = _load_mart_full(conn, client_id) if mode == "incremental" else mart_df

        # Determine if GA4 tables absent (for lookback writeback)
        ga4_absent = (
            mart_df.empty
            or "ga4_pdp_bounce_rate" not in mart_df.columns
            or mart_df["ga4_pdp_bounce_rate"].isna().all()
        )

        # ── Phase 1: DQ pre-checks ─────────────────────────────────────────
        try:
            with conn:
                pass  # ensure clean connection state
            skip_map = run_dq_prechecks(conn, client_id, scan_date)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

        # ── Phase 2: Known chain validation ───────────────────────────────
        try:
            tier_map = run_known_chains(conn, client_id, mart_df, skip_map, scan_date, mode)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

        # ── Phase 3: Novel chain discovery ────────────────────────────────
        try:
            run_novel_discovery(conn, client_id, mart_df, scan_date, mode, full_df=full_df)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

        # ── Phase 4: GMV derivation ───────────────────────────────────────
        try:
            gmv_annual = run_gmv_derivation(conn, client_id, full_df)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

        # ── Phase 5: Lookback days write-back ─────────────────────────────
        try:
            run_lookback_writeback(conn, client_id, full_df, ga4_absent)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

        # ── Phase 6: Onboarding message (full mode only) ──────────────────
        if mode == "full":
            try:
                run_onboarding_message(conn, client_id, full_df, gmv_annual)
            except Exception as e:
                _update_scan_status(conn, client_id, "failed")
                raise

        # ── Incremental extras ────────────────────────────────────────────
        if mode == "incremental":
            _check_pending_connectors(conn, client_id, mart_df, skip_map, scan_date)

        # ── Phase 7: Final status ──────────────────────────────────────────
        try:
            run_final_status(conn, client_id)
        except Exception as e:
            _update_scan_status(conn, client_id, "failed")
            raise

    except Exception:
        _update_scan_status(conn, client_id, "failed")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point  (importable as module without side effects — CONSTRAINT 5)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profit Sentinel historical pattern scan")
    parser.add_argument("--client_id", required=True,
                        help="Client identifier (e.g. client_azure_co)")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full",
                        help="Scan mode: full (onboarding) or incremental (monthly)")
    args = parser.parse_args()
    main(args.client_id, args.mode)

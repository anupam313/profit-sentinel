-- ================================================
-- MANUALLY DESIGNED SCHEMA — NOT FROM REAL AIRBYTE SYNC
-- Created: 2026-05-14
-- ================================================
-- These tables are safe to use for:
-- - Synthetic data (Step 5 seed script)
-- - dbt staging and mart models on synthetic data
-- - Agent A/B/C/D testing against synthetic data
--
-- Must be re-verified before:
-- - Connecting a real client Loop Returns account
-- - Treating dbt output as production-accurate
-- - Activating Loop signals in Agent A for live client
--
-- Re-verification process when real client onboards:
-- 1. Connect Loop Returns via Airbyte → client schema
-- 2. Run schema_discovery.py against real Airbyte tables
-- 3. Compare real column names against these placeholders
-- 4. If names differ: update dbt models and agent logic
-- 5. Drop placeholder tables once real tables confirmed
-- ================================================

CREATE TABLE IF NOT EXISTS client_azure_co.loop_returns (
    id                      bigint          primary key,
    order_id                bigint,
    customer_id             bigint,
    status                  text,
    return_type             text,
    created_at              timestamptz,
    updated_at              timestamptz,
    processed_at            timestamptz,
    total_refund_amount     numeric,
    currency                text,
    destination             text,
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);

CREATE TABLE IF NOT EXISTS client_azure_co.loop_return_line_items (
    id                      bigint          primary key,
    return_id               bigint,
    order_line_item_id      bigint,
    variant_id              bigint,
    product_id              bigint,
    sku                     text,
    quantity                integer,
    return_reason           text,
    return_reason_detail    text,
    condition               text,
    price                   numeric,
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);

CREATE TABLE IF NOT EXISTS client_azure_co.loop_refunds (
    id                      bigint          primary key,
    return_id               bigint,
    amount                  numeric,
    currency                text,
    status                  text,
    refund_method           text,
    created_at              timestamptz,
    _airbyte_extracted_at   timestamptz,
    is_synthetic            boolean default false
);

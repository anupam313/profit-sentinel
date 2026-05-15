-- ============================================================
-- Loop Returns — Corrected Schema
-- Updated: 2026-05-15 (original: 2026-05-14)
-- Authority: Loop Returns API — detailed-returns-list endpoint
--   docs.loopreturns.com/api-reference/latest/return-data/
--   detailed-returns-list
-- ============================================================
-- CORRECTIONS vs 2026-05-14 placeholder schema:
--
-- loop_returns:
--   id:         text (was bigint — Loop IDs are strings)
--   state:      replaces status (actual API field name)
--   type:       replaces return_type (actual API field name)
--   customer:   text replaces customer_id bigint (API returns
--               customer as a string identifier, not integer)
--   processed_at: REMOVED — field does not exist in API
--   destination_id: replaces destination (actual field name)
--   total_refund_amount: REMOVED — replaced by 11 separate
--               financial fields matching API response:
--               return_product_total, return_discount_total,
--               return_tax_total, return_total,
--               return_credit_total, exchange_product_total,
--               exchange_discount_total, exchange_tax_total,
--               exchange_total, exchange_credit_total, refund
--   30 new fields added: origin_country, multi_currency,
--               gift_card*, handling_fee, upsell, carrier,
--               tracking_number, label_*, status_page_url,
--               package_reference, return_method, exchanges,
--               labels, and exchange financial fields
--
-- loop_return_line_items:
--   line_item_id text: replaces id bigint (actual field name)
--   return_id text: added as FK to loop_returns.id
--   provider_line_item_id: replaces order_line_item_id
--   quantity: REMOVED — field does not exist in API response
--   price, discount, tax: text (were numeric — API returns
--               all financial values as strings)
--   title, barcode: new fields from API
--   refund, refund_item, refund_tax: new per-line refund fields
--   outcome, returned_at, exchange_variant: new from API
--   consolidation_tracking/destination_id: new from API
--   condition, disposition: new jsonb objects from API
--   return_reason_detail: REMOVED — API uses return_comment
--
-- loop_refunds: DROPPED — this table has no corresponding
--   API endpoint in Loop Returns. Refund data is embedded
--   in loop_returns.refund (total refund amount) and in
--   loop_return_line_items (refund, refund_item, refund_tax
--   per line). The placeholder was not backed by a real API
--   entity. Drop the table and clear the registry.
-- ============================================================
-- Safe to use for:
--   - Synthetic data (Step 5 seed script)
--   - dbt staging and mart models on synthetic data
--   - Agent A/B/C/D testing against synthetic data
--
-- Must re-verify before:
--   - Connecting a real client Loop Returns account
--   - Treating dbt output as production-accurate
--   - Activating Loop signals in Agent A for live client
-- ============================================================


CREATE TABLE IF NOT EXISTS client_azure_co.loop_returns (
    -- Primary key (text — Loop IDs are strings, not integers)
    id                          text primary key,

    -- State and type (actual API field names)
    state                       text,   -- pending | in_transit | received |
                                        -- resolved | cancelled
    type                        text,   -- standard | exchange_only | etc.
    outcome                     text,   -- refund | exchange | store_credit |
                                        -- donate | repair | keep | etc.

    -- Timestamps (API returns ISO 8601 strings)
    created_at                  text,
    updated_at                  text,
    edited_at                   text,
    label_updated_at            text,

    -- Order references (all strings from API)
    order_id                    text,   -- Shopify order ID
    order_name                  text,   -- e.g. '#1234'
    order_number                text,
    provider_order_id           text,
    provider_order_number       text,

    -- Customer (API returns as string identifier, not FK)
    customer                    text,

    -- Geography
    origin_country              text,
    origin_country_code         text,

    -- Currency
    currency                    text,
    multi_currency              boolean,

    -- Financial totals (all text — API returns as strings;
    -- python_transformer casts to numeric in staging)
    return_product_total        text,
    return_discount_total       text,
    return_tax_total            text,
    return_total                text,
    return_credit_total         text,
    exchange_product_total      text,
    exchange_discount_total     text,
    exchange_tax_total          text,
    exchange_total              text,
    exchange_credit_total       text,
    gift_card                   text,
    gift_card_order_name        text,
    gift_card_order_id          text,
    handling_fee                text,
    refund                      text,   -- total refund amount for this return
    upsell                      text,

    -- Shipping and label
    carrier                     text,
    tracking_number             text,
    label_status                text,
    label_url                   text,
    label_rate                  text,
    status_page_url             text,

    -- Return destination
    destination_id              text,
    package_reference           text,

    -- Nested objects (raw API shape preserved; transformer
    -- extracts specific fields into staging as needed)
    return_method               jsonb,  -- {provider, method_type, address,
                                        --  state, rma_id, qr_code_url,
                                        --  scheduled_at, scannable_id}
    exchanges                   jsonb,  -- array of exchange line items
                                        -- [{exchange_id, exchange_order_id,
                                        --   product_id, variant_id, sku, ...}]
    labels                      jsonb,  -- array of shipping label objects

    -- Pipeline
    _airbyte_extracted_at       timestamptz,
    is_synthetic                boolean default false
);


CREATE TABLE IF NOT EXISTS client_azure_co.loop_return_line_items (
    -- Surrogate key: Loop's line_item_id is Loop-internal.
    -- Composite uniqueness enforced by UNIQUE constraint.
    line_item_id                text,
    return_id                   text not null,  -- FK to loop_returns.id

    -- Product identifiers (all text — API returns as strings)
    provider_line_item_id       text,   -- Shopify line item ID
    product_id                  text,
    variant_id                  text,
    sku                         text,
    barcode                     text,
    title                       text,

    -- Financial per line (text — cast to numeric in staging)
    price                       text,
    discount                    text,
    tax                         text,
    refund                      text,       -- line-level refund total
    refund_item                 text,       -- item portion of refund
    refund_tax                  text,       -- tax portion of refund

    -- Return details
    return_reason               text,
    parent_return_reason        text,
    return_comment              text,
    outcome                     text,
    returned_at                 text,       -- ISO datetime string
    exchange_variant            text,

    -- Logistics
    provider_restock_location_id    text,
    consolidation_tracking          text,
    consolidation_destination_id    text,

    -- Inspection objects (raw API shape as jsonb)
    condition                   jsonb,      -- {description, condition_category,
                                            --  return_processor, note,
                                            --  inspected_at, images}
    disposition                 jsonb,      -- {disposition_outcome,
                                            --  return_processor, note,
                                            --  inspected_at}

    -- Pipeline
    _airbyte_extracted_at       timestamptz,
    is_synthetic                boolean default false,

    UNIQUE (return_id, line_item_id)
);


-- loop_refunds: intentionally not created.
-- No Loop Returns API endpoint exposes refunds as a
-- separate collection. Refund data lives in:
--   loop_returns.refund           (total refund amount)
--   loop_return_line_items.refund (per-line item refund)
--   loop_return_line_items.refund_item
--   loop_return_line_items.refund_tax
-- The 2026-05-14 placeholder was an incorrect assumption.
-- Any existing loop_refunds table in client_azure_co is
-- dropped by _run_loop_returns.py.

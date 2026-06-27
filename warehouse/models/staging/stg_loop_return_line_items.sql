-- Filtered Loop return line items. One row per line_item_id.
-- HERO (return-driver) reads this for SKU-level return reason; the RULE-3
-- per-client synthetic filter is applied HERE so the mart never reads raw.
--
-- Provenance note: loop_return_line_items carries NO order_id, NO numeric id,
-- and NO stored is_synthetic column. The seed isolates synthetic returns by
-- the PARENT order (Shopify spine), so provenance is TRANSITIVE via the parent
-- header loop_returns.order_id. We derive is_synthetic from the header and join
-- on return_id. stg_loop_returns is intentionally NOT modified (it is shared
-- with the C1 sizing-complaint path); loop_returns is read here for the derive
-- only.
with returns_provenance as (
    -- REGEX form (NOT ::bigint): text-safe. A real Shopify order GID
    -- (e.g. 'gid://shopify/Order/...') or any non-7-digit id tests FALSE
    -- (=> real) instead of throwing a cast error — the genuinely fail-closed
    -- choice (RULE 4: no raw type cast). Synthetic spine ids are 7-digit
    -- numerics (< 13 digits); real Shopify numeric ids are 13+ digits.
    select
        return_id,
        (order_id ~ '^[0-9]+$' and length(order_id) < 13) as is_synthetic
    from {{ source('client_azure_co', 'loop_returns') }}
),

li as (
    select
        line_item_id,
        return_id,
        order_line_item_id,
        sku,
        quantity,
        return_reason_primary,
        return_reason_secondary,
        condition_received,
        restockable,
        return_lag_segment
    from {{ source('client_azure_co', 'loop_return_line_items') }}
)

select
    li.line_item_id,
    li.return_id,
    li.order_line_item_id,
    li.sku,
    li.quantity,
    li.return_reason_primary,
    li.return_reason_secondary,
    li.condition_received,
    li.restockable,
    li.return_lag_segment,
    -- ORPHAN line item (return_id with no header) => fail-closed REAL: never
    -- leak as synthetic. The not_null test on return_id (schema.yml) is the
    -- loud tripwire so an orphan cannot vanish silently (R9 presence lesson).
    coalesce(rp.is_synthetic, false) as is_synthetic

from li
left join returns_provenance rp on li.return_id = rp.return_id
-- RULE 3 (per-client form): synthetic rows visible only when the client's
-- toggle is on; real rows always survive.
where (
    coalesce(rp.is_synthetic, false) = false
    or (select use_synthetic_data from public.client_config
        where client_id = '{{ var("client_id") }}') = true
)

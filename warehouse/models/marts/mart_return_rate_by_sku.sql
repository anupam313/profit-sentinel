-- SKU-level return rate. Agent A uses this to detect return spikes by product.
-- Reason source is native-PRIMARY with a Loop SUPPLEMENT (owed-J): the native
-- Shopify returnReasonDefinition.handle takes precedence and Loop fills the gap.
-- The native slot is inert today (see native_reason) so output is 100% Loop
-- until J-1 wires the handle at first live connect.
with sold as (
    select
        sku,
        sum(quantity)           as units_sold,
        sum(gross_line_revenue) as gross_revenue_sold,
        count(distinct order_id) as orders_with_sku
    from {{ ref('stg_shopify_order_line_items') }}
    where sku is not null
    group by sku
),

native_reason as (
    -- J-1 NATIVE HANDLE SLOT — do NOT fill now. shopify_order_refunds.return is
    -- 100% NULL pre-pilot; its nesting/casing is OWED. At first live connect:
    -- unnest refund_line_items -> sku, extract return->...->>'handle', map to
    -- canonical handles, and filter via staging. `where false` => zero rows =>
    -- the COALESCE below always falls through to Loop, so HERO stays 100% Loop
    -- until this is wired.
    select
        null::text as sku,
        null::text as native_return_reason_handle
    where false
),

returned as (
    select
        li.sku,
        sum(li.quantity)                                    as units_returned,
        count(distinct li.return_id)                        as return_count,
        sum(r.refund_amount) / nullif(count(li.line_item_id), 0) as avg_refund_per_return,
        -- native-PRIMARY, Loop-SUPPLEMENT: native handle wins when present;
        -- today native is always NULL so this resolves to the Loop reason and
        -- output is identical to the prior raw-Loop mart.
        mode() within group (
            order by coalesce(nr.native_return_reason_handle, li.return_reason_primary)
        )                                                   as primary_return_reason,
        mode() within group (order by r.return_lag_segment)     as dominant_lag_segment
    from {{ ref('stg_loop_return_line_items') }} li
    inner join {{ ref('stg_loop_returns') }} r on li.return_id = r.return_id
    left join native_reason nr on nr.sku = li.sku
    where li.sku is not null
    group by li.sku
),

costs as (
    -- Most recent active cost record per SKU
    select distinct on (sku)
        sku,
        landed_cost
    from {{ source('client_azure_co', 'sku_cost_master') }}
    -- RULE 3 (per-client form): sku_cost_master carries a stored is_synthetic;
    -- gate on the client_config table value, not the dbt var.
    where (
        is_synthetic = false
        or (select use_synthetic_data from public.client_config
            where client_id = '{{ var("client_id") }}') = true
    )
    order by sku, effective_from desc
)

select
    s.sku,
    s.units_sold,
    s.gross_revenue_sold,
    s.orders_with_sku,
    coalesce(r.units_returned, 0)                               as units_returned,
    coalesce(r.return_count, 0)                                 as return_count,
    coalesce(r.units_returned, 0) * 100.0
        / nullif(s.units_sold, 0)                               as return_rate_pct,
    r.avg_refund_per_return,
    r.primary_return_reason,
    r.dominant_lag_segment,
    c.landed_cost,
    coalesce(r.units_returned, 0) * coalesce(c.landed_cost, 0) as estimated_return_cost

from sold s
left join returned r  on s.sku = r.sku
left join costs c     on s.sku = c.sku
order by return_rate_pct desc nulls last

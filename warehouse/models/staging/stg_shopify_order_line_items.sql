with line_items as (
    select
        *,
        -- is_synthetic DERIVED from the seed isolation predicate (order_id < 1e12).
        -- Raw is bigint here; derive before the ::text cast below.
        (order_id < 1000000000000) as is_synthetic
    from {{ source('client_azure_co', 'shopify_order_line_items') }}
)
select
    id::text          as line_item_id,
    order_id::text    as order_id,
    product_id::text  as product_id,
    variant_id::text  as variant_id,
    sku,
    title             as product_title,
    quantity,
    price             as unit_price,
    total_discount,
    price * quantity  as gross_line_revenue,
    is_synthetic
from line_items
-- RULE 3 (per-client form): synthetic rows visible only when toggle is on
where (
    is_synthetic = false
    or (select use_synthetic_data from public.client_config
        where client_id = '{{ var("client_id") }}') = true
)

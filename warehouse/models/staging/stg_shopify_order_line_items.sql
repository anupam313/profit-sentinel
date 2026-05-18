with line_items as (
    select * from {{ source('client_azure_co', 'shopify_order_line_items') }}
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
    price * quantity  as gross_line_revenue
from line_items

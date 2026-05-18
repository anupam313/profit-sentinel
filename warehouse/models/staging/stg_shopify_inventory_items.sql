-- Airbyte-managed table: no is_synthetic column (Fix 1 — omit filter).
-- cost column = Tier 2 COGS source (Shopify cost field).
-- Required for G2/G3 stockout detection and D3 margin calculations.
with inventory_items as (
    select * from {{ source('client_azure_co', 'shopify_inventory_items') }}
)
select
    id::text                    as inventory_item_id,
    sku,
    cost                        as unit_cost,
    tracked,
    currency_code,
    requires_shipping,
    country_code_of_origin,
    created_at::timestamp       as created_at,
    updated_at::timestamp       as updated_at,
    _airbyte_extracted_at
from inventory_items

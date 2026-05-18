-- Airbyte-managed table: no is_synthetic column (Fix 1 — omit filter).
-- Required for G2 (stockout risk) and G3 (overstock detection).
with inventory_levels as (
    select * from {{ source('client_azure_co', 'shopify_inventory_levels') }}
)
select
    inventory_item_id::text     as inventory_item_id,
    location_id::text           as location_id,
    available,
    available = 0               as is_out_of_stock,
    updated_at::timestamp       as updated_at,
    _airbyte_extracted_at
from inventory_levels

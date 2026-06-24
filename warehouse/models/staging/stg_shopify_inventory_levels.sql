-- Airbyte-managed table: raw has NO is_synthetic column (DEBT-006). Phase C
-- DERIVES it from the seed isolation predicate, then RULE-3 filters.
-- Required for G2 (stockout risk) and G3 (overstock detection).
with inventory_levels as (
    select
        *,
        -- Real Airbyte rows carry a 13+ digit inventory_item_id; seed rows do not.
        -- So NOT(13+ digits) == synthetic (exact replica of the seed predicate).
        (not (inventory_item_id::text ~ '^[0-9]{13,}$')) as is_synthetic
    from {{ source('client_azure_co', 'shopify_inventory_levels') }}
)
select
    inventory_item_id::text     as inventory_item_id,
    location_id::text           as location_id,
    available,
    available = 0               as is_out_of_stock,
    updated_at::timestamp       as updated_at,
    _airbyte_extracted_at,
    is_synthetic
from inventory_levels
-- RULE 3 (per-client form): synthetic rows visible only when toggle is on
where (
    is_synthetic = false
    or (select use_synthetic_data from public.client_config
        where client_id = '{{ var("client_id") }}') = true
)

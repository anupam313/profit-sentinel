-- Phase D (R11): composite uniqueness for stg_shopify_inventory_levels.
-- dbt_utils absent + RULE 4 (no surrogate cast in the model) -> native singular
-- test. Returns offending (inventory_item_id, location_id) groups; passes when
-- the result set is empty (dbt singular-test contract).
select
    inventory_item_id,
    location_id,
    count(*) as n
from {{ ref('stg_shopify_inventory_levels') }}
group by inventory_item_id, location_id
having count(*) > 1

-- Phase D (R11): composite uniqueness for stg_synthetic_touchpoint_journey.
-- dbt_utils absent + RULE 4 (no surrogate cast in the model) -> native singular
-- test. Returns offending (order_id, touchpoint_sequence) groups; passes when
-- the result set is empty (dbt singular-test contract).
select
    order_id,
    touchpoint_sequence,
    count(*) as n
from {{ ref('stg_synthetic_touchpoint_journey') }}
group by order_id, touchpoint_sequence
having count(*) > 1

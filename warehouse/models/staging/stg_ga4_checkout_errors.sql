with errors as (
    select * from {{ source('client_azure_co', 'ga4_checkout_errors') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
)
select
    date,
    hour,
    error_type,
    device_category,
    error_count,
    affected_sessions,
    affected_sessions::numeric / nullif(error_count, 0)  as sessions_per_error
from errors

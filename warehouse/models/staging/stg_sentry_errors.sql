with errors as (
    select * from {{ source('client_azure_co', 'sentry_errors_daily') }}
    where is_synthetic = {{ var('use_synthetic_data', true) }}
)
select
    date,
    hour,
    error_type,
    environment,
    release_version,
    browser,
    device_category,
    url_path,
    error_count,
    coalesce(affected_users, 0)             as affected_users,
    coalesce(p50_duration_ms, 0)            as p50_duration_ms,
    coalesce(p95_duration_ms, 0)            as p95_duration_ms,
    resolved,
    not resolved                            as is_open
from errors

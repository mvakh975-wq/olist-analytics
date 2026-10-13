select
    *,  -- noqa: AM04  (all order columns pass through)
    purchase_month between '{{ var("analysis_start") }}'::date
    and '{{ var("analysis_end") }}'::date as is_analysis_period
from {{ ref('int_orders_enriched') }}

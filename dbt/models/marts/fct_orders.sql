-- all order columns pass through, plus the analysis-period flag
select
    *,  -- noqa: AM04
    purchase_month between '{{ var("analysis_start") }}'::date
    and '{{ var("analysis_end") }}'::date as is_analysis_period
from {{ ref('int_orders_enriched') }}

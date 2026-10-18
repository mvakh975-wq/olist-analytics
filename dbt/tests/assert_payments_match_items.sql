{{ config(severity = 'warn') }}
-- payments should equal items + freight within 1 BRL;
-- the source has known mismatches (docs/data_quality.md #9), so this only warns
select
    order_id,
    gmv,
    payment_value
from {{ ref('int_orders_enriched') }}
where
    payment_value is not null
    and n_items > 0
    and abs(gmv - payment_value) > 1

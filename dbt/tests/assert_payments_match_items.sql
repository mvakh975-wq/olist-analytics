{{ config(severity = 'warn') }}
select
    order_id,
    gmv,
    payment_value
from {{ ref('int_orders_enriched') }}
where
    payment_value is not null
    and n_items > 0
    and abs(gmv - payment_value) > 1

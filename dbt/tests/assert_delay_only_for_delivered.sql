select order_id
from {{ ref('fct_orders') }}
where
    (delay_days is not null or is_late is not null)
    and (order_status <> 'delivered' or delivered_at is null)

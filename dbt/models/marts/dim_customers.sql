-- one row per person (customer_unique_id), valid orders only
select
    customer_unique_id,
    first(customer_state order by purchased_at asc) as customer_state,
    min(purchased_at) as first_order_at,
    date_trunc('month', min(purchased_at))::date as first_order_month,
    max(purchased_at) as last_order_at,
    count(*) as n_orders,
    sum(gmv) as total_gmv
from {{ ref('fct_orders') }}
where is_valid_order
group by customer_unique_id

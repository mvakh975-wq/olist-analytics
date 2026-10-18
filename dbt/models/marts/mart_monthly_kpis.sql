-- business KPIs per purchase month, valid orders only
with orders as (
    select * from {{ ref('fct_orders') }}  -- noqa: AM04
    where is_valid_order
)

select
    o.purchase_month as month,  -- noqa: RF04
    bool_and(o.is_analysis_period) as is_analysis_period,
    count(*) as orders,
    count(distinct o.customer_unique_id) as customers,
    count(distinct case
        when c.first_order_month = o.purchase_month then o.customer_unique_id
    end) as new_customers,
    sum(o.gmv) as gmv,
    sum(o.items_value) as items_value,
    sum(o.freight_value) as freight_value,
    sum(o.gmv) / count(*) as avg_order_value,
    sum(o.freight_value) / nullif(sum(o.gmv), 0) as freight_share,
    avg(o.is_late::int) as late_rate,
    avg(o.review_score) as avg_review_score
from orders as o
left join {{ ref('dim_customers') }} as c on o.customer_unique_id = c.customer_unique_id
group by o.purchase_month

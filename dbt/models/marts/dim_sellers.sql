-- orders are attributed to their main seller (most expensive item);
-- late_rate and avg_review_score ignore NULLs, so they cover delivered and reviewed orders only
with orders as (
    select
        main_seller_id as seller_id,
        count(*) as n_orders,
        sum(items_value) as items_value,
        avg(is_late::int) as late_rate,
        avg(review_score) as avg_review_score
    from {{ ref('fct_orders') }}
    where is_valid_order
    group by main_seller_id
)

select
    s.seller_id,
    s.seller_state,
    s.seller_city,
    o.late_rate,
    o.avg_review_score,
    coalesce(o.n_orders, 0) as n_orders,
    coalesce(o.items_value, 0) as items_value
from {{ ref('stg_sellers') }} as s
left join orders as o on s.seller_id = o.seller_id

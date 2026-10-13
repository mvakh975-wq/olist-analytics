-- one row per order with everything the marts need
with items as (
    select
        i.order_id,
        count(*) as n_items,
        count(distinct i.seller_id) as n_sellers,
        sum(i.price) as items_value,
        sum(i.freight_value) as freight_value,
        -- the seller and category of the most expensive item represent the order
        first(i.seller_id order by i.price desc, i.order_item_id asc) as main_seller_id,
        first(p.category order by i.price desc, i.order_item_id asc) as main_category
    from {{ ref('stg_order_items') }} as i
    left join {{ ref('stg_products') }} as p on i.product_id = p.product_id
    group by i.order_id
),

payments as (
    select
        order_id,
        sum(payment_value) as payment_value
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    -- some orders have several reviews with different scores: keep the last answered one
    select
        order_id,
        first(review_score order by review_answered_at desc) as review_score
    from {{ ref('stg_order_reviews') }}
    group by order_id
),

base as (
    select
        o.order_id,
        o.customer_id,
        c.customer_unique_id,
        c.customer_state,
        o.order_status,
        o.purchased_at,
        o.delivered_at,
        o.estimated_delivery_at,
        date_trunc('month', o.purchased_at)::date as purchase_month,
        o.order_status = 'delivered'
        and o.delivered_at is not null
        and o.delivered_at >= o.purchased_at as has_valid_delivery
    from {{ ref('stg_orders') }} as o
    inner join {{ ref('stg_customers') }} as c on o.customer_id = c.customer_id
)

select
    b.order_id,
    b.customer_id,
    b.customer_unique_id,
    b.customer_state,
    b.order_status,
    b.purchased_at,
    b.purchase_month,
    b.delivered_at,
    b.estimated_delivery_at,
    i.main_seller_id,
    i.main_category,
    p.payment_value,
    r.review_score,
    b.order_status not in ('canceled', 'unavailable')
    and coalesce(i.n_items, 0) > 0 as is_valid_order,
    case
        when b.has_valid_delivery
            then date_diff('day', b.purchased_at::date, b.delivered_at::date)
    end as delivery_days,
    case
        when b.has_valid_delivery
            then date_diff('day', b.estimated_delivery_at::date, b.delivered_at::date)
    end as delay_days,
    case
        when b.has_valid_delivery
            then b.delivered_at::date > b.estimated_delivery_at::date
    end as is_late,
    coalesce(i.n_items, 0) as n_items,
    coalesce(i.n_sellers, 0) as n_sellers,
    coalesce(i.items_value, 0) as items_value,
    coalesce(i.freight_value, 0) as freight_value,
    coalesce(i.items_value, 0) + coalesce(i.freight_value, 0) as gmv,
    r.review_score is not null as has_review
from base as b
left join items as i on b.order_id = i.order_id
left join payments as p on b.order_id = p.order_id
left join reviews as r on b.order_id = r.order_id

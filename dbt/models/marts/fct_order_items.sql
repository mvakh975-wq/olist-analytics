select
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    p.category,
    i.price,
    i.freight_value,
    o.purchased_at,
    o.purchase_month,
    o.customer_state,
    s.seller_state,
    o.is_valid_order,
    o.is_analysis_period
from {{ ref('stg_order_items') }} as i
inner join {{ ref('fct_orders') }} as o on i.order_id = o.order_id
left join {{ ref('stg_products') }} as p on i.product_id = p.product_id
left join {{ ref('stg_sellers') }} as s on i.seller_id = s.seller_id

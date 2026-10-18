select
    order_id,
    order_item_id::int as order_item_id,
    product_id,
    seller_id,
    shipping_limit_date::timestamp as shipping_limit_at,
    price::decimal(12, 2) as price,
    freight_value::decimal(12, 2) as freight_value
from {{ source('olist', 'olist_order_items_dataset') }}

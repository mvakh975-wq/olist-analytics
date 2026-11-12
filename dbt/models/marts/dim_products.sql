select
    product_id,
    category,
    category_name_pt,
    weight_g,
    photos_qty
from {{ ref('stg_products') }}

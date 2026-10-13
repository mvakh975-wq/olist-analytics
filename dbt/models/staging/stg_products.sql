-- the source's length columns (product_name_lenght, ...) are not used
select
    p.product_id,
    p.product_category_name as category_name_pt,
    coalesce(t.category_name_en, p.product_category_name, 'unknown') as category,
    p.product_weight_g::int as weight_g,
    p.product_photos_qty::int as photos_qty
from {{ source('olist', 'olist_products_dataset') }} as p
left join {{ ref('stg_category_translation') }} as t
    on p.product_category_name = t.category_name_pt

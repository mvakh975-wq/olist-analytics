select
    seller_id,
    seller_zip_code_prefix as seller_zip_prefix,
    seller_city,
    upper(seller_state) as seller_state
from {{ source('olist', 'olist_sellers_dataset') }}

select
    order_id,
    payment_sequential::int as payment_sequential,
    payment_type,
    payment_installments::int as payment_installments,
    payment_value::decimal(12, 2) as payment_value
from {{ source('olist', 'olist_order_payments_dataset') }}

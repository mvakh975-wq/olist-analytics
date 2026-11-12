select order_id
from {{ ref('int_orders_enriched') }}
where delay_days is not null and delivered_at < purchased_at

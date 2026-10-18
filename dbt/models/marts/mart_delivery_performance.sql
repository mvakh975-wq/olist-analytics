-- delivered orders with a measurable delay, bucketed, with their review score
select
    order_id,
    purchase_month,
    customer_state,
    main_seller_id,
    main_category,
    delivery_days,
    delay_days,
    is_late,
    review_score,
    is_analysis_period,
    case
        when delay_days <= 0 then 'On time or early'
        when delay_days <= 3 then '1–3 days late'
        when delay_days <= 7 then '4–7 days late'
        when delay_days <= 14 then '8–14 days late'
        else '15+ days late'
    end as delay_bucket,
    case
        when delay_days <= 0 then 1
        when delay_days <= 3 then 2
        when delay_days <= 7 then 3
        when delay_days <= 14 then 4
        else 5
    end as delay_bucket_order,
    review_score <= 2 as is_low_score
from {{ ref('fct_orders') }}
where delay_days is not null and is_valid_order

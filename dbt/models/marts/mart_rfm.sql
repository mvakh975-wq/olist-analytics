-- RFM segmentation per person. Most customers buy once, so frequency is bucketed
-- (1 / 2 / 3+ orders) instead of split into quintiles.
with ref_date as (
    select max(purchased_at)::date + 1 as as_of
    from {{ ref('fct_orders') }}
    where is_valid_order
),

base as (
    select
        c.customer_unique_id,
        c.customer_state,
        c.n_orders as frequency,
        c.total_gmv as monetary,
        date_diff('day', c.last_order_at::date, r.as_of) as recency_days
    from {{ ref('dim_customers') }} as c
    cross join ref_date as r
),

scored as (
    select
        customer_unique_id,
        customer_state,
        recency_days,
        frequency,
        monetary,
        ntile(5) over (order by recency_days desc, customer_unique_id asc) as r_score,
        least(frequency, 3) as f_score,
        ntile(5) over (order by monetary asc, customer_unique_id asc) as m_score
    from base
)

select
    customer_unique_id,
    customer_state,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    case
        when f_score >= 2 and r_score >= 4 then 'Champions'
        when f_score >= 2 then 'Loyal'
        when r_score >= 4 and m_score >= 4 then 'Promising high-value'
        when r_score >= 4 then 'Recent'
        when r_score <= 2 and m_score >= 4 then 'At risk high-value'
        else 'Hibernating'
    end as segment
from scored

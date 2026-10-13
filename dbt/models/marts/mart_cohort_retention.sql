-- monthly cohorts by first purchase; a customer is active in a month if they placed a valid order
with activity as (
    select distinct
        c.customer_unique_id,
        c.first_order_month as cohort_month,
        date_diff('month', c.first_order_month, o.purchase_month) as months_since_first
    from {{ ref('fct_orders') }} as o
    inner join {{ ref('dim_customers') }} as c on o.customer_unique_id = c.customer_unique_id
    where o.is_valid_order
),

cohorts as (
    select
        cohort_month,
        count(*) as cohort_size
    from activity
    where months_since_first = 0
    group by cohort_month
),

-- the last month with a full order volume; later months hold almost no orders
last_month as (
    select date_trunc('month', '{{ var("analysis_end") }}'::date)::date as max_month
),

-- every cohort x month offset that can be observed within the analysis period
grid as (
    select
        c.cohort_month,
        c.cohort_size,
        m.months_since_first
    from cohorts as c
    cross join range(0, 25) as m (months_since_first)
    cross join last_month as l
    where c.cohort_month + to_months(m.months_since_first::int) <= l.max_month
)

select
    g.cohort_month,
    g.months_since_first,
    g.cohort_size,
    count(a.customer_unique_id) as active_customers,
    count(a.customer_unique_id) / g.cohort_size as retention,
    g.cohort_month between '{{ var("analysis_start") }}'::date
    and '{{ var("analysis_end") }}'::date as is_analysis_period
from grid as g
left join activity as a
    on
        g.cohort_month = a.cohort_month
        and g.months_since_first = a.months_since_first
group by g.cohort_month, g.months_since_first, g.cohort_size

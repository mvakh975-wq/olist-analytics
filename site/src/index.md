---
title: Overview
sql:
  kpis: ./data/monthly_kpis.parquet
  orders_per_customer: ./data/orders_per_customer.parquet
  cohorts: ./data/cohort_retention.parquet
  effect: ./data/stats_delay_effect.parquet
  by_state: ./data/stats_delay_by_state.parquet
  states: ./data/delivery_by_state.parquet
  monthly_delivery: ./data/delivery_by_month.parquet
  buckets: ./data/delivery_by_bucket_state.parquet
  sellers: ./data/sellers_delivery.parquet
  segments: ./data/rfm_segments.parquet
---

```js
import {integer, pct, millionsBRL, brl, signed, stars, asDate} from "./components/format.js";
```

# Olist marketplace: growth, retention and delivery

<p class="lede">An analysis of ~98,000 orders on Olist, a Brazilian e-commerce marketplace, from January 2017 to August 2018: how the business grew, whether customers come back, and how delivery affects satisfaction.</p>

```sql id=yoy
select
  sum(gmv) filter (where month between '2018-01-01' and '2018-08-01') as gmv_2018,
  sum(gmv) filter (where month between '2017-01-01' and '2017-08-01') as gmv_2017,
  sum(orders) filter (where month between '2018-01-01' and '2018-08-01') as orders_2018,
  sum(orders) filter (where month between '2017-01-01' and '2017-08-01') as orders_2017,
  sum(gmv) filter (where is_analysis_period) / sum(orders) filter (where is_analysis_period) as aov,
  max(gmv) filter (where month >= '2018-01-01' and is_analysis_period) as best_2018_month,
  max(gmv) filter (where month = '2017-11-01') as black_friday_month
from kpis
```

```sql id=repeat
select sum(customers) filter (where n_orders > 1) / sum(customers) as repeat_share,
       sum(customers) as customers
from orders_per_customer
```

```sql id=month1
select sum(active_customers) / sum(cohort_size) as retention
from cohorts
where is_analysis_period and months_since_first = 1
```

```sql id=late
select sum(late_orders) / sum(orders) as late_rate from states
```

```sql id=low_scores
select
  sum(low_score_orders) filter (where delay_bucket_order = 1) / sum(reviewed) filter (where delay_bucket_order = 1) as on_time,
  sum(low_score_orders) filter (where delay_bucket_order = 3) / sum(reviewed) filter (where delay_bucket_order = 3) as late_4_7
from buckets
```

```sql id=state_range
select
  max(late_orders / orders) filter (where customer_state = 'SP') as sp,
  max(late_orders / orders) filter (where customer_state = 'RJ') as rj,
  max(late_orders / orders) filter (where customer_state = 'MA') as ma
from states
```

```sql id=spikes
select
  max(late_orders / orders) filter (where month = '2017-11-01') as nov_2017,
  max(late_orders / orders) filter (where month = '2018-03-01') as mar_2018
from monthly_delivery
```

```sql id=worst_sellers
with ranked as (select *, ntile(10) over (order by late_rate desc) as decile from sellers)
select
  count(*) filter (where decile = 1) as n_worst,
  sum(late_rate * n_orders) filter (where decile = 1) / sum(n_orders) filter (where decile = 1) as worst,
  sum(late_rate * n_orders) filter (where decile > 1) / sum(n_orders) filter (where decile > 1) as rest
from ranked
```

```sql id=high_value
select sum(customers) filter (where segment in ('Promising high-value', 'At risk high-value')) / sum(customers) as customer_share,
       sum(revenue) filter (where segment in ('Promising high-value', 'At risk high-value')) / sum(revenue) as revenue_share
from segments
```

```sql id=state_diffs
select diff from by_state
```

```sql id=effect_rows
select * from effect where comparison = 'late vs on time'
```

```js
const y = yoy.get(0);
const r = repeat.get(0);
const e = effect_rows.get(0);
const s = state_range.get(0);
const sp = spikes.get(0);
const w = worst_sellers.get(0);
const hv = high_value.get(0);
const lo = low_scores.get(0);
const stateDiffs = [...state_diffs].map((d) => d.diff);
```

<div class="grid grid-cols-4">
  <div class="card kpi">
    <h2>GMV, Jan–Aug 2018</h2>
    <div class="value">${millionsBRL(y.gmv_2018)}</div>
    <div class="kpi-note">${signed((y.gmv_2018 / y.gmv_2017 - 1) * 100, 0)}% vs Jan–Aug 2017</div>
  </div>
  <div class="card kpi">
    <h2>Average order value</h2>
    <div class="value">${brl(y.aov)}</div>
    <div class="kpi-note">flat across the period</div>
  </div>
  <div class="card kpi">
    <h2>Customers who ordered again</h2>
    <div class="value">${pct(r.repeat_share)}</div>
    <div class="kpi-note">of ${integer(r.customers)} customers</div>
  </div>
  <div class="card kpi">
    <h2>Late deliveries</h2>
    <div class="value">${pct(late.get(0).late_rate)}</div>
    <div class="kpi-note">of delivered orders</div>
  </div>
</div>

## Key findings

<div class="finding">

### 1. Growth came from new orders, and it stalled in 2018

GMV in January–August 2018 was **${millionsBRL(y.gmv_2018)}, ${(y.gmv_2018 / y.gmv_2017).toFixed(1)}× the same months of 2017**, with orders up by a similar amount while the average order value stayed near ${brl(y.aov)}. Since January 2018, no month has beaten the Black Friday month of November 2017 (${millionsBRL(y.black_friday_month)}).

<p class="recommendation">With basket size flat and acquisition levelling off, the next stage of growth has to come from customers who already bought.</p>

### 2. Almost nobody buys twice

**${pct(1 - r.repeat_share, 0)} of customers placed exactly one order.** Only ${pct(month1.get(0).retention, 2)} of a cohort orders again in the month after their first purchase. Two one-time-buyer segments with high spend are ${pct(hv.customer_share, 0)} of customers and ${pct(hv.revenue_share, 0)} of revenue.

<p class="recommendation">Run an A/B-tested second-purchase offer in the first 30 days after delivery, starting with recent high-value buyers.</p>

### 3. Late delivery goes with far worse reviews

On-time orders average **${stars(e.mean_on_time)} stars, late orders ${stars(e.mean_late)}** (difference ${signed(e.diff)}, 95% CI ${signed(e.ci_low)} to ${signed(e.ci_high)}). The share of 1–2 star reviews rises from ${pct(lo.on_time, 0)} on time to ${pct(lo.late_4_7, 0)} at 4–7 days late. The gap holds inside each of the ${stateDiffs.length} states with enough late orders to test (${signed(d3.max(stateDiffs), 1)} to ${signed(d3.min(stateDiffs), 1)} stars), so it is not explained by geography; the data is observational.

<p class="recommendation">Treat the promised delivery date as part of the product: a more conservative estimate on risky routes is cheaper than a 1-star review.</p>

### 4. Delays concentrate in time and place

Late deliveries reached ${pct(sp.nov_2017)} in November 2017 and ${pct(sp.mar_2018)} in March 2018. São Paulo, the largest market, sees ${pct(s.sp)} late, against ${pct(s.rj)} in Rio de Janeiro and ${pct(s.ma)} in Maranhão. The worst 10% of sellers with 50+ orders (${w.n_worst} sellers) are late on ${pct(w.worst)} of orders, against ${pct(w.rest)} for the rest.

<p class="recommendation">Plan carrier capacity before sales peaks, widen estimates for the North-East and Rio, and put the slowest sellers on a delivery-time plan.</p>

</div>

---

<p class="chart-note">GMV = items price + freight, in Brazilian reais (BRL). Valid orders only: not canceled or unavailable and with at least one item. See <a href="./methodology">Methodology</a> for definitions and data-quality decisions.</p>

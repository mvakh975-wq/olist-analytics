---
title: Delivery & satisfaction
sql:
  buckets: ./data/delivery_by_bucket_state.parquet
  monthly: ./data/delivery_by_month.parquet
  states: ./data/delivery_by_state.parquet
  sellers: ./data/sellers_delivery.parquet
  effect: ./data/stats_delay_effect.parquet
  by_state: ./data/stats_delay_by_state.parquet
---

```js
import {integer, pct, signed, stars, asDate} from "./components/format.js";
```

# Does delivery affect satisfaction?

<p class="lede">Delivered orders in January 2017 – August 2018. Delay = delivered date minus the delivery date promised at purchase, in days. Orders without a review are left out of the review metrics.</p>

```sql id=state_options
select customer_state from states order by orders desc
```

```js
const state = view(Inputs.select(["All states", ...[...state_options].map((d) => d.customer_state)], {label: "Customer state"}));
```

```sql id=by_bucket
select delay_bucket, delay_bucket_order,
       sum(orders) as orders,
       sum(reviewed) as reviewed,
       sum(low_score_orders) as low_score_orders,
       sum(score_sum) / sum(reviewed) as mean_score,
       sum(low_score_orders) / sum(reviewed) as low_score_share
from buckets
where ${state} = 'All states' or customer_state = ${state}
group by 1, 2
order by 2
```

```js
const bucketOrder = [...by_bucket].map((d) => d.delay_bucket);
const onTime = by_bucket.get(0);
const late4 = [...by_bucket].filter((d) => d.delay_bucket_order >= 3);
const late4Low = d3.sum(late4, (d) => d.low_score_orders) / d3.sum(late4, (d) => d.reviewed);
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>${pct(late4Low, 0)} of orders delivered 4+ days late get a 1–2 star review, against ${pct(onTime.low_score_share, 0)} on time</h2>
    <h3>${state} · by delivery date vs the promised date</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 300,
      marginBottom: 55,
      x: {domain: bucketOrder, label: null, tickRotate: width < 560 ? -30 : 0},
      y: {grid: true, label: "1–2 star reviews, % of reviewed orders", percent: true, domain: [0, 100]},
      marks: [
        Plot.barY(by_bucket, {x: "delay_bucket", y: "low_score_share", fill: (d) => (d.delay_bucket_order === 1 ? "var(--accent)" : "var(--signal)"), insetLeft: 4, insetRight: 4, tip: {format: {y: (d) => pct(d), fill: false}}, channels: {orders: {value: "orders", label: "Orders"}}}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
  <div class="card">
    <h2>Mean review score falls from ${stars(onTime.mean_score)} on time to as low as ${stars(d3.min(late4, (d) => d.mean_score))} for orders 4+ days late</h2>
    <h3>${state} · by delivery date vs the promised date</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 300,
      marginBottom: 55,
      x: {domain: bucketOrder, label: null, tickRotate: width < 560 ? -30 : 0},
      y: {grid: true, label: "Mean review score, 1–5 stars", domain: [0, 5]},
      marks: [
        Plot.barY(by_bucket, {x: "delay_bucket", y: "mean_score", fill: (d) => (d.delay_bucket_order === 1 ? "var(--accent)" : "var(--signal)"), insetLeft: 4, insetRight: 4, tip: {format: {y: (d) => stars(d), fill: false}}}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
</div>

## How large and how reliable is the effect?

Mean scores of reviewed orders, with a 95% bootstrap confidence interval for the difference, a Mann–Whitney U test (review scores are ordinal, so a rank test) and the rank-biserial correlation as effect size (−1 to 1).

```sql id=effect_rows
select * from effect order by n_late desc
```

```js
display(Inputs.table([...effect_rows].map((d) => ({
  Comparison: d.comparison,
  "On-time orders": d.n_on_time,
  "Late orders": d.n_late,
  "Mean, on time": d.mean_on_time,
  "Mean, late": d.mean_late,
  Difference: d.diff,
  "95% CI": `${signed(d.ci_low)} to ${signed(d.ci_high)}`,
  "p-value": d.mannwhitney_p,
  "Rank-biserial": d.rank_biserial
})), {
  layout: "auto",
  format: {
    "On-time orders": integer,
    "Late orders": integer,
    "Mean, on time": stars,
    "Mean, late": stars,
    Difference: (d) => signed(d),
    "p-value": (d) => (d < 0.001 ? "< 0.001" : d.toFixed(3)),
    "Rank-biserial": (d) => signed(d)
  }
}));
```

```sql id=state_diffs
select * from by_state order by diff
```

```js
const diffs = [...state_diffs];
```

<div class="card">
  <h2>The gap holds inside every state: late orders score ${(-d3.max(diffs, (d) => d.diff)).toFixed(1)} to ${(-d3.min(diffs, (d) => d.diff)).toFixed(1)} stars lower</h2>
  <h3>Mean score of late minus on-time orders, states with 300+ reviewed deliveries and 30+ late ones</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 420,
    marginLeft: 40,
    x: {grid: true, label: "Difference in mean review score, stars", domain: [-3, 0]},
    y: {domain: diffs.map((d) => d.customer_state), label: null},
    marks: [
      Plot.ruleX([0]),
      Plot.ruleY(diffs, {y: "customer_state", x1: 0, x2: "diff", stroke: "var(--context)", strokeOpacity: 0.5}),
      Plot.dot(diffs, {y: "customer_state", x: "diff", fill: "var(--signal)", r: 5, tip: {format: {x: (d) => signed(d), n: (d) => integer(d), late_share: (d) => pct(d)}}, channels: {n: {value: "n", label: "Reviewed orders"}, late_share: {value: "late_share", label: "Late share"}}})
    ]
  }))}
</div>

<p class="chart-note">This is observational data: the association is strong and consistent across states and categories, but it does not prove that delays cause the low scores.</p>

# Where does logistics fail?

```sql id=monthly_rows
select * from monthly order by month
```

```js
const monthlyRows = [...monthly_rows].map((d) => ({month: asDate(d.month), late_rate: d.late_orders / d.orders, orders: d.orders}));
```

<div class="card">
  <h2>Late deliveries spiked in Nov 2017 (Black Friday) and again in Feb–Mar 2018</h2>
  ${resize((width) => Plot.plot({
    width,
    height: 280,
    x: {type: "utc", label: "Purchase month", ticks: width < 600 ? "6 months" : "3 months", tickFormat: "%b %Y"},
    y: {grid: true, label: "Late deliveries, % of delivered orders", percent: true},
    marks: [
      Plot.ruleY([0]),
      Plot.lineY(monthlyRows, {x: "month", y: "late_rate", stroke: "var(--signal)", strokeWidth: 2}),
      Plot.dot(monthlyRows, {x: "month", y: "late_rate", fill: "var(--signal)", r: 3}),
      Plot.tip(monthlyRows, Plot.pointerX({x: "month", y: "late_rate", title: (d) => `${d3.utcFormat("%B %Y")(d.month)}\nLate: ${pct(d.late_rate)} of ${integer(d.orders)} orders`}))
    ]
  }))}
</div>

```sql id=state_rows
select * from states
```

```js
const stateRows = [...state_rows]
  .filter((d) => d.orders >= 500)
  .map((d) => ({state: d.customer_state, late_rate: d.late_orders / d.orders, orders: d.orders, avg_days: d.delivery_days_sum / d.orders}))
  .sort((a, b) => b.late_rate - a.late_rate);
const overall = d3.sum(state_rows, (d) => d.late_orders) / d3.sum(state_rows, (d) => d.orders);
```

<div class="card">
  <h2>Late deliveries are 2–4× more common in the North-East and Rio than in São Paulo</h2>
  <h3>States with 500+ delivered orders; red = above the average of ${pct(overall)}</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 460,
    marginLeft: 40,
    x: {grid: true, label: "Late deliveries, % of delivered orders", percent: true},
    y: {domain: stateRows.map((d) => d.state), label: null},
    marks: [
      Plot.barX(stateRows, {y: "state", x: "late_rate", fill: (d) => (d.late_rate > overall ? "var(--signal)" : "var(--context)"), insetTop: 2, insetBottom: 2, tip: {format: {x: (d) => pct(d), fill: false, orders: (d) => integer(d), avg_days: (d) => d.toFixed(1)}}, channels: {orders: {value: "orders", label: "Orders"}, avg_days: {value: "avg_days", label: "Avg delivery, days"}}}),
      Plot.ruleX([overall], {stroke: "currentColor", strokeDasharray: "4,3"}),
      Plot.ruleX([0])
    ]
  }))}
</div>

## Sellers

```sql id=seller_split
with ranked as (select *, ntile(10) over (order by late_rate desc) as decile from sellers)
select decile = 1 as worst_10pct,
       count(*) as sellers,
       sum(n_orders) as orders,
       sum(late_rate * n_orders) / sum(n_orders) as late_rate
from ranked
group by 1
order by 1 desc
```

```js
const worst = seller_split.get(0);
const rest = seller_split.get(1);
```

The worst 10% of sellers with 50+ orders (${worst.sellers} sellers, ${integer(worst.orders)} orders) are late on **${pct(worst.late_rate)}** of their orders, against ${pct(rest.late_rate)} for the other ${rest.sellers}. Sellers are identified by the first 8 characters of their anonymised id.

```sql id=worst_sellers
select seller, seller_state, n_orders, late_rate, avg_review_score
from sellers
order by late_rate desc
limit 15
```

```js
display(Inputs.table(worst_sellers, {
  layout: "auto",
  header: {seller: "Seller", seller_state: "State", n_orders: "Orders", late_rate: "Late", avg_review_score: "Mean score"},
  format: {n_orders: integer, late_rate: (d) => pct(d), avg_review_score: stars}
}));
```

---
title: Retention
sql:
  cohorts: ./data/cohort_retention.parquet
  orders_per_customer: ./data/orders_per_customer.parquet
---

```js
import {integer, pct, asDate} from "./components/format.js";
```

# Do customers come back?

<p class="lede">Customers are grouped into monthly cohorts by their first purchase. Retention in month N is the share of a cohort that placed another valid order N months later. A customer is a person (<code>customer_unique_id</code>), not the per-order <code>customer_id</code>.</p>

```sql id=distribution
select
  case when n_orders >= 3 then '3+ orders' else n_orders::varchar || (case when n_orders = 1 then ' order' else ' orders' end) end as bucket,
  least(n_orders, 3) as bucket_order,
  sum(customers) as customers,
  sum(customers) / (select sum(customers) from orders_per_customer) as share
from orders_per_customer
group by 1, 2
order by 2
```

```js
const once = distribution.get(0);
```

<div class="grid grid-cols-3">
  <div class="card kpi">
    <h2>Bought exactly once</h2>
    <div class="value">${pct(once.share)}</div>
    <div class="kpi-note">${integer(once.customers)} customers</div>
  </div>
  <div class="card kpi">
    <h2>Bought twice</h2>
    <div class="value">${pct(distribution.get(1).share, 2)}</div>
    <div class="kpi-note">${integer(distribution.get(1).customers)} customers</div>
  </div>
  <div class="card kpi">
    <h2>Bought 3+ times</h2>
    <div class="value">${pct(distribution.get(2).share, 2)}</div>
    <div class="kpi-note">${integer(distribution.get(2).customers)} customers</div>
  </div>
</div>

```sql id=curve
select months_since_first,
       sum(active_customers) / sum(cohort_size) as retention,
       sum(cohort_size) as customers_observed
from cohorts
where is_analysis_period and months_since_first between 1 and 12
group by 1
order by 1
```

<div class="card">
  <h2>Only ${pct(curve.get(0).retention, 2)} of customers order again in the month after their first purchase</h2>
  <h3>All cohorts from Jan 2017, weighted by size; later months include fewer cohorts</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 280,
    x: {label: "Months since first purchase", ticks: 12, tickFormat: "d"},
    y: {grid: true, label: "Customers placing an order, % of cohort", percent: true, domain: [0, 0.6]},
    marks: [
      Plot.ruleY([0]),
      Plot.lineY(curve, {x: "months_since_first", y: "retention", stroke: "var(--accent)", strokeWidth: 2}),
      Plot.dot(curve, {x: "months_since_first", y: "retention", fill: "var(--accent)", r: 3.5, tip: {format: {y: (d) => pct(d, 2), customers_observed: (d) => integer(d)}}, channels: {customers_observed: {value: "customers_observed", label: "Customers observed"}}})
    ]
  }))}
</div>

```sql id=grid
select strftime(cohort_month, '%b %Y') as cohort, cohort_month, months_since_first, retention, cohort_size, active_customers
from cohorts
where is_analysis_period and months_since_first between 1 and 12
```

```js
const cohortOrder = [...new Map([...grid].map((d) => [d.cohort, +asDate(d.cohort_month)])).entries()].sort((a, b) => a[1] - b[1]).map((d) => d[0]);
```

<div class="card">
  <h2>No cohort goes above ${pct(d3.max(grid, (d) => d.retention), 2)} in any month</h2>
  <h3>Share of each cohort placing an order N months after the first purchase</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 520,
    marginLeft: 70,
    padding: 0.06,
    x: {label: "Months since first purchase", tickFormat: "d"},
    y: {label: "Cohort (first purchase)", domain: cohortOrder},
    color: {type: "linear", scheme: "blues", domain: [0, 0.008], legend: true, label: "Customers placing an order, % of cohort", tickFormat: (d) => `${(d * 100).toFixed(1)}%`},
    marks: [
      Plot.cell(grid, {x: "months_since_first", y: "cohort", fill: "retention", inset: 0.5, tip: {format: {fill: (d) => pct(d, 2), cohort_size: (d) => integer(d), active_customers: (d) => integer(d)}}, channels: {cohort_size: {value: "cohort_size", label: "Cohort size"}, active_customers: {value: "active_customers", label: "Ordered"}}})
    ]
  }))}
</div>

## Why `customer_unique_id`

Olist creates a new `customer_id` for every order, so grouping by it makes every customer look new and retention exactly zero. The models use `customer_unique_id`, which identifies the person. The ${integer(d3.sum(distribution, (d) => d.customers))} people in this data hold slightly more ids than that, one per order, and that small difference is the whole signal: every repeat purchase is invisible at the `customer_id` level.

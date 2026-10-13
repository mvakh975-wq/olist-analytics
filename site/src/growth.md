---
title: Growth
sql:
  kpis: ./data/monthly_kpis.parquet
  gmv: ./data/gmv_by_month_category_state.parquet
---

```js
import {integer, pct, millionsBRL, brl, asDate} from "./components/format.js";
```

# Is the business growing?

<p class="lede">Monthly GMV (items + freight, BRL) over the analysis period, January 2017 – August 2018. Filter by customer state and product category.</p>

```sql id=state_options
select distinct customer_state from gmv where customer_state is not null order by 1
```

```sql id=category_options
select category from gmv where is_analysis_period group by 1 order by sum(gmv) desc
```

```js
const state = view(Inputs.select(["All states", ...[...state_options].map((d) => d.customer_state)], {label: "Customer state"}));
const category = view(Inputs.select(["All categories", ...[...category_options].map((d) => d.category)], {label: "Category"}));
```

```sql id=monthly
select month, sum(gmv) as gmv
from gmv
where is_analysis_period
  and (${state} = 'All states' or customer_state = ${state})
  and (${category} = 'All categories' or category = ${category})
group by month
order by month
```

```sql id=yoy
select
  sum(gmv) filter (where month between '2017-01-01' and '2017-08-01') as gmv_2017,
  sum(gmv) filter (where month between '2018-01-01' and '2018-08-01') as gmv_2018
from gmv
where (${state} = 'All states' or customer_state = ${state})
  and (${category} = 'All categories' or category = ${category})
```

```js
const g = yoy.get(0);
const growth = g.gmv_2017 > 0 ? g.gmv_2018 / g.gmv_2017 - 1 : null;
```

<div class="card">
  <h2>${growth === null ? "Monthly GMV" : `GMV ${growth >= 0 ? "grew" : "fell"} ${pct(Math.abs(growth), 0)} year over year (Jan–Aug 2018 vs Jan–Aug 2017)`}</h2>
  <h3>${state}, ${category} · ${millionsBRL(g.gmv_2018 ?? 0)} in Jan–Aug 2018</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 300,
    marginLeft: 60,
    x: {type: "utc", label: "Purchase month", ticks: width < 600 ? "6 months" : "3 months", tickFormat: "%b %Y"},
    y: {grid: true, label: "GMV, thousand BRL", tickFormat: (d) => (d / 1e3).toLocaleString("en-US")},
    marks: [
      Plot.ruleY([0]),
      Plot.lineY(monthly, {x: (d) => asDate(d.month), y: "gmv", stroke: "var(--accent)", strokeWidth: 2}),
      Plot.dot(monthly, {x: (d) => asDate(d.month), y: "gmv", fill: "var(--accent)", r: 3}),
      Plot.tip(monthly, Plot.pointerX({x: (d) => asDate(d.month), y: "gmv", title: (d) => `${d3.utcFormat("%B %Y")(asDate(d.month))}\nGMV: ${brl(d.gmv)}`}))
    ]
  }))}
</div>

## Which categories drove the growth?

```sql id=categories
select
  category,
  coalesce(sum(gmv) filter (where month between '2018-01-01' and '2018-08-01'), 0)
    - coalesce(sum(gmv) filter (where month between '2017-01-01' and '2017-08-01'), 0) as gmv_change
from gmv
where (${state} = 'All states' or customer_state = ${state})
group by category
order by gmv_change desc
limit 10
```

<div class="card">
  <h2>Top 10 categories by GMV added, Jan–Aug 2018 vs Jan–Aug 2017</h2>
  <h3>${state}</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 320,
    marginLeft: 170,
    x: {grid: true, label: "GMV added, thousand BRL", tickFormat: (d) => (d / 1e3).toLocaleString("en-US")},
    y: {label: null},
    marks: [
      Plot.barX(categories, {y: "category", x: "gmv_change", fill: "var(--accent)", sort: {y: "-x"}, insetTop: 3, insetBottom: 3, tip: {format: {x: (d) => brl(d)}}}),
      Plot.ruleX([0])
    ]
  }))}
</div>

## Order value and freight

<p class="chart-note">These two charts cover all states and categories.</p>

```sql id=kpiRows
select month, avg_order_value, freight_share from kpis where is_analysis_period order by month
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Average order value stayed flat at ~160 BRL</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 240,
      x: {type: "utc", label: "Purchase month", tickFormat: "%b %y"},
      y: {grid: true, label: "Average order value, BRL", domain: [0, 200]},
      marks: [
        Plot.lineY(kpiRows, {x: (d) => asDate(d.month), y: "avg_order_value", stroke: "var(--accent)", strokeWidth: 2, tip: {format: {y: (d) => brl(d)}}}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
  <div class="card">
    <h2>Freight takes a slightly larger share of GMV</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 240,
      x: {type: "utc", label: "Purchase month", tickFormat: "%b %y"},
      y: {grid: true, label: "Freight share of GMV, %", percent: true, domain: [0, 20]},
      marks: [
        Plot.lineY(kpiRows, {x: (d) => asDate(d.month), y: "freight_share", stroke: "var(--context)", strokeWidth: 2, tip: true}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
</div>

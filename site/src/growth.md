---
title: Growth
---

```js
import {pct, millionsBRL, brl} from "./components/format.js";

// ~85 kB of pre-aggregated rows (scripts/export_marts.py): filtering them here is instant,
// so this page does not need to load the in-browser database
const parseMonth = d3.utcParse("%Y-%m");
const gmv = (await FileAttachment("data/growth_gmv.csv").csv()).map((d) => ({...d, gmv: +d.gmv}));
const kpis = (await FileAttachment("data/growth_kpis.csv").csv()).map((d) => ({
  month: d.month,
  avg_order_value: +d.avg_order_value,
  freight_share: +d.freight_share
}));
const amount = (value) => (value >= 1e6 ? millionsBRL(value) : brl(value));
const inYear = (year) => (d) => d.month >= `${year}-01` && d.month <= `${year}-08`;
```

# Is the business growing?

<p class="lede">Monthly GMV (items + freight, BRL) over the analysis period, January 2017 – August 2018. Filter by period, customer state and product category.</p>

```js
const months = kpis.map((d) => d.month);
const monthLabel = (m) => d3.utcFormat("%b %Y")(parseMonth(m));
const from = view(Inputs.select(months, {label: "From", format: monthLabel, value: months[0]}));
const to = view(Inputs.select(months, {label: "To", format: monthLabel, value: months.at(-1)}));
```

```js
// a reversed range is read as the same range the right way round
const [start, end] = from <= to ? [from, to] : [to, from];
```

```js
const states = [...new Set(gmv.map((d) => d.state))].sort();
const categories = d3.groupSort(gmv, (rows) => -d3.sum(rows, (d) => d.gmv), (d) => d.category);
const state = view(Inputs.select(["All states", ...states], {label: "Customer state"}));
const category = view(Inputs.select(["All categories", ...categories], {label: "Category"}));
```

```js
const byState = state === "All states" ? gmv : gmv.filter((d) => d.state === state);
const selected = category === "All categories" ? byState : byState.filter((d) => d.category === category);
const totals = d3.rollup(selected, (rows) => d3.sum(rows, (d) => d.gmv), (d) => d.month);
// every month of the period, so months without sales show as 0 instead of being skipped
const monthly = months
  .filter((m) => m >= start && m <= end)
  .map((m) => ({month: parseMonth(m), gmv: totals.get(m) ?? 0}));
const gmv2017 = d3.sum(selected.filter(inYear(2017)), (d) => d.gmv);
const gmv2018 = d3.sum(selected.filter(inYear(2018)), (d) => d.gmv);
const growth = gmv2017 > 0 ? gmv2018 / gmv2017 - 1 : null;
```

<div class="card">
  <h2>${growth === null ? "Monthly GMV" : `GMV ${growth >= 0 ? "grew" : "fell"} ${pct(Math.abs(growth), 0)} year over year (Jan–Aug 2018 vs Jan–Aug 2017)`}</h2>
  <h3>${state}, ${category} · ${amount(gmv2018)} in Jan–Aug 2018</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 300,
    marginLeft: 60,
    marginRight: 30,
    x: {type: "utc", label: "Purchase month", ticks: width < 600 ? "6 months" : "3 months", tickFormat: "%b %Y"},
    y: {grid: true, label: "GMV, thousand BRL", tickFormat: (d) => (d / 1e3).toLocaleString("en-US")},
    marks: [
      Plot.ruleY([0]),
      Plot.lineY(monthly, {x: "month", y: "gmv", stroke: "var(--accent)", strokeWidth: 2}),
      Plot.dot(monthly, {x: "month", y: "gmv", fill: "var(--accent)", r: 3}),
      Plot.tip(monthly, Plot.pointerX({x: "month", y: "gmv", title: (d) => `${d3.utcFormat("%B %Y")(d.month)}\nGMV: ${brl(d.gmv)}`}))
    ]
  }))}
</div>

## Which categories drove the growth?

```js
const change = d3.rollups(
  byState,
  (rows) => d3.sum(rows.filter(inYear(2018)), (d) => d.gmv) - d3.sum(rows.filter(inYear(2017)), (d) => d.gmv),
  (d) => d.category
);
const topCategories = change
  .map(([category, gmv_change]) => ({category, gmv_change}))
  .sort((a, b) => b.gmv_change - a.gmv_change)
  .slice(0, 10);
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
      Plot.barX(topCategories, {y: "category", x: "gmv_change", fill: "var(--accent)", sort: {y: "-x"}, insetTop: 3, insetBottom: 3, tip: {format: {x: (d) => brl(d)}}}),
      Plot.ruleX([0])
    ]
  }))}
</div>

## Order value and freight

<p class="chart-note">These two charts follow the period filter and cover all states and categories.</p>

```js
const kpiRows = kpis.filter((d) => d.month >= start && d.month <= end).map((d) => ({...d, month: parseMonth(d.month)}));
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Average order value stayed flat at ~160 BRL</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 240,
      marginRight: 24,
      x: {type: "utc", label: "Purchase month", tickFormat: "%b %y"},
      y: {grid: true, label: "Average order value, BRL", domain: [0, 200]},
      marks: [
        Plot.lineY(kpiRows, {x: "month", y: "avg_order_value", stroke: "var(--accent)", strokeWidth: 2, tip: {format: {y: (d) => brl(d)}}}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
  <div class="card">
    <h2>Freight takes a slightly larger share of GMV</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 240,
      marginRight: 24,
      x: {type: "utc", label: "Purchase month", tickFormat: "%b %y"},
      y: {grid: true, label: "Freight share of GMV, %", percent: true, domain: [0, 20]},
      marks: [
        Plot.lineY(kpiRows, {x: "month", y: "freight_share", stroke: "var(--context)", strokeWidth: 2, tip: true}),
        Plot.ruleY([0])
      ]
    }))}
  </div>
</div>

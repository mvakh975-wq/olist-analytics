---
title: Customers
sql:
  segments: ./data/rfm_segments.parquet
---

```js
import {integer, pct, brl} from "./components/format.js";
```

# Who are our customers?

<p class="lede">RFM segmentation per person. Recency and monetary value are split into quintiles (5 = best). Frequency is 1, 2 or 3+ orders, because almost every customer bought once and frequency quintiles would put everyone in the same bucket.</p>

```sql id=seg
select segment,
       customers,
       customers / sum(customers) over () as share_of_customers,
       revenue / sum(revenue) over () as share_of_revenue,
       revenue / customers as revenue_per_customer,
       median_recency_days
from segments
order by share_of_revenue desc
```

```js
const order = [...seg].map((d) => d.segment);
const long = [...seg].flatMap((d) => [
  {segment: d.segment, measure: "Share of customers", value: d.share_of_customers},
  {segment: d.segment, measure: "Share of revenue", value: d.share_of_revenue}
]);
const highValue = [...seg].filter((d) => d.segment.endsWith("high-value"));
```

<div class="card">
  <h2>Two high-value one-time-buyer segments are ${pct(d3.sum(highValue, (d) => d.share_of_customers), 0)} of customers and ${pct(d3.sum(highValue, (d) => d.share_of_revenue), 0)} of revenue</h2>
  <h3>Share of all customers and of all revenue, by segment</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 340,
    marginLeft: 150,
    x: {grid: true, label: "% of total", percent: true},
    fy: {domain: order, label: null, axis: "left"},
    y: {axis: null, domain: ["Share of customers", "Share of revenue"]},
    color: {domain: ["Share of customers", "Share of revenue"], range: ["var(--context)", "var(--accent)"], legend: true},
    marks: [
      Plot.barX(long, {fy: "segment", y: "measure", x: "value", fill: "measure", insetTop: 1, insetBottom: 1, tip: {format: {x: (d) => pct(d), fy: true, y: true}}}),
      Plot.ruleX([0])
    ]
  }))}
</div>

## What to do with each segment

```js
const actions = new Map([
  ["Champions", ["2+ orders, ordered recently", "Early access to sales and a referral programme"]],
  ["Loyal", ["2+ orders, not recently", "Personalised win-back with category recommendations"]],
  ["Promising high-value", ["1 order, recent, top-40% spend", "Second-purchase offer within 30 days of delivery"]],
  ["Recent", ["1 order, recent, lower spend", "Onboarding emails and low-cost add-ons"]],
  ["At risk high-value", ["1 order, not recent (bottom 60% by recency), top-40% spend", "Win-back campaign; check whether the delivery went wrong"]],
  ["Hibernating", ["Everyone else", "Low-cost reactivation only"]]
]);
const rows = [...seg].map((d) => ({
  Segment: d.segment,
  Action: actions.get(d.segment)[1],
  Rule: actions.get(d.segment)[0],
  Customers: d.customers,
  "% of customers": d.share_of_customers,
  "% of revenue": d.share_of_revenue,
  "Revenue per customer": d.revenue_per_customer,
  "Median days since last order": d.median_recency_days
}));
```

```js
display(Inputs.table(rows, {
  rows: 7,
  layout: "auto",
  format: {
    Customers: integer,
    "% of customers": (d) => pct(d),
    "% of revenue": (d) => pct(d),
    "Revenue per customer": brl,
    "Median days since last order": (d) => integer(d)
  }
}));
```

<p class="chart-note">Revenue = GMV of a customer's valid orders over the whole dataset. Recency is measured from the day after the last order in the data.</p>

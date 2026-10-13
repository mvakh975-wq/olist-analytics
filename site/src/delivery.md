---
title: Delivery & satisfaction
---

```js
import {integer, pct, signed, stars, asDate} from "./components/format.js";

// small aggregates computed when the site is built (scripts/export_marts.py)
const buckets = await FileAttachment("data/delivery_by_bucket_state.json").json();
const monthly = await FileAttachment("data/delivery_by_month.json").json();
const states = await FileAttachment("data/delivery_by_state.json").json();
const sellers = await FileAttachment("data/sellers_delivery.json").json();
const effect = await FileAttachment("data/stats_delay_effect.json").json();
const byState = await FileAttachment("data/stats_delay_by_state.json").json();
// like SQL: a ratio over nothing is "no value", not NaN
const ratio = (a, b) => (b ? a / b : null);
```

# Does delivery affect satisfaction?

<p class="lede">Delivered orders in January 2017 – August 2018. Delay = delivered date minus the delivery date promised at purchase, in days. Orders without a review are left out of the review metrics.</p>

```js
const state_options = d3.sort(states, (d) => -d.orders);
```

```js
const state = view(Inputs.select(["All states", ...[...state_options].map((d) => d.customer_state)], {label: "Customer state"}));
```

```js
const by_bucket = d3
  .rollups(
    state === "All states" ? buckets : buckets.filter((d) => d.customer_state === state),
    (rows) => {
      const sum = (key) => d3.sum(rows, (d) => d[key]);
      return {
        delay_bucket: rows[0].delay_bucket,
        delay_bucket_order: rows[0].delay_bucket_order,
        orders: sum("orders"),
        reviewed: sum("reviewed"),
        low_score_orders: sum("low_score_orders"),
        mean_score: ratio(sum("score_sum"), sum("reviewed")),
        low_score_share: ratio(sum("low_score_orders"), sum("reviewed"))
      };
    },
    (d) => d.delay_bucket_order
  )
  .map(([, v]) => v)
  .sort((a, b) => a.delay_bucket_order - b.delay_bucket_order);
```

```js
// fixed order so an empty bucket stays visible as a gap instead of disappearing
const bucketOrder = ["On time or early", "1–3 days late", "4–7 days late", "8–14 days late", "15+ days late"];
const onTime = by_bucket[0];
const late4 = [...by_bucket].filter((d) => d.delay_bucket_order >= 3);
const late4Reviewed = d3.sum(late4, (d) => d.reviewed);
const late4Low = d3.sum(late4, (d) => d.low_score_orders) / late4Reviewed;
// below this many reviewed late orders a headline percentage would be noise
const enoughLate = late4Reviewed >= 30;
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>${enoughLate ? `${pct(late4Low, 0)} of orders delivered 4+ days late get a 1–2 star review, against ${pct(onTime.low_score_share, 0)} on time` : `1–2 star reviews by delivery delay (only ${late4Reviewed} reviewed ${late4Reviewed === 1 ? "order" : "orders"} 4+ days late here)`}</h2>
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
    <h2>${enoughLate ? `Mean review score falls from ${stars(onTime.mean_score)} on time to as low as ${stars(d3.min(late4, (d) => d.mean_score))} for orders 4+ days late` : "Mean review score by delivery delay"}</h2>
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

```js
const effect_rows = d3.sort(effect, (d) => -d.n_late);
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

```js
const state_diffs = d3.sort(byState, (d) => d.diff);
```

```js
const diffs = [...state_diffs];
```

<div class="card">
  <h2>The gap holds inside each of the ${diffs.length} states tested: late orders score ${(-d3.max(diffs, (d) => d.diff)).toFixed(1)} to ${(-d3.min(diffs, (d) => d.diff)).toFixed(1)} stars lower</h2>
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

```js
const monthly_rows = d3.sort(monthly, (d) => d.month);
```

```js
const monthlyRows = [...monthly_rows].map((d) => ({month: asDate(d.month), late_rate: d.late_orders / d.orders, orders: d.orders}));
```

<div class="card">
  <h2>Late deliveries spiked in Nov 2017 (Black Friday) and again in Feb–Mar 2018</h2>
  ${resize((width) => Plot.plot({
    width,
    height: 280,
    marginRight: 30,
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

```js
const state_rows = states;
```

```js
const stateRows = [...state_rows]
  .filter((d) => d.orders >= 500)
  .map((d) => ({state: d.customer_state, late_rate: d.late_orders / d.orders, orders: d.orders, avg_days: d.delivery_days_sum / d.orders, avg_days_late: d.late_delay_days_sum / d.late_orders}))
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
      Plot.barX(stateRows, {y: "state", x: "late_rate", fill: (d) => (d.late_rate > overall ? "var(--signal)" : "var(--context)"), insetTop: 2, insetBottom: 2, tip: {format: {x: (d) => pct(d), fill: false, orders: (d) => integer(d), avg_days: (d) => d.toFixed(1), avg_days_late: (d) => d.toFixed(1)}}, channels: {orders: {value: "orders", label: "Orders"}, avg_days: {value: "avg_days", label: "Avg delivery, days"}, avg_days_late: {value: "avg_days_late", label: "Avg delay when late, days"}}}),
      Plot.ruleX([overall], {stroke: "currentColor", strokeDasharray: "4,3"}),
      Plot.ruleX([0])
    ]
  }))}
</div>

## Sellers

```js
// sellers with 50+ delivered orders in the analysis period, worst late rate first, split into
// deciles the way SQL's ntile(10) does (the first n % 10 groups get one extra seller)
const ranked = d3.sort(sellers, (a, b) => b.late_rate - a.late_rate || d3.ascending(a.seller, b.seller));
const ntile = (i, n, k) => {
  const size = Math.floor(n / k), extra = n % k;
  return i < extra * (size + 1) ? Math.floor(i / (size + 1)) + 1 : extra + Math.floor((i - extra * (size + 1)) / size) + 1;
};
const allLate = d3.sum(states, (d) => d.late_orders);
const seller_split = [true, false].map((worst) => {
  const group = ranked.filter((d, i) => (ntile(i, ranked.length, 10) === 1) === worst);
  const late = d3.sum(group, (d) => d.late_orders);
  const delivered = d3.sum(group, (d) => d.delivered_orders);
  return {worst_10pct: worst, sellers: group.length, orders: delivered, late_rate: late / delivered, share_of_all_late: late / allLate};
});
```

```js
const worst = seller_split[0];
const rest = seller_split[1];
```

The worst 10% of sellers with 50+ delivered orders (${worst.sellers} sellers, ${integer(worst.orders)} orders) are late on **${pct(worst.late_rate)}** of their orders, against ${pct(rest.late_rate)} for the other ${rest.sellers}. Still, they cause only ${pct(worst.share_of_all_late, 0)} of all late deliveries: most delays are spread across the network. Sellers are identified by the first 8 characters of their anonymised id.

```js
const worst_sellers = ranked.slice(0, 15).map(({seller, seller_state, delivered_orders, late_rate, avg_days_late, avg_review_score}) => ({seller, seller_state, delivered_orders, late_rate, avg_days_late, avg_review_score}));
```

```js
display(Inputs.table(worst_sellers, {
  layout: "auto",
  header: {seller: "Seller", seller_state: "State", delivered_orders: "Delivered orders", late_rate: "Late", avg_days_late: "Avg delay when late, days", avg_review_score: "Mean score"},
  format: {delivered_orders: integer, late_rate: (d) => pct(d), avg_days_late: (d) => (d == null ? "–" : d.toFixed(1)), avg_review_score: stars}
}));
```

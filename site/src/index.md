---
title: Overview
---

```js
import {integer, pct, millionsBRL, brl, signed, stars} from "./components/format.js";

// every number on this page is computed at build time from the marts (scripts/export_marts.py),
// so the overview opens without loading the in-browser database
const o = await FileAttachment("data/overview.json").json();
const change = (now, before) => `${signed((now / before - 1) * 100, 0)}%`;
```

# Olist marketplace: growth, retention and delivery

<p class="lede">An analysis of ~98,000 orders on Olist, a Brazilian e-commerce marketplace, from January 2017 to August 2018: how the business grew, whether customers come back, and how delivery affects satisfaction.</p>

<div class="grid grid-cols-4">
  <div class="card kpi">
    <h2>GMV, Jan–Aug 2018</h2>
    <div class="value">${millionsBRL(o.gmv_2018)}</div>
    <div class="kpi-note">${change(o.gmv_2018, o.gmv_2017)} vs Jan–Aug 2017</div>
  </div>
  <div class="card kpi">
    <h2>Average order value, Jan–Aug 2018</h2>
    <div class="value">${brl(o.aov_2018)}</div>
    <div class="kpi-note">${change(o.aov_2018, o.aov_2017)} vs Jan–Aug 2017 (${brl(o.aov_2017)})</div>
  </div>
  <div class="card kpi">
    <h2>Customers who ordered again</h2>
    <div class="value">${pct(o.repeat_share)}</div>
    <div class="kpi-note">of ${integer(o.customers)} customers</div>
  </div>
  <div class="card kpi">
    <h2>Late deliveries, Jan–Aug 2018</h2>
    <div class="value">${pct(o.late_rate_2018)}</div>
    <div class="kpi-note">vs ${pct(o.late_rate_2017)} in Jan–Aug 2017</div>
  </div>
</div>

## Key findings

<div class="finding">

### 1. Growth came from new orders, and it stalled in 2018

GMV in January–August 2018 was **${millionsBRL(o.gmv_2018)}, ${(o.gmv_2018 / o.gmv_2017).toFixed(1)}× the same months of 2017**, with orders up ${change(o.orders_2018, o.orders_2017)} while the average order value barely moved (${brl(o.aov_2017)} → ${brl(o.aov_2018)}). Since January 2018, no month has beaten the Black Friday month of November 2017 (${millionsBRL(o.black_friday_gmv)}).

<p class="recommendation">With basket size flat and acquisition levelling off, the next stage of growth has to come from customers who already bought.</p>

### 2. Almost nobody buys twice

**${pct(1 - o.repeat_share, 0)} of customers placed exactly one order.** Only ${pct(o.month1_retention, 2)} of a cohort orders again in the month after their first purchase. Two one-time-buyer segments with high spend are ${pct(o.high_value_customer_share, 0)} of customers and ${pct(o.high_value_revenue_share, 0)} of revenue.

<p class="recommendation">Run an A/B-tested second-purchase offer in the first 30 days after delivery, starting with recent high-value buyers.</p>

### 3. Late delivery goes with far worse reviews

On-time orders average **${stars(o.effect.mean_on_time)} stars, late orders ${stars(o.effect.mean_late)}** (difference ${signed(o.effect.diff)}, 95% CI ${signed(o.effect.ci_low)} to ${signed(o.effect.ci_high)}). The share of 1–2 star reviews rises from ${pct(o.low_score_on_time, 0)} on time to ${pct(o.low_score_late_4_7, 0)} at 4–7 days late. The gap holds inside each of the ${o.states_tested} states with enough late orders to test (${signed(o.state_gap_min, 1)} to ${signed(o.state_gap_max, 1)} stars), so it is not explained by geography; the data is observational.

<p class="recommendation">Treat the promised delivery date as part of the product: a more conservative estimate on risky routes is cheaper than a 1-star review.</p>

### 4. Delays concentrate in time and place

Late deliveries reached ${pct(o.late_nov_2017)} in November 2017 and ${pct(o.late_mar_2018)} in March 2018. São Paulo, the largest market, sees ${pct(o.late_sp)} late, against ${pct(o.late_rj)} in Rio de Janeiro and ${pct(o.late_ma)} in Maranhão. The worst 10% of sellers with 50+ delivered orders (${o.worst_sellers} sellers) are late on ${pct(o.worst_sellers_late)} of orders, against ${pct(o.other_sellers_late)} for the rest, but they cause only ${pct(o.worst_sellers_share_of_late, 0)} of all late deliveries.

<p class="recommendation">Plan carrier capacity before sales peaks, widen estimates for the North-East and Rio, and put the slowest sellers on a delivery-time plan.</p>

</div>

---

<p class="chart-note">GMV = items price + freight, in Brazilian reais (BRL). Valid orders only: not canceled or unavailable and with at least one item. See <a href="./methodology">Methodology</a> for definitions and data-quality decisions.</p>

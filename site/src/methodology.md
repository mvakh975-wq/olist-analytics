---
title: Methodology
---

# Methodology

## Data

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle: 99,441 orders placed between September 2016 and October 2018, with items, payments, reviews, customers, sellers and products. Licensed CC BY-NC-SA 4.0 (© Olist); the aggregates behind this site are shared under the same license.

**Analysis period: January 2017 – August 2018**, the 20 full months with a steady order volume. September–December 2016 and September–October 2018 hold only a few hundred orders between them and stay out of trends and comparisons.

## Pipeline

1. Raw CSV files are loaded into DuckDB by **dbt**, in three layers: *staging* (types, names, translations), *intermediate* (one row per order) and *marts* (facts, dimensions and one table per business question).
2. **53 dbt tests** check keys, relationships, accepted values and business rules on every build. In CI they run on a sample of real rows chosen to contain every edge case found during profiling.
3. Python notebooks do the statistics (bootstrap confidence intervals, Mann–Whitney U, checks inside states and categories).
4. This site is built with **Observable Framework**; every number in its charts and findings comes from a SQL query over aggregates of the marts, run in the browser with DuckDB.

Code, SQL models and notebooks: [github.com/mvakh975-wq/olist-analytics](https://github.com/mvakh975-wq/olist-analytics).

## Definitions

| Metric | Definition |
|---|---|
| Valid order | Status is not `canceled` or `unavailable`, and the order has at least one item |
| GMV | Items price + freight, BRL. Payments are not used for revenue (they differ from items + freight on 249 orders) |
| Customer | A person, `customer_unique_id`. Olist's `customer_id` is created per order |
| Retention, month N | Share of a first-purchase cohort that placed a valid order N months after the first one |
| Delay | Delivered date − promised (estimated) date, in days. Only for orders with status `delivered` and a delivery date |
| Late | Delay > 0 days |
| Review score | One per order: the last answered review. Orders without a review are left out of score metrics, never counted as 0 |
| RFM | Recency and monetary value in quintiles (5 = best); frequency as 1, 2 or 3+ orders |

## Data quality decisions

| Issue | Scale | Decision |
|---|---|---|
| `customer_id` is unique per order | 99,441 ids vs 96,096 people | Customers are `customer_unique_id` everywhere |
| Orders with several reviews | 547 orders, scores differ in 202 | Keep the last answered review |
| Orders without a review | 768 | Score is empty, not 0 |
| Orders without items | 775, mostly unavailable or canceled | Not a valid sale |
| Delivered without a delivery date | 8 | No delay is computed; not counted as on time |
| Payments ≠ items + freight | 249 orders, 3,262 BRL in total | GMV from items; flagged by a warning test |
| Products without a category | 610 of 32,951 | Category `unknown` |
| Sparse months at the edges | 2016 and Sep–Oct 2018 | Outside the analysis period |

The full list, with the profiling notebook, is in [`docs/data_quality.md`](https://github.com/mvakh975-wq/olist-analytics/blob/main/docs/data_quality.md).

## Limitations

- **Observational data.** The link between late delivery and low scores is strong and holds within states and categories, but it is an association, not a measured causal effect. An experiment (for example, more conservative delivery estimates on some routes) would be needed to size the effect of an intervention.
- **Review coverage.** Customers who leave a review may differ from those who don't.
- **Recent orders.** Orders placed close to the end of the data are only included in delivery metrics once delivered, which can make the last months look slightly better than they were.
- **No marketing, traffic or cost data.** Growth is described from orders only; acquisition channels and margins are out of scope.

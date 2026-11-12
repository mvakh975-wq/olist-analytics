# Data quality

Findings from [`notebooks/00_data_profiling.ipynb`](../notebooks/00_data_profiling.ipynb) on the raw
Olist files (99,441 orders, purchases from 2016-09-04 to 2018-10-17), and what the models do about
each one.

| # | Issue | Scale | Decision | Implemented in |
|---|-------|-------|----------|----------------|
| 1 | `customer_id` is unique per order, not per person | 99,441 `customer_id` vs 96,096 `customer_unique_id`; 2,997 people placed more than one order | A customer is `customer_unique_id` everywhere (retention, RFM, new vs returning) | `int_orders_enriched`, `dim_customers` |
| 2 | Orders with several reviews | 547 orders have 2+ reviews; in 202 of them the scores differ | One score per order: the review answered last (`review_answer_timestamp`) | `int_orders_enriched` |
| 3 | One review attached to several orders | 814 repeated `review_id` values; the pair (`review_id`, `order_id`) is unique and the score never differs within a `review_id` | Keep the pair as the review key; the review counts once per order it belongs to | `stg_order_reviews` |
| 4 | Orders without a review | 768 orders | Score is `NULL`, never 0; such orders are left out of satisfaction metrics | `int_orders_enriched` |
| 5 | Orders without items | 775 orders (603 unavailable, 164 canceled, 8 in other statuses) | Not a valid sale: a valid order is not `canceled`/`unavailable` **and** has at least one item | `int_orders_enriched.is_valid_order` |
| 6 | Delivered orders without a delivery date | 8 orders | Delay metrics are `NULL` for them; they are not counted as on time | `int_orders_enriched` |
| 7 | Delivery date on non-delivered orders | 6 orders | Delay metrics only for status `delivered` | `int_orders_enriched` |
| 8 | Delivery recorded before purchase | 0 orders | Guarded anyway by a dbt test | `assert_delivered_not_before_purchase` |
| 9 | Payments differ from items + freight | 249 of 98,665 orders differ by more than 1 BRL (3,262 BRL in total); 1 order has no payment record | Revenue (GMV) is computed from items + freight, payments are not used for revenue; dbt test warns on the mismatch | `assert_payments_match_items` |
| 10 | Products without a category | 610 of 32,951 products | Category `unknown` | `stg_products` |
| 11 | Categories without an English name | 2 (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`) | Fall back to the Portuguese name | `stg_products` |
| 12 | Sparse months at the edges | 2016-09: 4 orders, 2016-10: 324, 2016-11: none, 2016-12: 1; 2018-09: 16, 2018-10: 4 | Analysis period is **2017-01-01 … 2018-08-31** (20 full months); edge months stay in the tables with `is_analysis_period = false` | `fct_orders`, marts |
| 13 | Recent orders have had less time to arrive | Purchases in the last weeks of the period are only observed if delivered before the data was cut | Delivery metrics for the last months may look better than reality; stated as a limitation | Methodology page |
| 14 | Full-row duplicates | 261,831 in `geolocation`, 0 in every other table | `geolocation` is not used (state-level geography comes from customers and sellers) | — |
| 15 | UTF-8 byte order mark in `product_category_name_translation.csv` | First column header | DuckDB's CSV reader strips it; column name verified | `stg_category_translation` |

Other checks that came back clean: no duplicate `order_id` or `customer_id`, no missing estimated
delivery dates, all prices positive (0.85 to 6,735 BRL), review scores only 1–5.

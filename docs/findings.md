# Key findings

Analysis period: January 2017 – August 2018, valid orders only. Every number below comes from the
notebooks linked in each section.

## 1. Growth came from new customers, and it stalled in 2018

GMV in January–August 2018 was **8.59 M BRL, 2.4x the same months of 2017** (3.57 M BRL, +140%).
Orders grew by the same amount (+137%) while the average order value stayed flat at ~160 BRL.
Since January 2018, however, monthly GMV has stayed between 0.98 and 1.16 M BRL, never above the
Black Friday peak of November 2017. The top 10 categories added 67% of the new GMV, led by health &
beauty and watches & gifts.

**Recommendation:** with basket size flat and acquisition plateauing, the next stage of growth has to
come from customers who already bought (see 2).
→ [`01_growth`](../notebooks/01_growth.ipynb)

## 2. Almost nobody buys twice

**97% of customers placed exactly one order.** Only 0.48% of a cohort orders again in the month after
their first purchase, and no cohort goes above 0.71% in any later month. 30% of the second orders that
do happen are placed on the same day as the first, so genuine return visits are rarer still.

**Recommendation:** launch and A/B-test a second-purchase programme (a time-limited offer in the first
30 days after delivery), aimed first at the "Promising high-value" segment: 15% of customers who
bought recently and spent in the top 40%. Together with "At risk high-value", these one-time buyers are
38% of customers and 68% of revenue. "At risk high-value" customers also had the highest
late-delivery rate of any segment (8.1%), so the win-back should start by checking how their order
went.
→ [`02_retention`](../notebooks/02_retention.ipynb), [`03_rfm`](../notebooks/03_rfm.ipynb)

## 3. Late delivery goes with far worse reviews

On-time orders average **4.29 stars, late orders 2.27** (difference −2.02, 95% CI −2.06 to −1.98,
Mann–Whitney p < 0.001). The share of 1–2 star reviews rises from 9% on time to 32% at 1–3 days late
and 68% at 4–7 days late. The gap holds inside every one of 21 states (−1.6 to −2.6 stars) and inside
the five largest categories, so it is not explained by where or what people buy. The data is
observational, so this is a strong association rather than a proven cause.

**Recommendation:** treat the promised delivery date as a product feature. Missing it by four days or
more costs most of the goodwill of the order; a more conservative estimate in high-risk routes is
cheaper than a 1-star review.
→ [`04_delivery_vs_reviews`](../notebooks/04_delivery_vs_reviews.ipynb)

## 4. Delays concentrate in time and place

- **Time:** the late-delivery rate more than doubled, from 3.5% in January–August 2017 to 7.7% in the same
  months of 2018. It peaked at 12.4% in November 2017 (Black Friday) and 14.1% / 19.0% in February /
  March 2018, against about 3% in calm months of 2017.
- **Place:** 4.5% in São Paulo, the largest market, against 12.1% in Rio de Janeiro and 17.5% in
  Maranhão (states with 500+ delivered orders range from 4.1% in Paraná to 17.5%).
- **Sellers:** the worst 10% of sellers with 50+ delivered orders (42 sellers) are late on 15.3% of their orders,
  against 6.2% for the rest. They are a clear target for improvement, though they account for only
  about a tenth of all late deliveries; most delays are spread across the network.

**Recommendation:** plan carrier capacity ahead of sales peaks; widen delivery estimates for the
North-East and Rio de Janeiro; put the slowest sellers on a delivery-time improvement plan and track
their late rate monthly.
→ [`04_delivery_vs_reviews`](../notebooks/04_delivery_vs_reviews.ipynb)

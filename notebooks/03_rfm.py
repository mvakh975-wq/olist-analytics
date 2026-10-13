# %% [markdown]
# # 03 · Who are our customers?
# RFM segmentation per person. Recency and monetary value are quintiles (5 = best).
# Frequency is 1, 2 or 3+ orders: with ~97% of customers buying once, frequency quintiles
# would put almost everyone into the same bucket.

# %%
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from _common import ACCENT, MUTED, con

db = con()
db.sql("select frequency, count(*) as customers from mart_rfm group by 1 order by 1").df()

# %%
seg = db.sql("""
    select segment,
           count(*) as customers,
           count(*) / sum(count(*)) over () as share_of_customers,
           sum(monetary) / sum(sum(monetary)) over () as share_of_revenue,
           avg(monetary) as avg_revenue_per_customer,
           median(recency_days) as median_recency_days
    from mart_rfm group by 1 order by share_of_revenue desc
""").df()
seg

# %%
fig, ax = plt.subplots(figsize=(9, 4))
y = range(len(seg))[::-1]
ax.barh(
    [i + 0.2 for i in y],
    seg.share_of_customers,
    height=0.38,
    color=MUTED,
    label="Share of customers",
)
ax.barh(
    [i - 0.2 for i in y], seg.share_of_revenue, height=0.38, color=ACCENT, label="Share of revenue"
)
ax.set_yticks(list(y), seg.segment)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_xlabel("% of total")
ax.set_title("Three one-time-buyer segments hold most of the revenue")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, loc="lower right")
plt.show()

# %% [markdown]
# ## What to do with each segment
#
# | Segment | Rule | Action |
# |---|---|---|
# | Champions | 2+ orders, bought recently | Early access, referral programme |
# | Loyal | 2+ orders, not recently | Personalised win-back with category recommendations |
# | Promising high-value | 1 order, recent, top-40% spend | Second-purchase offer within the first 30 days |
# | Recent | 1 order, recent, lower spend | Onboarding emails, cross-sell cheap add-ons |
# | At risk high-value | 1 order, long ago, top-40% spend | Win-back campaign; check whether delivery went wrong |
# | Hibernating | everyone else | Low-cost reactivation only |

# %%
db.sql("""
    select r.segment,
           avg(o.is_late::int) as late_rate,
           avg(o.review_score) as avg_review_score
    from mart_rfm r
    join fct_orders o using (customer_unique_id)
    where o.is_valid_order
    group by 1 order by late_rate desc
""").df()

# %% [markdown]
# ## Findings
# - **Two high-value one-time segments** — "Promising high-value" (recent) and "At risk high-value"
#   (long ago) — are 30% of customers and bring 56% of revenue, at ~300 BRL per customer.
# - Repeat buyers ("Champions" + "Loyal") are only 3% of customers and 6% of revenue.
# - Late-delivery rates differ little between segments (5.5–7.3%), so segment membership is not driven
#   by delivery experience; the next notebook looks at delivery directly.

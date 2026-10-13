# %% [markdown]
# # 04 · Does delivery affect satisfaction? Where does logistics fail?
# Delivered orders in the analysis period with a review. Delay = delivered date − estimated
# delivery date, in days. This is observational data: the analysis shows a strong association
# and checks it inside states and categories, but it cannot prove causation.

# %%
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from _common import ACCENT, MARTS, MUTED, SIGNAL, bootstrap_diff_ci, con
from scipy.stats import mannwhitneyu

db = con()
df = db.sql("""
    select * from mart_delivery_performance
    where is_analysis_period and review_score is not null
""").df()
print(f"{len(df):,} reviewed deliveries, {df.is_late.mean():.1%} late")

# %% [markdown]
# ## Review score by delay

# %%
by_bucket = (
    df.groupby(["delay_bucket_order", "delay_bucket"])
    .agg(
        orders=("order_id", "count"),
        mean_score=("review_score", "mean"),
        low_score_share=("is_low_score", "mean"),
    )
    .reset_index()
)
by_bucket

# %%
fig, ax = plt.subplots()
colors = [ACCENT] + [SIGNAL] * (len(by_bucket) - 1)
ax.bar(by_bucket.delay_bucket, by_bucket.low_score_share, color=colors, width=0.6)
ax.set_title("A delay of 4+ days turns most reviews into 1–2 stars")
ax.set_xlabel("Delivery vs estimated date")
ax.set_ylabel("1–2 star reviews, % of orders")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.grid(axis="x", visible=False)
plt.show()

# %% [markdown]
# ## Size and significance of the effect
# Difference of mean scores with a 95% bootstrap interval, Mann–Whitney U test
# (scores are ordinal, so a rank test), and rank-biserial correlation as effect size.


# %%
def compare(name, a, b):
    diff, lo, hi = bootstrap_diff_ci(a, b)
    u, p = mannwhitneyu(a, b, alternative="two-sided")
    return {
        "comparison": name,
        "n_on_time": len(a),
        "n_late": len(b),
        "mean_on_time": a.mean(),
        "mean_late": b.mean(),
        "diff": diff,
        "ci_low": lo,
        "ci_high": hi,
        "mannwhitney_p": p,
        "rank_biserial": 1 - 2 * u / (len(a) * len(b)),
    }


on_time = df.loc[~df.is_late, "review_score"].to_numpy()
late = df.loc[df.is_late, "review_score"].to_numpy()
very_late = df.loc[df.delay_days >= 15, "review_score"].to_numpy()
effect = pd.DataFrame(
    [
        compare("late vs on time", on_time, late),
        compare("15+ days late vs on time", on_time, very_late),
    ]
)
effect.to_parquet(MARTS / "stats_delay_effect.parquet", index=False)
effect

# %% [markdown]
# ## Does the gap hold inside each state? (confounding check)
# If late deliveries were concentrated in states whose customers rate lower anyway, the gap would
# shrink inside states. States with at least 300 reviewed deliveries and 30 late ones.

# %%
rows = []
for state, g in df.groupby("customer_state"):
    if len(g) < 300 or g.is_late.sum() < 30:
        continue
    rows.append(
        {
            "customer_state": state,
            "n": len(g),
            "late_share": g.is_late.mean(),
            "mean_on_time": g.loc[~g.is_late, "review_score"].mean(),
            "mean_late": g.loc[g.is_late, "review_score"].mean(),
        }
    )
by_state = pd.DataFrame(rows).assign(diff=lambda d: d.mean_late - d.mean_on_time)
by_state.to_parquet(MARTS / "stats_delay_by_state.parquet", index=False)
by_state.sort_values("diff")

# %% [markdown]
# ## …and inside the largest categories?

# %%
top_cats = df.main_category.value_counts().head(5).index
pd.DataFrame(
    [
        {
            "category": c,
            "n": len(g),
            "mean_on_time": g.loc[~g.is_late, "review_score"].mean(),
            "mean_late": g.loc[g.is_late, "review_score"].mean(),
        }
        for c, g in df[df.main_category.isin(top_cats)].groupby("main_category")
    ]
).assign(diff=lambda d: d.mean_late - d.mean_on_time)

# %% [markdown]
# ## Where does logistics fail?

# %%
deliv = db.sql("select * from mart_delivery_performance where is_analysis_period").df()
states = (
    deliv.groupby("customer_state")
    .agg(
        orders=("order_id", "count"),
        late_rate=("is_late", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
    )
    .query("orders >= 500")
    .sort_values("late_rate", ascending=False)
)
states.head(10)

# %%
# every state with 500+ delivered orders; above-average states in the signal colour
shown = states.iloc[::-1]
overall = deliv.is_late.mean()
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(
    shown.index,
    shown.late_rate,
    color=[SIGNAL if r > overall else MUTED for r in shown.late_rate],
    height=0.6,
)
ax.axvline(overall, color="#52514e", linewidth=1, linestyle="--")
ax.text(
    overall,
    len(shown) - 0.4,
    f" all states {overall:.1%}",
    fontsize=9,
    color="#52514e",
    va="bottom",
)
ax.set_title("Late deliveries are 2–4x more common in the North-East and Rio than in São Paulo")
ax.set_xlabel("Late deliveries, % of delivered orders")
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.grid(axis="y", visible=False)
plt.show()

# %%
monthly_late = deliv.groupby("purchase_month").is_late.mean()
fig, ax = plt.subplots()
ax.plot(
    monthly_late.index, monthly_late.values, color=SIGNAL, linewidth=2, marker="o", markersize=4
)
ax.set_title("Late deliveries spiked in Nov 2017 (Black Friday) and again in Feb–Mar 2018")
ax.set_xlabel("Purchase month")
ax.set_ylabel("Late deliveries, % of delivered orders")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(bottom=0)
plt.show()

# %% [markdown]
# ## Sellers

# %%
sellers = db.sql("""
    select seller_id, seller_state, n_orders, late_rate, avg_review_score
    from dim_sellers where n_orders >= 50
""").df()
print(f"{len(sellers)} sellers with 50+ orders; median late rate {sellers.late_rate.median():.1%}")
sellers.sort_values("late_rate", ascending=False).head(10)

# %%
db.sql("""
    with s as (select seller_id, late_rate, n_orders from dim_sellers where n_orders >= 50),
         ranked as (select *, ntile(10) over (order by late_rate desc) as decile from s)
    select decile = 1 as worst_10pct_sellers,
           count(*) as sellers,
           sum(n_orders) as orders,
           sum(late_rate * n_orders) / sum(n_orders) as late_rate
    from ranked group by 1
""").df()

# %% [markdown]
# ## Findings
# - **Late delivery goes with far worse reviews**: on-time orders average
#   4.29 stars, late ones 2.27 (difference −2.02, 95% CI −2.06 to −1.98; Mann–Whitney p < 0.001;
#   rank-biserial −0.64, a large effect). 15+ days late: −2.57.
# - **Four or more days late flips the review**: the share of 1–2 star reviews goes from 9% (on time)
#   to 32% (1–3 days late) and 68% (4–7 days late).
# - **The gap holds inside each of the 21 states with enough late orders** (−1.6 to −2.6 stars) and inside the five
#   largest categories (−1.9 to −2.2), so it is not explained by where or what people buy.
#   It is still an observational association.
# - **Where it fails**: late rates spiked in the Black Friday month (12.4% in Nov 2017) and again in
#   Feb–Mar 2018 (14.1% and 19.0%), against about 3% in calm months of 2017; by state, 4.5% in SP (the largest
#   market) against 12.1% in RJ and 17.5% in MA;
#   the worst 10% of sellers with 50+ orders (42 sellers) are late on 15.4% of orders vs 6.2% for the rest.

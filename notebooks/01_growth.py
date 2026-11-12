# %% [markdown]
# # 01 · Is the business growing?
# Monthly GMV, orders, average order value and freight share over the analysis period
# (2017-01 … 2018-08), and which categories drove the growth.
# GMV = items price + freight, BRL; valid orders only (see `docs/data_quality.md`).

# %%
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from _common import ACCENT, MUTED, con

db = con()
kpis = db.sql("select * from mart_monthly_kpis where is_analysis_period order by month").df()
kpis[["month", "orders", "customers", "gmv", "avg_order_value", "freight_share", "late_rate"]]

# %%
fig, ax = plt.subplots()
ax.plot(kpis.month, kpis.gmv / 1e6, color=ACCENT, linewidth=2, marker="o", markersize=4)
ax.set_title("Monthly GMV grew ~2.4x year over year, with a Black Friday peak in Nov 2017")
ax.set_xlabel("Purchase month")
ax.set_ylabel("GMV, million BRL")
ax.set_ylim(bottom=0)
plt.show()

# %% [markdown]
# ## Same months, one year apart
# January–August 2018 vs January–August 2017, so seasonality does not distort the comparison.

# %%
yoy = db.sql("""
    select
        case when month < '2018-01-01' then 'Jan–Aug 2017' else 'Jan–Aug 2018' end as period,
        sum(orders) as orders,
        sum(customers) as customer_months,
        sum(gmv) as gmv,
        sum(gmv) / sum(orders) as avg_order_value,
        sum(freight_value) / sum(gmv) as freight_share
    from mart_monthly_kpis
    where month between '2017-01-01' and '2017-08-01' or month between '2018-01-01' and '2018-08-01'
    group by 1 order by 1
""").df()
yoy["gmv_growth"] = yoy.gmv / yoy.gmv.shift(1) - 1
yoy["orders_growth"] = yoy.orders / yoy.orders.shift(1) - 1
yoy

# %% [markdown]
# ## Which categories drove the growth?

# %%
cats = db.sql("""
    with p as (
        select
            category,
            sum(price + freight_value) filter (where purchase_month between '2017-01-01' and '2017-08-01') as gmv_2017,
            sum(price + freight_value) filter (where purchase_month between '2018-01-01' and '2018-08-01') as gmv_2018
        from fct_order_items
        where is_valid_order
        group by 1
    )
    select category, coalesce(gmv_2017, 0) as gmv_2017, coalesce(gmv_2018, 0) as gmv_2018,
           coalesce(gmv_2018, 0) - coalesce(gmv_2017, 0) as gmv_change,
           (coalesce(gmv_2018, 0) - coalesce(gmv_2017, 0))
             / sum(coalesce(gmv_2018, 0) - coalesce(gmv_2017, 0)) over () as share_of_growth
    from p order by gmv_change desc
""").df()
cats.head(10)

# %%
top = cats.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.barh(top.category, top.gmv_change / 1e3, color=ACCENT, height=0.6)
ax.set_title("Top 10 categories by GMV added, Jan–Aug 2018 vs Jan–Aug 2017")
ax.set_xlabel("GMV added, thousand BRL")
ax.grid(axis="y", visible=False)
plt.show()

# %%
print(f"Top 10 categories account for {cats.head(10).share_of_growth.sum():.0%} of GMV growth")

# %% [markdown]
# ## Order value and freight

# %%
fig, ax = plt.subplots()
ax.plot(kpis.month, kpis.freight_share, color=MUTED, linewidth=2, marker="o", markersize=4)
ax.set_title("Freight share of GMV edged up from 13.8% to 14.6% year over year")
ax.set_xlabel("Purchase month")
ax.set_ylabel("Freight share of GMV, %")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
plt.show()

# %% [markdown]
# ## Findings
# - **GMV grew 2.4x**: 8.59 M BRL in Jan–Aug 2018 vs 3.57 M BRL in Jan–Aug 2017 (+140%);
#   orders grew +137% (53,530 vs 22,562).
# - **Growth came from more orders, not bigger baskets**: average order value stayed flat
#   (158.5 → 160.5 BRL).
# - **Growth is broad but led by a few categories**: the top 10 categories added 67% of the new GMV,
#   led by health_beauty (+600 k BRL) and watches_gifts (+551 k BRL).
# - **Freight share edged up** from 13.8% to 14.6% of GMV.
# - **Sales stopped growing in 2018**: monthly GMV stayed between 0.98 and 1.16 M BRL from January to August, below the Nov 2017 peak of 1.17 M.

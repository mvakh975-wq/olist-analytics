from tests.conftest import query, raw


def test_one_row_per_order(built_db):
    ((dupes,),) = query(
        built_db, "select count(*) - count(distinct order_id) from int_orders_enriched"
    )
    ((orders,),) = query(built_db, f"select count(*) from {raw('olist_orders_dataset')}")
    ((rows,),) = query(built_db, "select count(*) from int_orders_enriched")
    assert dupes == 0
    assert rows == orders


def test_undelivered_orders_have_null_delay(built_db):
    rows = query(
        built_db,
        """select count(*) from int_orders_enriched
           where (order_status <> 'delivered' or delivered_at is null)
             and (delay_days is not null or is_late is not null or delivery_days is not null)""",
    )
    assert rows == [(0,)]
    # the fixture has a delivered order without a delivery date; it must not count as on time
    ((n,),) = query(
        built_db,
        "select count(*) from int_orders_enriched where order_status = 'delivered' and delivered_at is null",
    )
    assert n >= 1


def test_one_review_score_per_order(built_db):
    # orders without a review keep NULL, not 0
    rows = query(
        built_db,
        f"""select count(*) from int_orders_enriched o
            where not exists (select 1 from {raw("olist_order_reviews_dataset")} r
                              where r.order_id = o.order_id)
              and (o.review_score is not null or o.has_review)""",
    )
    assert rows == [(0,)]


def test_conflicting_reviews_resolve_to_latest_answer(built_db):
    rows = query(
        built_db,
        f"""with r as (
                select order_id, review_score::int as score,
                       row_number() over (partition by order_id
                                          order by review_answer_timestamp::timestamp desc) as rn
                from {raw("olist_order_reviews_dataset")})
            select count(*) from int_orders_enriched o join r using (order_id)
            where r.rn = 1 and o.review_score <> r.score""",
    )
    assert rows == [(0,)]


def test_gmv_matches_raw_items(built_db):
    ((model,),) = query(built_db, "select sum(gmv) from int_orders_enriched")
    ((expected,),) = query(
        built_db,
        f"""select sum(price::decimal(12,2) + freight_value::decimal(12,2))
            from {raw("olist_order_items_dataset")}""",
    )
    assert model == expected


def test_late_flag_consistent_with_delay(built_db):
    rows = query(
        built_db,
        """select count(*) from int_orders_enriched
           where is_late is not null and is_late <> (delay_days > 0)""",
    )
    assert rows == [(0,)]


def test_valid_order_requires_items_and_live_status(built_db):
    rows = query(
        built_db,
        """select count(*) from int_orders_enriched
           where is_valid_order <> (order_status not in ('canceled', 'unavailable') and n_items > 0)""",
    )
    assert rows == [(0,)]
    ((no_items,),) = query(built_db, "select count(*) from int_orders_enriched where n_items = 0")
    assert no_items >= 1


def test_main_seller_is_the_highest_priced_item(built_db):
    rows = query(
        built_db,
        f"""with i as (
                select order_id, seller_id,
                       row_number() over (partition by order_id
                           order by price::decimal(12,2) desc, order_item_id::int) as rn
                from {raw("olist_order_items_dataset")})
            select count(*) from int_orders_enriched o join i using (order_id)
            where i.rn = 1 and o.main_seller_id <> i.seller_id""",
    )
    assert rows == [(0,)]

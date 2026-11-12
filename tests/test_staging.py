from tests.conftest import query, raw


def test_row_counts_match_raw(built_db):
    pairs = {
        "stg_orders": "olist_orders_dataset",
        "stg_order_items": "olist_order_items_dataset",
        "stg_order_payments": "olist_order_payments_dataset",
        "stg_order_reviews": "olist_order_reviews_dataset",
        "stg_customers": "olist_customers_dataset",
        "stg_sellers": "olist_sellers_dataset",
        "stg_products": "olist_products_dataset",
    }
    for model, src in pairs.items():
        ((n_model,),) = query(built_db, f"select count(*) from {model}")
        ((n_raw,),) = query(built_db, f"select count(*) from {raw(src)}")
        assert n_model == n_raw, model


def test_products_always_have_category(built_db):
    assert query(built_db, "select count(*) from stg_products where category is null") == [(0,)]


def test_untranslated_category_falls_back_to_portuguese(built_db):
    rows = query(
        built_db,
        """select count(*) from stg_products
           where category_name_pt is not null and category = 'unknown'""",
    )
    assert rows == [(0,)]


def test_timestamps_are_typed(built_db):
    ((dtype,),) = query(built_db, "select typeof(purchased_at) from stg_orders limit 1")
    assert dtype == "TIMESTAMP"

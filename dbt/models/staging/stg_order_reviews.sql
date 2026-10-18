-- (review_id, order_id) is the key: one review can be attached to several orders
-- review text is not used, only whether a comment was left
select
    review_id,
    order_id,
    review_score::int as review_score,
    coalesce(trim(review_comment_message), '') <> '' as has_comment,
    review_creation_date::timestamp as review_created_at,
    review_answer_timestamp::timestamp as review_answered_at
from {{ source('olist', 'olist_order_reviews_dataset') }}

# Test fixtures

`raw/` holds a sample of real rows from the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(CC BY-NC-SA 4.0, © Olist), about 90 orders with every related row, chosen so the edge cases
found during profiling are present. Regenerate with:

```
uv run python -m scripts.make_fixtures data/raw tests/fixtures/raw
```

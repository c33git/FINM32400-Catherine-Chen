# Assignment 4: Smart Order Router

This assignment builds a machine learning system to predict price improvement and route orders to the best exchange.

## Files

- `feature_engineering.py`: Annotates executions with quotes and calculates price improvement
- `train_models.py`: Trains per-exchange regression models
- `somewhat_smart_order_router.py`: Inference script that loads models and routes orders
- `test_somewhat_smart_order_router.py`: Unit tests for the order router


# Run feature engineering
python feature_engineering.py \
    --executions /opt/assignment3/executions.csv \
    --quotes /opt/assignment4/quotes_2025-09-10_small.csv.gz \
    --output annotated_executions.csv \
    --filter_symbols

# Train models
python train_models.py \
    --input annotated_executions.csv \
    --output_dir models/

# Run tests
pytest test_somewhat_smart_order_router.py -v
```

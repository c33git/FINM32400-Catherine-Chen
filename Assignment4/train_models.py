"""Train per-exchange regression models to predict price improvement.

This script loads the feature-engineered data, trains regression models
for each exchange, performs hyperparameter tuning, and saves the models.
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for model training.
    
    Features: side, order_qty, limit_price, bid_price, ask_price, bid_size, ask_size
    Target: price_improvement
    
    Note: execution_time and execution_price are NOT included as they won't be
    available for new orders.
    
    Args:
        df: DataFrame with feature-engineered data
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Select feature columns
    feature_cols = [
        'side', 'order_qty', 'limit_price',
        'bid_price', 'ask_price', 'bid_size', 'ask_size'
    ]
    
    # Check which columns exist
    available_cols = [col for col in feature_cols if col in df.columns]
    
    if len(available_cols) < len(feature_cols):
        missing = set(feature_cols) - set(available_cols)
        print(f"Warning: Missing columns {missing}, using available columns")
    
    X = df[available_cols].copy()
    y = df['price_improvement'].copy()
    
    # Convert side to numeric (1 for buy, 0 for sell)
    if 'side' in X.columns:
        X['side'] = (X['side'] == '1').astype(int)
    
    # Fill missing values in bid_size and ask_size with 0
    if 'bid_size' in X.columns:
        X['bid_size'] = X['bid_size'].fillna(0)
    if 'ask_size' in X.columns:
        X['ask_size'] = X['ask_size'].fillna(0)
    
    # Drop rows with missing values
    mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[mask]
    y = y[mask]
    
    return X, y


def train_exchange_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    exchange: str,
    use_hyperparameter_tuning: bool = True
) -> Pipeline:
    """Train a regression model for a specific exchange.
    
    Args:
        X_train: Training features
        y_train: Training target
        exchange: Exchange name (for logging)
        use_hyperparameter_tuning: Whether to perform hyperparameter tuning
        
    Returns:
        Trained pipeline (scaler + model)
    """
    print(f"\nTraining model for {exchange}...")
    print(f"  Training samples: {len(X_train)}")
    
    if len(X_train) < 10:
        print(f"  Warning: Too few samples for {exchange}, skipping")
        return None
    
    # Create pipeline with scaler and model
    if use_hyperparameter_tuning:
        # Use GradientBoostingRegressor with hyperparameter tuning
        # Note: GradientBoostingRegressor doesn't support n_jobs parameter
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(random_state=42))
        ])
        
        # Hyperparameter grid
        param_grid = {
            'model__n_estimators': [50, 100],
            'model__max_depth': [3, 5, 7],
            'model__learning_rate': [0.01, 0.1]
        }
        
        # Grid search with cross-validation
        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=3,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        best_pipeline = grid_search.best_estimator_
        
        print(f"  Best parameters: {grid_search.best_params_}")
        print(f"  Best CV score (neg MSE): {grid_search.best_score_:.4f}")
        
    else:
        # Simple model without tuning
        # Note: GradientBoostingRegressor doesn't support n_jobs parameter
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            ))
        ])
        
        pipeline.fit(X_train, y_train)
        best_pipeline = pipeline
    
    return best_pipeline


def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    exchange: str
) -> dict:
    """Evaluate model performance.
    
    Args:
        model: Trained pipeline
        X_test: Test features
        y_test: Test target
        exchange: Exchange name
        
    Returns:
        Dictionary with evaluation metrics
    """
    y_pred = model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    metrics = {
        'exchange': exchange,
        'rmse': rmse,
        'r2': r2,
        'mse': mse,
        'n_test_samples': len(X_test)
    }
    
    print(f"  Test RMSE: {rmse:.4f}")
    print(f"  Test R²: {r2:.4f}")
    
    return metrics


def main():
    """Main function to train models."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Train per-exchange regression models for price improvement'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to feature-engineered CSV file'
    )
    parser.add_argument(
        '--output_dir',
        required=True,
        help='Directory to save trained models'
    )
    parser.add_argument(
        '--test_size',
        type=float,
        default=0.2,
        help='Fraction of data to use for testing (default: 0.2)'
    )
    parser.add_argument(
        '--min_samples',
        type=int,
        default=50,
        help='Minimum samples required to train a model for an exchange (default: 50)'
    )
    parser.add_argument(
        '--no_tuning',
        action='store_true',
        help='Skip hyperparameter tuning (faster but less optimal)'
    )
    
    args = parser.parse_args()
    
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    print("Loading feature-engineered data...")
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} rows")
    
    # Prepare features
    X, y = prepare_features(df)
    print(f"Prepared {len(X)} samples with {X.shape[1]} features")
    
    # Get exchanges with enough data
    exchange_counts = df['exchange'].value_counts()
    valid_exchanges = exchange_counts[exchange_counts >= args.min_samples].index.tolist()
    
    print(f"\nExchanges with >= {args.min_samples} samples: {len(valid_exchanges)}")
    print(f"Exchanges: {valid_exchanges}")
    
    # Train models for each exchange
    models = {}
    evaluation_results = []
    
    for exchange in valid_exchanges:
        # Filter to this exchange
        exchange_mask = df['exchange'] == exchange
        X_exchange = X[exchange_mask]
        y_exchange = y[exchange_mask]
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_exchange,
            y_exchange,
            test_size=args.test_size,
            random_state=42
        )
        
        # Train model
        model = train_exchange_model(
            X_train,
            y_train,
            exchange,
            use_hyperparameter_tuning=not args.no_tuning
        )
        
        if model is not None:
            # Evaluate
            metrics = evaluate_model(model, X_test, y_test, exchange)
            evaluation_results.append(metrics)
            
            # Save model
            model_path = os.path.join(args.output_dir, f'model_{exchange}.joblib')
            joblib.dump(model, model_path)
            print(f"  Saved model to {model_path}")
            
            models[exchange] = model
    
    # Save all models as a dictionary
    models_path = os.path.join(args.output_dir, 'models.joblib')
    joblib.dump(models, models_path)
    print(f"\nSaved all models to {models_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("Training Summary")
    print("="*50)
    results_df = pd.DataFrame(evaluation_results)
    print(results_df.to_string(index=False))
    
    # Save evaluation results
    results_path = os.path.join(args.output_dir, 'evaluation_results.csv')
    results_df.to_csv(results_path, index=False)
    print(f"\nSaved evaluation results to {results_path}")


if __name__ == '__main__':
    main()


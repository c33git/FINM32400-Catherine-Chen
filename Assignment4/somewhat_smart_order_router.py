"""Smart order router that predicts price improvement and selects best exchange.

This module loads trained models and provides a function to determine
the best exchange for a new order based on predicted price improvement.
"""
import joblib
import os
from typing import Tuple
import numpy as np
import pandas as pd


def best_price_improvement(
    symbol: str,
    side: str,
    quantity: int,
    limit_price: float,
    bid_price: float,
    ask_price: float,
    bid_size: int,
    ask_size: int
) -> Tuple[str, float]:
    """Determine the exchange with the best predicted price improvement.
    
    Args:
        symbol: Stock ticker symbol (not used in model, can be discarded)
        side: Order side ('B' for buy or 'S' for sell)
        quantity: Order quantity
        limit_price: Limit price of the order
        bid_price: Current bid price from NBBO
        ask_price: Current ask price from NBBO
        bid_size: Current bid size from NBBO
        ask_size: Current ask size from NBBO
        
    Returns:
        Tuple of (exchange_name, predicted_price_improvement)
        Returns (None, float('-inf')) if no models are available
    """
    # Load models (lazy loading - load on first call)
    if not hasattr(best_price_improvement, '_models'):
        # Try to find models file in current directory or common locations
        model_paths = [
            'models.joblib',
            'assignment4_order_router/models.joblib',
            os.path.join(os.path.dirname(__file__), 'models.joblib')
        ]
        
        models = None
        for path in model_paths:
            if os.path.exists(path):
                models = joblib.load(path)
                break
        
        if models is None:
            raise FileNotFoundError(
                "Could not find models.joblib. Please ensure models are trained and saved."
            )
        
        best_price_improvement._models = models
    
    models = best_price_improvement._models
    
    if not models:
        return (None, float('-inf'))
    
    # Prepare features
    # Convert side: 'B' or '1' -> 1 (buy), anything else -> 0 (sell)
    side_numeric = 1 if (side == 'B' or side == '1') else 0
    
    # Handle missing bid_size/ask_size
    bid_size = bid_size if bid_size is not None and not np.isnan(bid_size) else 0
    ask_size = ask_size if ask_size is not None and not np.isnan(ask_size) else 0
    
    # Create feature array
    features = np.array([[
        side_numeric,
        quantity,
        limit_price,
        bid_price,
        ask_price,
        bid_size,
        ask_size
    ]])
    
    # Predict price improvement for each exchange
    best_exchange = None
    best_prediction = float('-inf')
    
    for exchange, model in models.items():
        try:
            prediction = model.predict(features)[0]
            if prediction > best_prediction:
                best_prediction = prediction
                best_exchange = exchange
        except Exception as e:
            # Skip exchanges where prediction fails
            continue
    
    if best_exchange is None:
        return (None, float('-inf'))
    
    return (best_exchange, best_prediction)


def load_models(models_path: str = None) -> dict:
    """Load models from disk.
    
    Args:
        models_path: Path to models.joblib file. If None, searches common locations.
        
    Returns:
        Dictionary of {exchange: model}
    """
    if models_path is None:
        model_paths = [
            'models.joblib',
            'assignment4_order_router/models.joblib',
            os.path.join(os.path.dirname(__file__), 'models.joblib')
        ]
        
        for path in model_paths:
            if os.path.exists(path):
                models_path = path
                break
        
        if models_path is None:
            raise FileNotFoundError("Could not find models.joblib")
    
    return joblib.load(models_path)


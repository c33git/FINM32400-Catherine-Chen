"""Unit tests for somewhat_smart_order_router module."""
import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import os
import tempfile
from somewhat_smart_order_router import best_price_improvement, load_models


@pytest.fixture
def sample_models():
    """Create sample models for testing."""
    # Create a simple model pipeline
    model1 = Pipeline([
        ('scaler', StandardScaler()),
        ('model', GradientBoostingRegressor(
            n_estimators=10,
            max_depth=3,
            random_state=42,
            n_jobs=1
        ))
    ])
    
    model2 = Pipeline([
        ('scaler', StandardScaler()),
        ('model', GradientBoostingRegressor(
            n_estimators=10,
            max_depth=3,
            random_state=42,
            n_jobs=1
        ))
    ])
    
    # Train on dummy data
    X_dummy = np.array([
        [1, 100, 50.0, 49.5, 50.5, 1000, 1000],
        [0, 200, 50.0, 49.5, 50.5, 1000, 1000],
        [1, 150, 75.0, 74.5, 75.5, 2000, 2000],
    ])
    y_dummy = np.array([0.1, 0.2, 0.15])
    
    model1.fit(X_dummy, y_dummy)
    model2.fit(X_dummy, y_dummy + 0.05)  # Slightly different target
    
    return {
        'EXCHANGE1': model1,
        'EXCHANGE2': model2
    }


@pytest.fixture
def temp_models_file(sample_models):
    """Create a temporary models file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as f:
        temp_path = f.name
        joblib.dump(sample_models, temp_path)
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_normal_order(temp_models_file, sample_models):
    """Test normal order routing."""
    # Temporarily replace models
    original_models = getattr(best_price_improvement, '_models', None)
    best_price_improvement._models = sample_models
    
    try:
        # Test buy order
        exchange, improvement = best_price_improvement(
            symbol='AAPL',
            side='B',
            quantity=100,
            limit_price=150.0,
            bid_price=149.5,
            ask_price=150.5,
            bid_size=1000,
            ask_size=1000
        )
        
        # Should return a valid exchange
        assert exchange is not None
        assert isinstance(exchange, str)
        assert isinstance(improvement, (int, float))
        assert improvement > float('-inf')
        
        # Test sell order
        exchange2, improvement2 = best_price_improvement(
            symbol='AAPL',
            side='S',
            quantity=200,
            limit_price=150.0,
            bid_price=149.5,
            ask_price=150.5,
            bid_size=1000,
            ask_size=1000
        )
        
        assert exchange2 is not None
        assert isinstance(improvement2, (int, float))
        
    finally:
        # Restore original models
        if original_models is not None:
            best_price_improvement._models = original_models
        elif hasattr(best_price_improvement, '_models'):
            delattr(best_price_improvement, '_models')


def test_corner_case_missing_sizes(temp_models_file, sample_models):
    """Test corner case with missing bid/ask sizes."""
    original_models = getattr(best_price_improvement, '_models', None)
    best_price_improvement._models = sample_models
    
    try:
        # Test with None/Nan sizes
        exchange, improvement = best_price_improvement(
            symbol='AAPL',
            side='B',
            quantity=100,
            limit_price=150.0,
            bid_price=149.5,
            ask_price=150.5,
            bid_size=None,
            ask_size=None
        )
        
        # Should still work (sizes default to 0)
        assert exchange is not None
        assert isinstance(improvement, (int, float))
        
        # Test with NaN sizes
        exchange2, improvement2 = best_price_improvement(
            symbol='AAPL',
            side='S',
            quantity=50,
            limit_price=75.0,
            bid_price=74.5,
            ask_price=75.5,
            bid_size=np.nan,
            ask_size=np.nan
        )
        
        assert exchange2 is not None
        assert isinstance(improvement2, (int, float))
        
    finally:
        if original_models is not None:
            best_price_improvement._models = original_models
        elif hasattr(best_price_improvement, '_models'):
            delattr(best_price_improvement, '_models')


def test_corner_case_side_variations(temp_models_file, sample_models):
    """Test corner case with different side representations."""
    original_models = getattr(best_price_improvement, '_models', None)
    best_price_improvement._models = sample_models
    
    try:
        # Test with '1' for buy (as in original data)
        exchange1, improvement1 = best_price_improvement(
            symbol='AAPL',
            side='1',
            quantity=100,
            limit_price=150.0,
            bid_price=149.5,
            ask_price=150.5,
            bid_size=1000,
            ask_size=1000
        )
        
        assert exchange1 is not None
        
        # Test with 'B' for buy
        exchange2, improvement2 = best_price_improvement(
            symbol='AAPL',
            side='B',
            quantity=100,
            limit_price=150.0,
            bid_price=149.5,
            ask_price=150.5,
            bid_size=1000,
            ask_size=1000
        )
        
        assert exchange2 is not None
        
        # Both should work
        assert isinstance(improvement1, (int, float))
        assert isinstance(improvement2, (int, float))
        
    finally:
        if original_models is not None:
            best_price_improvement._models = original_models
        elif hasattr(best_price_improvement, '_models'):
            delattr(best_price_improvement, '_models')


def test_load_models(temp_models_file):
    """Test loading models from file."""
    models = load_models(temp_models_file)
    
    assert isinstance(models, dict)
    assert len(models) > 0
    assert 'EXCHANGE1' in models
    assert 'EXCHANGE2' in models


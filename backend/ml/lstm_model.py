"""
LSTM Model for Stock Price Prediction
Time-series forecasting using deep learning
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.preprocessing import MinMaxScaler
import pickle
import os

# Optional TensorFlow import (will use fallback if not available)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("TensorFlow not available, using fallback prediction")

class LSTMPredictor:
    """
    LSTM-based stock price predictor
    """
    
    def __init__(
        self, 
        sequence_length: int = 60,
        units: int = 50,
        dropout: float = 0.2
    ):
        self.sequence_length = sequence_length
        self.units = units
        self.dropout = dropout
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_trained = False
    
    def _build_model(self, input_shape: Tuple[int, int]):
        """Build LSTM model architecture"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        model = Sequential([
            LSTM(self.units, return_sequences=True, input_shape=input_shape),
            Dropout(self.dropout),
            LSTM(self.units, return_sequences=True),
            Dropout(self.dropout),
            LSTM(self.units),
            Dropout(self.dropout),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def _prepare_data(
        self, 
        data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length:i, 0])
            y.append(data[i, 0])
        
        return np.array(X), np.array(y)
    
    def train(
        self, 
        prices: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train the LSTM model on historical prices
        """
        if not TENSORFLOW_AVAILABLE:
            return {"status": "skipped", "reason": "TensorFlow not available"}
        
        # Scale data
        scaled_data = self.scaler.fit_transform(prices.reshape(-1, 1))
        
        # Prepare sequences
        X, y = self._prepare_data(scaled_data)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Build model
        self.model = self._build_model((X.shape[1], 1))
        
        # Train with early stopping
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0
        )
        
        self.is_trained = True
        
        return {
            "status": "success",
            "epochs_trained": len(history.history['loss']),
            "final_loss": float(history.history['loss'][-1]),
            "final_val_loss": float(history.history['val_loss'][-1])
        }
    
    def predict(
        self, 
        prices: np.ndarray,
        days_ahead: int = 5
    ) -> Dict[str, Any]:
        """
        Predict future prices
        """
        if not TENSORFLOW_AVAILABLE or not self.is_trained:
            return self._fallback_predict(prices, days_ahead)
        
        # Scale data
        scaled_data = self.scaler.transform(prices.reshape(-1, 1))
        
        predictions = []
        current_sequence = scaled_data[-self.sequence_length:].flatten()
        
        for _ in range(days_ahead):
            # Reshape for prediction
            X = current_sequence.reshape(1, self.sequence_length, 1)
            
            # Predict next value
            pred_scaled = self.model.predict(X, verbose=0)[0, 0]
            pred_price = self.scaler.inverse_transform([[pred_scaled]])[0, 0]
            
            predictions.append(round(float(pred_price), 2))
            
            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred_scaled)
        
        return {
            "method": "lstm",
            "predictions": predictions,
            "currentPrice": float(prices[-1]),
            "daysAhead": days_ahead
        }
    
    def _fallback_predict(
        self, 
        prices: np.ndarray,
        days_ahead: int
    ) -> Dict[str, Any]:
        """
        Fallback prediction using simple linear regression
        """
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        
        predictions = []
        for i in range(1, days_ahead + 1):
            pred = slope * (len(prices) + i) + intercept
            predictions.append(round(float(pred), 2))
        
        return {
            "method": "linear_fallback",
            "predictions": predictions,
            "currentPrice": float(prices[-1]),
            "daysAhead": days_ahead
        }
    
    def save(self, path: str):
        """Save model to disk"""
        if self.model:
            self.model.save(f"{path}/lstm_model.h5")
            with open(f"{path}/scaler.pkl", 'wb') as f:
                pickle.dump(self.scaler, f)
    
    def load(self, path: str) -> bool:
        """Load model from disk"""
        try:
            if TENSORFLOW_AVAILABLE:
                self.model = load_model(f"{path}/lstm_model.h5")
                with open(f"{path}/scaler.pkl", 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                return True
        except:
            pass
        return False

# Global predictor instance
_predictor = LSTMPredictor()

def predict_prices(
    prices: List[float],
    days_ahead: int = 5,
    train_if_needed: bool = True
) -> Dict[str, Any]:
    """
    Predict future prices using LSTM
    
    Args:
        prices: List of historical closing prices
        days_ahead: Number of days to predict
        train_if_needed: Train model if not already trained
    """
    prices_array = np.array(prices)
    
    # Train if needed and enough data
    if train_if_needed and not _predictor.is_trained and len(prices) >= 100:
        _predictor.train(prices_array, epochs=25)
    
    return _predictor.predict(prices_array, days_ahead)

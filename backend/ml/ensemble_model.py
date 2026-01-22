"""
Ensemble Model for Stock Forecasting
Combines technical analysis signals with ML predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle

class EnsembleForecaster:
    """
    Ensemble model combining:
    - Random Forest for direction prediction (up/down)
    - Gradient Boosting for magnitude prediction
    - Technical analysis signals
    """
    
    def __init__(self):
        self.direction_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.magnitude_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for ML model
        """
        features = []
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Price-based features
        returns = close.pct_change().fillna(0)
        
        # Moving averages
        sma5 = close.rolling(5).mean() / close
        sma10 = close.rolling(10).mean() / close
        sma20 = close.rolling(20).mean() / close
        
        # Volatility
        volatility = returns.rolling(10).std()
        
        # RSI approximation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Volume features
        volume_sma = volume.rolling(10).mean()
        volume_ratio = volume / (volume_sma + 1e-10)
        
        # Combine features
        feature_df = pd.DataFrame({
            'returns': returns,
            'sma5_ratio': sma5,
            'sma10_ratio': sma10,
            'sma20_ratio': sma20,
            'volatility': volatility,
            'rsi': rsi / 100,
            'volume_ratio': volume_ratio,
            'high_low_ratio': (high - low) / close,
            'close_position': (close - low) / (high - low + 1e-10)
        }).fillna(0)
        
        return feature_df.values
    
    def train(
        self, 
        df: pd.DataFrame,
        lookforward: int = 5
    ) -> Dict[str, Any]:
        """
        Train ensemble models on historical data
        """
        if len(df) < 100:
            return {"status": "error", "reason": "Insufficient data (need 100+ rows)"}
        
        # Extract features
        features = self._extract_features(df)
        
        # Create labels
        future_returns = df['Close'].pct_change(lookforward).shift(-lookforward)
        direction = (future_returns > 0).astype(int).values
        magnitude = future_returns.values
        
        # Remove NaN rows
        valid_idx = ~(np.isnan(features).any(axis=1) | np.isnan(direction) | np.isnan(magnitude))
        
        X = features[valid_idx]
        y_dir = direction[valid_idx]
        y_mag = magnitude[valid_idx]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train models
        self.direction_model.fit(X_scaled, y_dir)
        self.magnitude_model.fit(X_scaled, y_mag)
        
        self.is_trained = True
        
        return {
            "status": "success",
            "samples_trained": len(X),
            "direction_accuracy": round(self.direction_model.score(X_scaled, y_dir), 4)
        }
    
    def predict(
        self, 
        df: pd.DataFrame,
        ta_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make predictions using ensemble
        """
        if not self.is_trained:
            return self._rule_based_predict(df, ta_signals)
        
        # Extract features for latest data point
        features = self._extract_features(df)
        X = features[-1:].reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Get predictions
        direction_prob = self.direction_model.predict_proba(X_scaled)[0]
        magnitude = self.magnitude_model.predict(X_scaled)[0]
        
        current_price = df['Close'].iloc[-1]
        predicted_price = current_price * (1 + magnitude)
        
        # Combine with TA signals
        ta_confidence = 0.5
        if ta_signals and 'overall' in ta_signals.get('signals', {}):
            overall = ta_signals['signals']['overall']
            if overall['signal'] == 'buy':
                ta_confidence = 0.5 + overall['strength'] * 0.3
            elif overall['signal'] == 'sell':
                ta_confidence = 0.5 - overall['strength'] * 0.3
        
        # Ensemble confidence
        ml_confidence = max(direction_prob)
        combined_confidence = (ml_confidence * 0.6 + ta_confidence * 0.4)
        
        if direction_prob[1] > direction_prob[0]:
            signal = "bullish"
        else:
            signal = "bearish"
        
        return {
            "signal": signal,
            "confidence": round(combined_confidence, 3),
            "mlProbability": {
                "up": round(direction_prob[1], 3),
                "down": round(direction_prob[0], 3)
            },
            "predictedChange": round(magnitude * 100, 2),
            "predictedPrice": round(predicted_price, 2),
            "currentPrice": round(current_price, 2),
            "method": "ensemble"
        }
    
    def _rule_based_predict(
        self, 
        df: pd.DataFrame,
        ta_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fallback rule-based prediction when model is not trained
        """
        current_price = df['Close'].iloc[-1]
        
        # Simple momentum-based prediction
        returns = df['Close'].pct_change().tail(10).mean()
        
        if returns > 0.01:
            signal = "bullish"
            confidence = min(0.5 + returns * 10, 0.75)
        elif returns < -0.01:
            signal = "bearish"
            confidence = min(0.5 + abs(returns) * 10, 0.75)
        else:
            signal = "neutral"
            confidence = 0.5
        
        predicted_price = current_price * (1 + returns * 5)
        
        return {
            "signal": signal,
            "confidence": round(confidence, 3),
            "predictedChange": round(returns * 500, 2),
            "predictedPrice": round(predicted_price, 2),
            "currentPrice": round(current_price, 2),
            "method": "rule_based"
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from Random Forest
        """
        if not self.is_trained:
            return {}
        
        feature_names = [
            'returns', 'sma5_ratio', 'sma10_ratio', 'sma20_ratio',
            'volatility', 'rsi', 'volume_ratio', 'high_low_ratio', 'close_position'
        ]
        
        importance = dict(zip(
            feature_names,
            self.direction_model.feature_importances_
        ))
        
        return {k: round(v, 4) for k, v in sorted(
            importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )}

# Global forecaster instance
_forecaster = EnsembleForecaster()

def get_ensemble_forecast(
    df: pd.DataFrame,
    ta_signals: Optional[Dict[str, Any]] = None,
    train_if_needed: bool = True
) -> Dict[str, Any]:
    """
    Get ensemble forecast for a stock
    """
    if train_if_needed and not _forecaster.is_trained and len(df) >= 100:
        _forecaster.train(df)
    
    return _forecaster.predict(df, ta_signals)

"""
Stock Screener Service - Scans stocks and ranks by sentiment
"""

import yfinance as yf
import json
import os
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from cachetools import TTLCache

from analysis.technical_indicators import get_all_indicators
from ml.ensemble_model import get_ensemble_forecast

# Cache scan results for 5 minutes
_scan_cache = TTLCache(maxsize=1, ttl=300)

# Load IDX stocks list
STOCKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'idx_stocks.json')

def _load_all_stocks() -> List[Dict]:
    """Load all IDX stocks from JSON file"""
    try:
        with open(STOCKS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def _analyze_single_stock(stock_info: Dict) -> Dict[str, Any]:
    """
    Analyze a single stock quickly (no news/commodity - speed is priority).
    Returns sentiment score, signal, confidence, price info.
    """
    symbol = stock_info["symbol"]
    name = stock_info.get("name", symbol)
    sector = stock_info.get("sector", "")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 14:
            return None
        
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        # Get technical indicators
        indicators = get_all_indicators(df)
        
        # Get ML ensemble forecast (fast, no training)
        ml_forecast = get_ensemble_forecast(df, indicators, train_if_needed=False)
        
        signal = ml_forecast.get("signal", "neutral")
        confidence = ml_forecast.get("confidence", 0.5)
        predicted_change = ml_forecast.get("predictedChange", 0)
        
        # Get technical signals
        signals = indicators.get("signals", {})
        overall_signal = signals.get("overall", {})
        ta_signal = overall_signal.get("signal", "neutral")
        ta_strength = overall_signal.get("strength", 0)
        
        # Calculate Sentiment Score (0-100)
        # Based on: ML signal, TA signal, confidence, predicted change, price momentum
        sentiment_score = 50  # Neutral base
        
        # ML signal contribution (±20)
        if signal == "bullish":
            sentiment_score += 20
        elif signal == "bearish":
            sentiment_score -= 20
        
        # TA signal contribution (±15)
        if ta_signal == "bullish":
            sentiment_score += 15
        elif ta_signal == "bearish":
            sentiment_score -= 15
        
        # Confidence contribution (±10)
        sentiment_score += (confidence - 0.5) * 20
        
        # Predicted change contribution (±10, capped)
        sentiment_score += max(-10, min(10, predicted_change * 2))
        
        # Price momentum (today's change, ±5)
        sentiment_score += max(-5, min(5, change_pct))
        
        # Clamp to 0-100
        sentiment_score = max(0, min(100, sentiment_score))
        
        # Individual signal details
        rsi_signal = signals.get("rsi", {}).get("signal", "neutral")
        macd_signal = signals.get("macd", {}).get("signal", "neutral")
        
        return {
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePct": round(change_pct, 2),
            "signal": signal,
            "taSignal": ta_signal,
            "confidence": round(confidence, 3),
            "sentimentScore": round(sentiment_score, 1),
            "predictedChange": round(predicted_change, 2),
            "rsi": rsi_signal,
            "macd": macd_signal
        }
        
    except Exception as e:
        return None


def scan_all_stocks(max_workers: int = 5) -> Dict[str, Any]:
    """
    Scan all IDX stocks and return ranked by sentiment score.
    Uses thread pool for parallel processing.
    Results cached for 5 minutes.
    """
    cache_key = "scan_result"
    
    if cache_key in _scan_cache:
        return _scan_cache[cache_key]
    
    stocks = _load_all_stocks()
    if not stocks:
        return {"stocks": [], "total": 0, "scanTime": 0}
    
    start_time = time.time()
    results = []
    failed = 0
    
    # Scan in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_analyze_single_stock, s): s for s in stocks}
        
        for future in as_completed(futures):
            try:
                result = future.result(timeout=30)
                if result:
                    results.append(result)
                else:
                    failed += 1
            except Exception:
                failed += 1
    
    # Sort by sentiment score (highest = most bullish first)
    results.sort(key=lambda x: x["sentimentScore"], reverse=True)
    
    scan_time = round(time.time() - start_time, 1)
    
    response = {
        "stocks": results,
        "total": len(results),
        "failed": failed,
        "scanTime": scan_time
    }
    
    _scan_cache[cache_key] = response
    return response

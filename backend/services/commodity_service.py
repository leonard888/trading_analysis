"""
Commodities Service - Fetches commodity prices (gold, oil, silver)
"""

import yfinance as yf
from typing import Dict, Any, List
from cachetools import TTLCache

# Cache commodity data for 5 minutes
_cache = TTLCache(maxsize=50, ttl=300)

# Commodity symbols
COMMODITIES = {
    "gold": {
        "symbol": "GC=F",
        "name": "Gold Futures",
        "unit": "USD/oz"
    },
    "silver": {
        "symbol": "SI=F", 
        "name": "Silver Futures",
        "unit": "USD/oz"
    },
    "oil": {
        "symbol": "CL=F",
        "name": "Crude Oil WTI Futures",
        "unit": "USD/barrel"
    },
    "brent": {
        "symbol": "BZ=F",
        "name": "Brent Crude Oil Futures",
        "unit": "USD/barrel"
    },
    "copper": {
        "symbol": "HG=F",
        "name": "Copper Futures",
        "unit": "USD/lb"
    },
    "platinum": {
        "symbol": "PL=F",
        "name": "Platinum Futures",
        "unit": "USD/oz"
    },
    "palladium": {
        "symbol": "PA=F",
        "name": "Palladium Futures",
        "unit": "USD/oz"
    },
    "natural_gas": {
        "symbol": "NG=F",
        "name": "Natural Gas Futures",
        "unit": "USD/MMBtu"
    },
    "coal": {
        "symbol": "MTF=F",
        "name": "Coal Futures",
        "unit": "USD/ton"
    },
    "nickel": {
        "symbol": "^SPGSNI",
        "name": "Nickel Index",
        "unit": "Index"
    }
}

def get_commodity_data(
    commodity_type: str,
    period: str = "1mo",
    interval: str = "1d"
) -> Dict[str, Any]:
    """
    Get commodity price data
    
    Args:
        commodity_type: Type of commodity (gold, silver, oil, etc.)
        period: Data period
        interval: Data interval
    """
    cache_key = f"{commodity_type}_{period}_{interval}"
    
    if cache_key in _cache:
        return _cache[cache_key]
    
    commodity = COMMODITIES.get(commodity_type.lower())
    if not commodity:
        return {"error": f"Unknown commodity: {commodity_type}"}
    
    try:
        ticker = yf.Ticker(commodity["symbol"])
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": f"No data found for {commodity_type}"}
        
        info = ticker.info
        current_price = hist["Close"].iloc[-1] if not hist.empty else None
        prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
        
        data = {
            "type": commodity_type,
            "symbol": commodity["symbol"],
            "name": commodity["name"],
            "unit": commodity["unit"],
            "currentPrice": round(current_price, 2) if current_price else None,
            "previousClose": round(prev_close, 2) if prev_close else None,
            "change": round(current_price - prev_close, 2) if current_price and prev_close else None,
            "changePercent": round((current_price - prev_close) / prev_close * 100, 2) if current_price and prev_close else None,
            "dayHigh": round(hist["High"].iloc[-1], 2) if not hist.empty else None,
            "dayLow": round(hist["Low"].iloc[-1], 2) if not hist.empty else None,
            "history": []
        }
        
        # Add historical data
        for idx, row in hist.iterrows():
                # Use string format for daily/weekly/monthly data to avoid timezone shifting
                if interval[-1] in ['d', 'k', 'o', 'y']:  # 1d, 5d, 1wk, 1mo, etc.
                    time_val = idx.strftime('%Y-%m-%d')
                else:
                    time_val = int(idx.timestamp())

                data["history"].append({
                    "time": time_val,
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]) if row["Volume"] else 0
                })
        
        _cache[cache_key] = data
        return data
        
    except Exception as e:
        return {"error": str(e), "type": commodity_type}

def get_all_commodities() -> List[Dict[str, Any]]:
    """
    Get current prices for all commodities
    """
    results = []
    for commodity_type, info in COMMODITIES.items():
        data = get_commodity_data(commodity_type, period="1d")
        if "error" not in data:
            results.append({
                "type": commodity_type,
                "name": info["name"],
                "unit": info["unit"],
                "price": data.get("currentPrice"),
                "change": data.get("change"),
                "changePercent": data.get("changePercent")
            })
    return results

def get_available_commodities() -> List[Dict[str, str]]:
    """
    Get list of available commodity types
    """
    return [
        {"type": k, "name": v["name"], "unit": v["unit"]}
        for k, v in COMMODITIES.items()
    ]


def get_commodity_forecast(commodity_type: str) -> Dict[str, Any]:
    """
    Get commodity forecast with price predictions and support/resistance
    
    Args:
        commodity_type: Type of commodity (gold, silver, oil, etc.)
    
    Returns:
        Forecast with bullish/bearish price targets and S/R levels
    """
    from analysis.support_resistance import calculate_support_resistance
    from ml.ensemble_model import get_ensemble_forecast
    from analysis.technical_indicators import get_all_indicators
    from analysis.pattern_detection import detect_all_patterns
    from services.forecast_service import calculate_validity
    
    commodity = COMMODITIES.get(commodity_type.lower())
    if not commodity:
        return {"error": f"Unknown commodity: {commodity_type}"}
    
    try:
        ticker = yf.Ticker(commodity["symbol"])
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 20:
            return {"error": f"Insufficient data for {commodity_type}"}
        
        current_price = df['Close'].iloc[-1]
        
        # Get technical indicators
        indicators = get_all_indicators(df)
        
        # Get ML forecast
        ml_forecast = get_ensemble_forecast(df, indicators, train_if_needed=False)
        predicted_change = ml_forecast.get("predictedChange", 0)
        forecast_signal = ml_forecast.get("signal", "neutral")
        confidence = ml_forecast.get("confidence", 0.5)
        
        # Calculate support/resistance
        sr_levels = calculate_support_resistance(df)
        
        # Detect patterns
        patterns = detect_all_patterns(df)
        
        # Calculate dynamic validity
        # Commodities don't rely heavily on news sentiment in this implementation yet, passing None
        validity = calculate_validity(df, indicators, None, sr_levels)
        
        # Calculate price targets based on forecast
        bullish_target = current_price * (1 + abs(predicted_change) / 100)
        bearish_target = current_price * (1 - abs(predicted_change) / 100)
        
        # Use S/R levels for more realistic targets
        if forecast_signal == "bullish":
            primary_target = min(bullish_target, sr_levels.get("r1", bullish_target))
            extended_target = sr_levels.get("r2", bullish_target * 1.05)
        else:
            primary_target = max(bearish_target, sr_levels.get("s1", bearish_target))
            extended_target = sr_levels.get("s2", bearish_target * 0.95)
        
        result = {
            "type": commodity_type,
            "symbol": commodity["symbol"],
            "name": commodity["name"],
            "unit": commodity["unit"],
            "currentPrice": round(current_price, 2),
            "forecast": {
                "signal": forecast_signal,
                "confidence": round(confidence, 3),
                "validity": validity,
                "predictedChange": round(predicted_change, 2),
                "bullishTarget": round(bullish_target, 2),
                "bearishTarget": round(bearish_target, 2),
                "primaryTarget": round(primary_target, 2),
                "extendedTarget": round(extended_target, 2)
            },
            "supportResistance": {
                "pivot": sr_levels.get("pivot"),
                "s1": sr_levels.get("s1"),
                "s2": sr_levels.get("s2"),
                "r1": sr_levels.get("r1"),
                "r2": sr_levels.get("r2")
            },
            "technicalSignals": indicators.get("signals", {}),
            "indicators": indicators,
            "patterns": patterns
        }
        
        print(f"DEBUG REFURNING KEYS: {list(result.keys())}")
        return result
        
        
    except Exception as e:
        return {"error": str(e), "type": commodity_type}

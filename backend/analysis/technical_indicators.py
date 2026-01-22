"""
Technical Indicators Module
RSI, MACD, SMA/EMA, Bollinger Bands, Volume Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (RSI)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(
    data: pd.Series, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9
) -> Dict[str, pd.Series]:
    """
    Moving Average Convergence Divergence (MACD)
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }

def calculate_bollinger_bands(
    data: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    Bollinger Bands
    """
    sma = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return {
        "upper": upper,
        "middle": sma,
        "lower": lower,
        "bandwidth": (upper - lower) / sma * 100
    }

def calculate_stochastic(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    k_period: int = 14, 
    d_period: int = 3
) -> Dict[str, pd.Series]:
    """
    Stochastic Oscillator
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    
    return {"k": k, "d": d}

def calculate_atr(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    period: int = 14
) -> pd.Series:
    """
    Average True Range (ATR)
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume (OBV)
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv

def calculate_vwap(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    volume: pd.Series
) -> pd.Series:
    """
    Volume Weighted Average Price (VWAP)
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def get_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all technical indicators for a dataframe
    
    Args:
        df: DataFrame with columns: Open, High, Low, Close, Volume
    
    Returns:
        Dictionary with all indicator values
    """
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # Calculate indicators
    rsi = calculate_rsi(close)
    macd = calculate_macd(close)
    bb = calculate_bollinger_bands(close)
    stoch = calculate_stochastic(high, low, close)
    atr = calculate_atr(high, low, close)
    obv = calculate_obv(close, volume)
    
    # Get latest values
    latest = {
        "sma20": round(calculate_sma(close, 20).iloc[-1], 2),
        "sma50": round(calculate_sma(close, 50).iloc[-1], 2),
        "sma200": round(calculate_sma(close, 200).iloc[-1], 2) if len(close) >= 200 else None,
        "ema12": round(calculate_ema(close, 12).iloc[-1], 2),
        "ema26": round(calculate_ema(close, 26).iloc[-1], 2),
        "rsi": round(rsi.iloc[-1], 2),
        "macd": {
            "value": round(macd["macd"].iloc[-1], 4),
            "signal": round(macd["signal"].iloc[-1], 4),
            "histogram": round(macd["histogram"].iloc[-1], 4)
        },
        "bollingerBands": {
            "upper": round(bb["upper"].iloc[-1], 2),
            "middle": round(bb["middle"].iloc[-1], 2),
            "lower": round(bb["lower"].iloc[-1], 2),
            "bandwidth": round(bb["bandwidth"].iloc[-1], 2)
        },
        "stochastic": {
            "k": round(stoch["k"].iloc[-1], 2),
            "d": round(stoch["d"].iloc[-1], 2)
        },
        "atr": round(atr.iloc[-1], 2),
        "obv": int(obv.iloc[-1]),
        "currentPrice": round(close.iloc[-1], 2)
    }
    
    # Generate signals
    signals = generate_signals(latest, close)
    latest["signals"] = signals
    
    return latest

def generate_signals(indicators: Dict[str, Any], close: pd.Series) -> Dict[str, Any]:
    """
    Generate buy/sell signals based on indicators
    """
    signals = {
        "rsi": {"signal": "neutral", "strength": 0},
        "macd": {"signal": "neutral", "strength": 0},
        "bollingerBands": {"signal": "neutral", "strength": 0},
        "movingAverages": {"signal": "neutral", "strength": 0},
        "stochastic": {"signal": "neutral", "strength": 0},
        "overall": {"signal": "neutral", "strength": 0}
    }
    
    current_price = close.iloc[-1]
    
    # RSI signals
    rsi = indicators["rsi"]
    if rsi < 30:
        signals["rsi"] = {"signal": "buy", "strength": (30 - rsi) / 30}
    elif rsi > 70:
        signals["rsi"] = {"signal": "sell", "strength": (rsi - 70) / 30}
    
    # MACD signals
    macd = indicators["macd"]
    if macd["histogram"] > 0 and macd["value"] > macd["signal"]:
        signals["macd"] = {"signal": "buy", "strength": min(abs(macd["histogram"]) * 10, 1)}
    elif macd["histogram"] < 0 and macd["value"] < macd["signal"]:
        signals["macd"] = {"signal": "sell", "strength": min(abs(macd["histogram"]) * 10, 1)}
    
    # Bollinger Bands signals
    bb = indicators["bollingerBands"]
    if current_price < bb["lower"]:
        signals["bollingerBands"] = {"signal": "buy", "strength": 0.8}
    elif current_price > bb["upper"]:
        signals["bollingerBands"] = {"signal": "sell", "strength": 0.8}
    
    # Moving averages signals
    sma20 = indicators["sma20"]
    sma50 = indicators["sma50"]
    if current_price > sma20 > sma50:
        signals["movingAverages"] = {"signal": "buy", "strength": 0.6}
    elif current_price < sma20 < sma50:
        signals["movingAverages"] = {"signal": "sell", "strength": 0.6}
    
    # Stochastic signals
    stoch = indicators["stochastic"]
    if stoch["k"] < 20 and stoch["d"] < 20:
        signals["stochastic"] = {"signal": "buy", "strength": 0.7}
    elif stoch["k"] > 80 and stoch["d"] > 80:
        signals["stochastic"] = {"signal": "sell", "strength": 0.7}
    
    # Calculate overall signal
    buy_score = sum(
        s["strength"] for s in signals.values() 
        if isinstance(s, dict) and s.get("signal") == "buy"
    )
    sell_score = sum(
        s["strength"] for s in signals.values() 
        if isinstance(s, dict) and s.get("signal") == "sell"
    )
    
    if buy_score > sell_score + 0.5:
        signals["overall"] = {"signal": "buy", "strength": min(buy_score / 3, 1)}
    elif sell_score > buy_score + 0.5:
        signals["overall"] = {"signal": "sell", "strength": min(sell_score / 3, 1)}
    
    return signals

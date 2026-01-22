"""
Chart Pattern Detection Module
Detects common chart patterns for technical analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.signal import argrelextrema

def find_local_extrema(
    data: pd.Series, 
    order: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Find local maxima and minima in data
    """
    maxima_idx = argrelextrema(data.values, np.greater, order=order)[0]
    minima_idx = argrelextrema(data.values, np.less, order=order)[0]
    return maxima_idx, minima_idx

def calculate_support_resistance(
    df: pd.DataFrame, 
    window: int = 20,
    num_levels: int = 3
) -> Dict[str, List[float]]:
    """
    Calculate support and resistance levels
    """
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    
    # Find pivot points
    max_idx, min_idx = find_local_extrema(pd.Series(closes), order=window//2)
    
    resistance_levels = []
    support_levels = []
    
    if len(max_idx) > 0:
        resistance_prices = highs[max_idx]
        # Cluster similar levels
        resistance_levels = cluster_price_levels(resistance_prices, num_levels)
    
    if len(min_idx) > 0:
        support_prices = lows[min_idx]
        support_levels = cluster_price_levels(support_prices, num_levels)
    
    return {
        "resistance": resistance_levels,
        "support": support_levels
    }

def cluster_price_levels(prices: np.ndarray, num_clusters: int) -> List[float]:
    """
    Cluster similar price levels together
    """
    if len(prices) == 0:
        return []
    
    prices = sorted(prices, reverse=True)
    
    # Simple clustering by proximity
    clusters = []
    current_cluster = [prices[0]]
    threshold = np.mean(prices) * 0.02  # 2% threshold
    
    for price in prices[1:]:
        if abs(price - np.mean(current_cluster)) < threshold:
            current_cluster.append(price)
        else:
            clusters.append(np.mean(current_cluster))
            current_cluster = [price]
    
    clusters.append(np.mean(current_cluster))
    
    return [round(c, 2) for c in clusters[:num_clusters]]

def detect_head_and_shoulders(
    df: pd.DataFrame,
    lookback: int = 50
) -> Optional[Dict[str, Any]]:
    """
    Detect Head and Shoulders pattern
    """
    if len(df) < lookback:
        return None
    
    recent = df.tail(lookback)
    highs = recent['High'].values
    closes = recent['Close'].values
    
    max_idx, _ = find_local_extrema(pd.Series(highs), order=5)
    
    if len(max_idx) < 3:
        return None
    
    # Look for three peaks where middle is highest
    for i in range(len(max_idx) - 2):
        left_shoulder = highs[max_idx[i]]
        head = highs[max_idx[i + 1]]
        right_shoulder = highs[max_idx[i + 2]]
        
        # Check pattern criteria
        if (head > left_shoulder * 1.02 and 
            head > right_shoulder * 1.02 and
            abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
            
            neckline = min(closes[max_idx[i]:max_idx[i + 2]])
            target = neckline - (head - neckline)
            
            return {
                "pattern": "head_and_shoulders",
                "type": "bearish",
                "confidence": 0.7,
                "leftShoulder": round(left_shoulder, 2),
                "head": round(head, 2),
                "rightShoulder": round(right_shoulder, 2),
                "neckline": round(neckline, 2),
                "target": round(target, 2)
            }
    
    return None

def detect_double_top_bottom(
    df: pd.DataFrame,
    lookback: int = 40
) -> Optional[Dict[str, Any]]:
    """
    Detect Double Top or Double Bottom patterns
    """
    if len(df) < lookback:
        return None
    
    recent = df.tail(lookback)
    highs = recent['High'].values
    lows = recent['Low'].values
    closes = recent['Close'].values
    
    max_idx, min_idx = find_local_extrema(pd.Series(closes), order=5)
    
    # Check for Double Top
    if len(max_idx) >= 2:
        peak1 = highs[max_idx[-2]]
        peak2 = highs[max_idx[-1]]
        
        if abs(peak1 - peak2) / peak1 < 0.03:  # Within 3%
            neckline = min(lows[max_idx[-2]:max_idx[-1]])
            target = neckline - (peak1 - neckline)
            
            return {
                "pattern": "double_top",
                "type": "bearish",
                "confidence": 0.65,
                "peak1": round(peak1, 2),
                "peak2": round(peak2, 2),
                "neckline": round(neckline, 2),
                "target": round(target, 2)
            }
    
    # Check for Double Bottom
    if len(min_idx) >= 2:
        trough1 = lows[min_idx[-2]]
        trough2 = lows[min_idx[-1]]
        
        if abs(trough1 - trough2) / trough1 < 0.03:  # Within 3%
            neckline = max(highs[min_idx[-2]:min_idx[-1]])
            target = neckline + (neckline - trough1)
            
            return {
                "pattern": "double_bottom",
                "type": "bullish",
                "confidence": 0.65,
                "trough1": round(trough1, 2),
                "trough2": round(trough2, 2),
                "neckline": round(neckline, 2),
                "target": round(target, 2)
            }
    
    return None

def detect_triangle(
    df: pd.DataFrame,
    lookback: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Detect Triangle patterns (ascending, descending, symmetrical)
    """
    if len(df) < lookback:
        return None
    
    recent = df.tail(lookback)
    highs = recent['High'].values
    lows = recent['Low'].values
    
    # Calculate trend lines
    x = np.arange(len(highs))
    
    # Upper trendline
    high_slope, high_intercept = np.polyfit(x, highs, 1)
    
    # Lower trendline
    low_slope, low_intercept = np.polyfit(x, lows, 1)
    
    # Determine triangle type
    if high_slope < -0.01 and abs(low_slope) < 0.01:
        pattern_type = "descending_triangle"
        bias = "bearish"
    elif low_slope > 0.01 and abs(high_slope) < 0.01:
        pattern_type = "ascending_triangle"
        bias = "bullish"
    elif high_slope < -0.01 and low_slope > 0.01:
        pattern_type = "symmetrical_triangle"
        bias = "neutral"
    else:
        return None
    
    current_price = recent['Close'].iloc[-1]
    apex_x = (low_intercept - high_intercept) / (high_slope - low_slope) if high_slope != low_slope else len(highs)
    
    return {
        "pattern": pattern_type,
        "type": bias,
        "confidence": 0.6,
        "upperSlope": round(high_slope, 4),
        "lowerSlope": round(low_slope, 4),
        "apex": round(apex_x),
        "currentPrice": round(current_price, 2)
    }

def detect_trend(
    df: pd.DataFrame,
    lookback: int = 20
) -> Dict[str, Any]:
    """
    Detect current trend direction and strength
    """
    if len(df) < lookback:
        return {"trend": "neutral", "strength": 0}
    
    recent = df.tail(lookback)
    closes = recent['Close'].values
    
    x = np.arange(len(closes))
    slope, _ = np.polyfit(x, closes, 1)
    
    # Normalize slope by price
    normalized_slope = slope / closes.mean() * 100
    
    if normalized_slope > 0.5:
        trend = "uptrend"
        strength = min(normalized_slope / 2, 1)
    elif normalized_slope < -0.5:
        trend = "downtrend"
        strength = min(abs(normalized_slope) / 2, 1)
    else:
        trend = "sideways"
        strength = 0.3
    
    return {
        "trend": trend,
        "strength": round(strength, 2),
        "slope": round(normalized_slope, 4)
    }

def detect_all_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run all pattern detection algorithms
    """
    patterns = {
        "detectedPatterns": [],
        "supportResistance": calculate_support_resistance(df),
        "trend": detect_trend(df)
    }
    
    # Check for specific patterns
    hs_pattern = detect_head_and_shoulders(df)
    if hs_pattern:
        patterns["detectedPatterns"].append(hs_pattern)
    
    dt_pattern = detect_double_top_bottom(df)
    if dt_pattern:
        patterns["detectedPatterns"].append(dt_pattern)
    
    triangle = detect_triangle(df)
    if triangle:
        patterns["detectedPatterns"].append(triangle)
    
    return patterns

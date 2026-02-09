"""
Support and Resistance Calculation
Uses Pivot Points and Local Extrema to find key levels
"""

import pandas as pd
import numpy as np

def round_to_idx_tick(price: float) -> float:
    """
    Round price to nearest valid IDX tick size.
    IDX Tick Size Rules:
    - Price < 200: tick = 1
    - Price 200-500: tick = 2
    - Price 500-2000: tick = 5
    - Price 2000-5000: tick = 10
    - Price >= 5000: tick = 25
    """
    if price <= 0:
        return 0
    
    if price < 200:
        tick = 1
    elif price < 500:
        tick = 2
    elif price < 2000:
        tick = 5
    elif price < 5000:
        tick = 10
    else:
        tick = 25
    
    return round(round(price / tick) * tick)

def calculate_support_resistance(df: pd.DataFrame, period: int = 20):
    """
    Calculate Support and Resistance using Pivot Points (Classic) and Rolling Min/Max
    """
    if df.empty:
        return {}

    # Get latest complete candle (previous day)
    last_candle = df.iloc[-1]
    high = last_candle['High']
    low = last_candle['Low']
    close = last_candle['Close']

    # 1. Classic Pivot Points
    pivot = (high + low + close) / 3
    
    # Resistance
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    # Support
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)

    # 2. Key Levels from recent price action (20-day high/low)
    recent_high = df['High'].tail(period).max()
    recent_low = df['Low'].tail(period).min()

    # Determine nearest meaningful levels to current price
    current_price = close
    
    # Filter and sort levels
    levels = sorted([s1, s2, s3, r1, r2, r3, recent_low, recent_high])
    
    # Find immediate support and resistance
    support_levels = [l for l in levels if l < current_price]
    resistance_levels = [l for l in levels if l > current_price]
    
    immediate_support = support_levels[-1] if support_levels else s1
    secondary_support = support_levels[-2] if len(support_levels) > 1 else s2
    
    immediate_resistance = resistance_levels[0] if resistance_levels else r1
    secondary_resistance = resistance_levels[1] if len(resistance_levels) > 1 else r2

    return {
        "pivot": round_to_idx_tick(pivot),
        "s1": round_to_idx_tick(immediate_support),
        "s2": round_to_idx_tick(secondary_support),
        "r1": round_to_idx_tick(immediate_resistance),
        "r2": round_to_idx_tick(secondary_resistance)
    }

def generate_trading_plan(current_price, signal, s1, s2, r1, r2):
    """
    Generate Buy/Sell targets based on S/R levels and signal
    """
    plan = {
        "action": "HOLD",
        "entry_zone": None,
        "take_profit": None,
        "stop_loss": None,
        "risk_reward": None
    }
    
    # Round current price to IDX tick
    current_price_tick = round_to_idx_tick(current_price)
    
    if signal == "bullish":
        plan["action"] = "BUY"
        # Entry near support or current price
        entry_low = round_to_idx_tick(s1)
        entry_high = current_price_tick
        plan["entry_zone"] = f"{entry_low} - {entry_high}"
        # Target R1 or R2
        plan["take_profit"] = round_to_idx_tick(r1) if r1 > current_price * 1.02 else round_to_idx_tick(r2)
        # Stop below S2
        plan["stop_loss"] = round_to_idx_tick(s2 * 0.99)
    
    elif signal == "bearish":
        plan["action"] = "WAIT TO BUY"
        # For bearish signal: wait for price to drop to support zone before buying
        # Entry zone should be at or below support levels (cheaper price)
        entry_low = round_to_idx_tick(s2)
        entry_high = round_to_idx_tick(s1)
        plan["entry_zone"] = f"{entry_low} - {entry_high}"
        # Take profit at pivot or R1 (above entry zone)
        plan["take_profit"] = round_to_idx_tick(r1)
        # Stop loss below S2
        plan["stop_loss"] = round_to_idx_tick(s2 * 0.97)
        
    # Calculate Risk/Reward
    if plan["take_profit"] and plan["stop_loss"]:
        risk = abs(current_price - plan["stop_loss"])
        reward = abs(plan["take_profit"] - current_price)
        if risk > 0:
            plan["risk_reward"] = round(reward / risk, 2)
            
    return plan

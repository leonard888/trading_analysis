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


def _round_price(price: float, is_commodity: bool = False) -> float:
    """
    Round price based on asset type.
    - IDX stocks: use IDX tick size rules
    - Commodities: round to 2 decimal places for accuracy
    """
    if is_commodity:
        return round(price, 2)
    return round_to_idx_tick(price)


def calculate_support_resistance(df: pd.DataFrame, period: int = 20, is_commodity: bool = False):
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
        "pivot": _round_price(pivot, is_commodity),
        "s1": _round_price(immediate_support, is_commodity),
        "s2": _round_price(secondary_support, is_commodity),
        "r1": _round_price(immediate_resistance, is_commodity),
        "r2": _round_price(secondary_resistance, is_commodity)
    }

def generate_trading_plan(current_price, signal, s1, s2, r1, r2, is_commodity: bool = False):
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
    
    # Round current price
    current_price_tick = _round_price(current_price, is_commodity)
    
    if signal == "bullish":
        plan["action"] = "BUY"
        # Entry near support or current price
        entry_low = _round_price(s1, is_commodity)
        entry_high = current_price_tick
        plan["entry_zone"] = f"{entry_low} - {entry_high}"
        # Target R1 or R2
        plan["take_profit"] = _round_price(r1, is_commodity) if r1 > current_price * 1.02 else _round_price(r2, is_commodity)
        # Stop below S2
        plan["stop_loss"] = _round_price(s2 * 0.99, is_commodity)
    
    elif signal == "bearish":
        plan["action"] = "WAIT TO BUY"
        # For bearish signal: wait for price to drop to support zone before buying
        entry_low = _round_price(s2, is_commodity)
        entry_high = _round_price(s1, is_commodity)
        plan["entry_zone"] = f"{entry_low} - {entry_high}"
        # Take profit at pivot or R1
        plan["take_profit"] = _round_price(r1, is_commodity)
        # Stop loss below S2
        plan["stop_loss"] = _round_price(s2 * 0.97, is_commodity)
        
    # Calculate Risk/Reward
    if plan["take_profit"] and plan["stop_loss"]:
        risk = abs(current_price - plan["stop_loss"])
        reward = abs(plan["take_profit"] - current_price)
        if risk > 0:
            plan["risk_reward"] = round(reward / risk, 2)
            
    return plan

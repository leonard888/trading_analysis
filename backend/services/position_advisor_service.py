"""
Position Advisor Service
ML-powered position analysis and action recommendations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime

from services.stock_service import get_stock_data
from services.forecast_service import generate_forecast_reasons, STOCK_COMMODITY_MAP
from analysis.support_resistance import calculate_support_resistance
from analysis.technical_indicators import get_all_indicators
from ml.ensemble_model import get_ensemble_forecast


# IDX lot size (1 lot = 100 shares)
IDX_LOT_SIZE = 100


# IDX Tick Size Rules (Fraksi Harga)
def get_idx_tick_size(price: float) -> int:
    """Get the tick size for a given IDX stock price"""
    if price < 200:
        return 1
    elif price < 500:
        return 2
    elif price < 2000:
        return 5
    elif price < 5000:
        return 10
    else:
        return 25


def round_to_tick(price: float, tick_size: int = None) -> float:
    """Round price to valid IDX tick size"""
    if tick_size is None:
        tick_size = get_idx_tick_size(price)
    return round(price / tick_size) * tick_size


def analyze_position(
    symbol: str,
    avg_price: float,
    quantity: int,
    remaining_balance: float = 0
) -> Dict[str, Any]:
    """
    Analyze a stock position and provide action recommendation
    
    Args:
        symbol: Stock symbol (e.g., BBCA.JK)
        avg_price: User's average purchase price
        quantity: Number of shares held
        remaining_balance: Remaining cash in IDR for potential averaging
    
    Returns:
        Dictionary with recommendation, reasoning, and details
    """
    
    # Ensure symbol has .JK suffix
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        # Fetch stock data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty:
            return {"error": f"No data found for {symbol}"}
        
        info = ticker.info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or df['Close'].iloc[-1]
        
        # Calculate P/L (quantity is in lots, convert to shares for calculation)
        shares = quantity * IDX_LOT_SIZE
        position_value = current_price * shares
        cost_basis = avg_price * shares
        pnl = position_value - cost_basis
        pnl_percent = ((current_price - avg_price) / avg_price) * 100
        
        # Get technical analysis
        indicators = get_all_indicators(df)
        sr_levels = calculate_support_resistance(df)
        
        # Get ML forecast
        ml_forecast = get_ensemble_forecast(df)
        predicted_change = ml_forecast.get("predictedChange", 0)
        forecast_signal = ml_forecast.get("signal", "neutral")
        confidence = ml_forecast.get("confidence", 0.5)
        
        # Calculate target price from forecast
        target_price = current_price * (1 + predicted_change / 100)
        target_price = round_to_tick(target_price)
        
        # Decision logic
        action, reasons = _determine_action(
            current_price=current_price,
            avg_price=avg_price,
            pnl_percent=pnl_percent,
            forecast_signal=forecast_signal,
            predicted_change=predicted_change,
            confidence=confidence,
            sr_levels=sr_levels,
            remaining_balance=remaining_balance,
            indicators=indicators
        )
        
        # Calculate potential actions (in lots)
        tick_size = get_idx_tick_size(current_price)
        potential_shares = int(remaining_balance / current_price)
        potential_lots = potential_shares // IDX_LOT_SIZE  # Round down to whole lots
        
        # New average if averaging down/up
        if potential_lots > 0:
            additional_shares = potential_lots * IDX_LOT_SIZE
            new_total_shares = shares + additional_shares
            new_avg_price = ((avg_price * shares) + (current_price * additional_shares)) / new_total_shares
            new_avg_price = round_to_tick(new_avg_price)
        else:
            new_avg_price = None
        
        return {
            "symbol": symbol,
            "action": action,
            "confidence": round(confidence, 3),
            "reasons": reasons,
            "position": {
                "avgPrice": round(avg_price, 2),
                "quantity": quantity,
                "currentPrice": round(current_price, 2),
                "positionValue": round(position_value, 2),
                "costBasis": round(cost_basis, 2),
                "pnl": round(pnl, 2),
                "pnlPercent": round(pnl_percent, 2)
            },
            "targets": {
                "targetPrice": round(target_price, 2),
                "predictedChange": round(predicted_change, 2),
                "stopLoss": round_to_tick(avg_price * 0.92),  # 8% cut loss
                "support1": sr_levels.get("s1"),
                "support2": sr_levels.get("s2"),
                "resistance1": sr_levels.get("r1"),
                "resistance2": sr_levels.get("r2")
            },
            "averaging": {
                "remainingBalance": remaining_balance,
                "potentialLots": potential_lots,
                "potentialShares": potential_lots * IDX_LOT_SIZE,
                "newAvgPrice": new_avg_price,
                "tickSize": tick_size,
                "lotSize": IDX_LOT_SIZE
            },
            "entryAdvisor": _calculate_entry_advice(
                current_price=current_price,
                avg_price=avg_price,
                action=action,
                sr_levels=sr_levels,
                forecast_signal=forecast_signal,
                predicted_change=predicted_change
            ),
            "forecast": {
                "signal": forecast_signal,
                "predictedChange": predicted_change,
                "method": ml_forecast.get("method", "unknown")
            }
        }
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _determine_action(
    current_price: float,
    avg_price: float,
    pnl_percent: float,
    forecast_signal: str,
    predicted_change: float,
    confidence: float,
    sr_levels: Dict[str, float],
    remaining_balance: float,
    indicators: Dict[str, Any]
) -> tuple[str, list[str]]:
    """
    Determine recommended action based on all factors
    
    Returns:
        Tuple of (action, list of reasons)
    """
    reasons = []
    
    # Get support/resistance levels
    s1 = sr_levels.get("s1", 0)
    s2 = sr_levels.get("s2", 0)
    r1 = sr_levels.get("r1", float('inf'))
    r2 = sr_levels.get("r2", float('inf'))
    
    # RSI analysis
    rsi = indicators.get("rsi", 50)
    
    # --- CUT LOSS: 8% or more loss with bearish outlook ---
    if pnl_percent <= -8:
        if forecast_signal == "bearish" or confidence < 0.4:
            reasons.append(f"Position is down {abs(pnl_percent):.1f}% (≥8% threshold)")
            reasons.append(f"Forecast is {forecast_signal} with {confidence*100:.0f}% confidence")
            if current_price < s1:
                reasons.append(f"Price broke below support at {s1}")
            return "CUT_LOSS", reasons
        else:
            # Loss but bullish forecast - consider holding or averaging
            reasons.append(f"Position is down {abs(pnl_percent):.1f}% but forecast is bullish")
    
    # --- TAKE PROFIT: Dynamic based on forecast ---
    if pnl_percent > 0 and predicted_change < 0:
        # In profit and forecast predicts decline
        reasons.append(f"Position is up {pnl_percent:.1f}%")
        reasons.append(f"Forecast predicts {predicted_change:.1f}% change (decline)")
        if current_price >= r1:
            reasons.append(f"Price is at/near resistance {r1}")
        return "TAKE_PROFIT", reasons
    
    if pnl_percent >= 15 and forecast_signal != "bullish":
        reasons.append(f"Position is up {pnl_percent:.1f}% (>15%)")
        reasons.append(f"Forecast is not strongly bullish")
        return "TAKE_PROFIT", reasons
    
    # --- AVERAGE DOWN: In loss but bullish outlook ---
    if pnl_percent < 0 and pnl_percent > -8:
        if forecast_signal == "bullish" and confidence >= 0.5:
            if remaining_balance > 0:
                potential_shares = int(remaining_balance / current_price)
                if potential_shares > 0:
                    reasons.append(f"Position is down {abs(pnl_percent):.1f}% (within averaging range)")
                    reasons.append(f"Forecast is bullish with {confidence*100:.0f}% confidence")
                    if current_price <= s1 * 1.02:
                        reasons.append(f"Price is near support level {s1}")
                    reasons.append(f"Can buy {potential_shares} more shares with available balance")
                    return "AVERAGE_DOWN", reasons
    
    # --- AVERAGE UP: In profit with strong bullish momentum ---
    if pnl_percent > 0 and pnl_percent < 10:
        if forecast_signal == "bullish" and confidence >= 0.6 and predicted_change > 5:
            if remaining_balance > 0:
                potential_shares = int(remaining_balance / current_price)
                if potential_shares > 0:
                    reasons.append(f"Position is up {pnl_percent:.1f}% with strong momentum")
                    reasons.append(f"Forecast predicts additional {predicted_change:.1f}% upside")
                    if rsi < 70:
                        reasons.append(f"RSI at {rsi:.0f} (not overbought)")
                    reasons.append(f"Can add {potential_shares} shares to ride the trend")
                    return "AVERAGE_UP", reasons
    
    # --- HOLD: Default action ---
    reasons.append(f"Current P/L: {pnl_percent:+.1f}%")
    reasons.append(f"Forecast: {forecast_signal} ({predicted_change:+.1f}%)")
    
    if pnl_percent > 0:
        reasons.append("Position is profitable, no immediate action needed")
    elif pnl_percent > -8:
        reasons.append("Loss is within tolerance, monitoring recommended")
    
    if forecast_signal == "bullish":
        reasons.append("Bullish outlook supports holding")
    elif forecast_signal == "neutral":
        reasons.append("Neutral outlook, wait for clearer signals")
    
    return "HOLD", reasons


def _calculate_entry_advice(
    current_price: float,
    avg_price: float,
    action: str,
    sr_levels: Dict[str, float],
    forecast_signal: str,
    predicted_change: float
) -> Dict[str, Any]:
    """
    Calculate entry price advice for averaging scenarios
    
    Returns:
        Dictionary with suggested entry price, zone, and reasoning
    """
    s1 = sr_levels.get("s1", current_price * 0.98)
    s2 = sr_levels.get("s2", current_price * 0.95)
    r1 = sr_levels.get("r1", current_price * 1.02)
    
    advice = {
        "suggestedEntry": None,
        "entryZone": None,
        "reasoning": None,
        "waitForDip": False
    }
    
    if action == "AVERAGE_DOWN":
        # For averaging down, suggest entry near support levels
        if current_price <= s1 * 1.02:
            # Already near support - good entry
            advice["suggestedEntry"] = round_to_tick(current_price)
            advice["entryZone"] = f"{round_to_tick(s1)} - {round_to_tick(current_price)}"
            advice["reasoning"] = "Current price is near support - favorable entry for averaging down"
            advice["waitForDip"] = False
        else:
            # Price above support - wait for pullback
            advice["suggestedEntry"] = round_to_tick(s1)
            advice["entryZone"] = f"{round_to_tick(s2)} - {round_to_tick(s1)}"
            advice["reasoning"] = f"Wait for pullback to support zone around {round_to_tick(s1)}"
            advice["waitForDip"] = True
    
    elif action == "AVERAGE_UP":
        # For averaging up, suggest entry on pullback during bullish trend
        if forecast_signal == "bullish" and predicted_change > 0:
            pullback_price = current_price * 0.98  # 2% pullback
            pullback_price = round_to_tick(pullback_price)
            
            advice["suggestedEntry"] = pullback_price
            advice["entryZone"] = f"{pullback_price} - {round_to_tick(current_price)}"
            advice["reasoning"] = f"Wait for 2% pullback to {pullback_price} for better entry"
            advice["waitForDip"] = True
        else:
            advice["suggestedEntry"] = round_to_tick(current_price)
            advice["entryZone"] = f"{round_to_tick(current_price)} - {round_to_tick(r1)}"
            advice["reasoning"] = "Strong momentum - current price acceptable for averaging up"
            advice["waitForDip"] = False
    
    elif action == "HOLD":
        # Provide entry suggestion if user wants to add more
        if forecast_signal == "bullish":
            advice["suggestedEntry"] = round_to_tick(s1)
            advice["entryZone"] = f"{round_to_tick(s1)} - {round_to_tick(current_price * 0.99)}"
            advice["reasoning"] = "If adding position, wait for pullback to support"
            advice["waitForDip"] = True
        else:
            advice["reasoning"] = "No entry recommended at current levels"
            advice["waitForDip"] = True
    
    else:
        # CUT_LOSS or TAKE_PROFIT - no entry advice
        advice["reasoning"] = f"No entry advised - current recommendation is {action}"
    
    return advice


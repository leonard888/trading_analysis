"""
Enhanced Forecast Service
Combines technical analysis, ML predictions, commodity correlation, and news sentiment
to provide comprehensive forecasts with reasoning
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Stock to commodity mapping
STOCK_COMMODITY_MAP = {
    # Gold mining
    "ARCI.JK": {"commodity": "gold", "commodity_symbol": "GC=F", "sector": "Gold Mining"},
    "ANTM.JK": {"commodity": "gold", "commodity_symbol": "GC=F", "sector": "Mining (Gold/Nickel)"},
    "BRMS.JK": {"commodity": "gold", "commodity_symbol": "GC=F", "sector": "Gold Mining"},
    
    # Coal
    "BUMI.JK": {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Coal Mining"},
    "ADRO.JK": {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Coal Mining"},
    "PTBA.JK": {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Coal Mining"},
    
    # Nickel
    "NCKL.JK": {"commodity": "nickel", "commodity_symbol": "^SPGSNI", "sector": "Nickel Mining"},
    "INCO.JK": {"commodity": "nickel", "commodity_symbol": "^SPGSNI", "sector": "Nickel Mining"},
    
    # Oil & Gas
    "ELSA.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Oil & Gas Services"},
    "MEDC.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Oil & Gas"},
    "PGAS.JK": {"commodity": "natural_gas", "commodity_symbol": "NG=F", "sector": "Natural Gas"},
    
    # Copper
    "TINS.JK": {"commodity": "tin", "commodity_symbol": "HG=F", "sector": "Tin Mining"},
    
    # Energy & Petrochemicals
    "BRPT.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Petrochemicals & Energy"},
    "TPIA.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Petrochemicals"},
    "BREN.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Renewable Energy"}, # Correlated with energy prices
    
    # Shipping & Logistics (Energy related)
    "BULL.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Oil Tanker Shipping"},
    "GTSI.JK": {"commodity": "natural_gas", "commodity_symbol": "NG=F", "sector": "LNG Shipping"},
    "HUMI.JK": {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Energy Shipping"},
    
    # Mining Services
    "PTRO.JK": {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Mining Contractor"},
    "DEWA.JK": {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Mining Contractor"},
    
    # Gold & Jewelry
    "HRTA.JK": {"commodity": "gold", "commodity_symbol": "GC=F", "sector": "Gold Jewelry"},
    
    # Technology & Telecom
    "NINE.JK": {"commodity": None, "commodity_symbol": None, "sector": "Technology Services"},
    "INET.JK": {"commodity": None, "commodity_symbol": None, "sector": "ISP & Tech"},
    "MLPL.JK": {"commodity": None, "commodity_symbol": None, "sector": "Holding (Tech/Retail)"},
    
    # Palm Oil / CPO
    "AALI.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "ANDI.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "BWPT.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "CBUT.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "CSRA.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "DSNG.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "FAPA.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "GOLL.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "GZCO.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "JARR.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "JAWA.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "LSIP.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "MAGP.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "MGRO.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "MKTR.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "PALM.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "PGUN.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "PNGO.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "PSGO.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "SGRO.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "SIMP.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "SMAR.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "SSMS.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "STAA.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "TAPG.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "TBLA.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    "TLDN.JK": {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"},
    
    # Property & Hospitality
    "BKSL.JK": {"commodity": None, "commodity_symbol": None, "sector": "Property"},
    "BUVA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Hospitality"},
    "MINA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Property & Hospitality"},
    "CDIA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Others"},
}

# Commodity News Keywords Map
COMMODITY_NEWS_MAP = {
    "GC=F": {"keywords": ["gold", "emas", "precious metal"], "name": "Gold"},
    "CL=F": {"keywords": ["oil", "minyak", "crude", "petroleum"], "name": "Crude Oil"},
    "SI=F": {"keywords": ["silver", "perak"], "name": "Silver"},
    "MTF=F": {"keywords": ["coal", "batubara"], "name": "Coal"},
    "^SPGSNI": {"keywords": ["nickel", "nikel"], "name": "Nickel"},
    "HG=F": {"keywords": ["copper", "tembaga"], "name": "Copper"},
    "NG=F": {"keywords": ["natural gas", "gas alam"], "name": "Natural Gas"},
    "ZL=F": {"keywords": ["palm oil", "cpo", "sawit", "kelapa sawit", "crude palm oil"], "name": "CPO (Palm Oil)"},
}

def get_commodity_trend(commodity_symbol: str, period: str = "1mo") -> Dict[str, Any]:
    """
    Analyze commodity price trend
    """
    try:
        ticker = yf.Ticker(commodity_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty or len(hist) < 5:
            return {"available": False}
        
        # Calculate trend
        closes = hist['Close'].values
        current = closes[-1]
        prev_day = closes[-2] if len(closes) > 1 else current
        week_ago = closes[-5] if len(closes) >= 5 else closes[0]
        month_start = closes[0]
        
        daily_change = (current - prev_day) / prev_day * 100
        weekly_change = (current - week_ago) / week_ago * 100
        monthly_change = (current - month_start) / month_start * 100
        
        # Determine trend
        if monthly_change > 5:
            trend = "strong_uptrend"
            description = "surging"
        elif monthly_change > 2:
            trend = "uptrend"
            description = "rising"
        elif monthly_change < -5:
            trend = "strong_downtrend"
            description = "plunging"
        elif monthly_change < -2:
            trend = "downtrend"
            description = "falling"
        else:
            trend = "sideways"
            description = "stable"
        
        return {
            "available": True,
            "currentPrice": round(current, 2),
            "dailyChange": round(daily_change, 2),
            "weeklyChange": round(weekly_change, 2),
            "monthlyChange": round(monthly_change, 2),
            "trend": trend,
            "description": description
        }
    except Exception as e:
        return {"available": False, "error": str(e)}

def analyze_news_sentiment(news_articles: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate sentiment from news articles
    """
    if not news_articles:
        return {
            "available": False,
            "overallSentiment": "neutral",
            "score": 0
        }
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    key_headlines = []
    
    for article in news_articles[:10]:  # Analyze top 10 articles
        sentiment = article.get("sentiment", {})
        label = sentiment.get("label", "neutral")
        
        if label == "positive":
            positive_count += 1
            if len(key_headlines) < 3:
                key_headlines.append({"title": article.get("title", ""), "sentiment": "positive"})
        elif label == "negative":
            negative_count += 1
            if len(key_headlines) < 3:
                key_headlines.append({"title": article.get("title", ""), "sentiment": "negative"})
        else:
            neutral_count += 1
    
    total = positive_count + negative_count + neutral_count
    if total == 0:
        return {"available": False, "overallSentiment": "neutral", "score": 0}
    
    # Calculate sentiment score (-1 to 1)
    score = (positive_count - negative_count) / total
    
    if score > 0.3:
        sentiment = "positive"
        description = "favorable"
    elif score < -0.3:
        sentiment = "negative"
        description = "unfavorable"
    else:
        sentiment = "neutral"
        description = "mixed"
    
    return {
        "available": True,
        "overallSentiment": sentiment,
        "description": description,
        "score": round(score, 2),
        "positiveCount": positive_count,
        "negativeCount": negative_count,
        "neutralCount": neutral_count,
        "keyHeadlines": key_headlines
    }

def detect_commodity_link(symbol: str, name: str = "", sector: str = "") -> Optional[Dict[str, str]]:
    """
    Smartly detect commodity correlation based on symbol, name and sector
    """
    # 1. Check direct hardcoded map first
    if symbol in STOCK_COMMODITY_MAP:
        return STOCK_COMMODITY_MAP[symbol]
        
    # 2. Check keywords in Name/Sector
    name_lower = name.lower()
    sector_lower = sector.lower()
    
    # Coal
    if "batu bara" in name_lower or "coal" in name_lower or "coal" in sector_lower:
        return {"commodity": "coal", "commodity_symbol": "MTF=F", "sector": "Coal Mining"}
        
    # Gold
    if "gold" in name_lower or "emas" in name_lower or ("gold" in sector_lower and "mining" in sector_lower):
        return {"commodity": "gold", "commodity_symbol": "GC=F", "sector": "Gold Mining"}
        
    # Nickel
    if "nickel" in name_lower or "nikel" in name_lower or "nickel" in sector_lower:
        return {"commodity": "nickel", "commodity_symbol": "^SPGSNI", "sector": "Nickel Mining"}
        
    # Oil & Gas
    if "oil" in name_lower or "petroleum" in name_lower or "petro" in name_lower or "migas" in name_lower or ("oil" in sector_lower and "gas" in sector_lower):
        return {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Oil & Gas"}
        
    # Palm Oil (CPO)
    if "sawit" in name_lower or "palm" in name_lower or "plantation" in sector_lower or "kelapa" in name_lower:
        return {"commodity": "cpo", "commodity_symbol": "ZL=F", "sector": "Palm Oil Plantation"}
        
    # Energy General
    if "energy" in name_lower or "energi" in name_lower or "energy" in sector_lower:
        return {"commodity": "oil", "commodity_symbol": "CL=F", "sector": "Energy"}
        
    return None

def calculate_validity(
    df: pd.DataFrame,
    ta_signals: Dict[str, Any],
    news_sentiment: Dict[str, Any],
    sr_levels: Dict[str, float]
) -> str:
    """
    Calculate forecast validity based on market conditions
    """
    # Default
    validity = "1 week"
    
    current_price = df['Close'].iloc[-1]
    
    # 1. High Volatility Checks
    # Check Bollinger Bandwidth
    if ta_signals and "bollingerBands" in ta_signals:
        bandwidth = ta_signals["bollingerBands"].get("bandwidth", 0)
        if bandwidth > 10: # High volatility > 10% bandwidth
            return "24-48 hours"
            
    # Check daily change (if huge move)
    daily_change = abs(df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]
    if daily_change > 0.05: # > 5% move
        return "24-48 hours"
        
    # 2. Breaking News
    if news_sentiment and news_sentiment.get("available"):
        score = abs(news_sentiment.get("score", 0))
        if score > 0.6: # Strong sentiment
            return "24 hours"
            
    # 3. Breakout/Breakdown (Price breeching key levels)
    r2 = sr_levels.get("r2")
    s2 = sr_levels.get("s2")
    
    if r2 and current_price > r2:
        return "Market Close" # Re-evaluate at close
    if s2 and current_price < s2:
        return "Market Close"
        
    return validity

from analysis.support_resistance import calculate_support_resistance, generate_trading_plan, round_to_idx_tick

def calculate_next_day_prediction(
    df: pd.DataFrame,
    sentiment_score: float = 0,
    overall_signal: str = "neutral",
    ml_confidence: float = 0
) -> Dict[str, Any]:
    """
    Calculate next day price prediction range using historical percentile analysis.
    
    Uses actual historical next-day high/low moves to produce realistic predictions,
    then applies a small directional bias based on signal/sentiment.
    """
    if df.empty or len(df) < 14:
        return {}

    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    current_price = close.iloc[-1]
    
    # 1. Calculate ATR for reference/display
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean().iloc[-1]
    if pd.isna(atr):
        atr = (high - low).mean()
    
    # 2. Calculate ACTUAL historical next-day moves (percentage from prev close)
    # How much does the High typically go above the previous Close?
    next_high_pct = ((high - prev_close) / prev_close * 100).dropna()
    # How much does the Low typically go below the previous Close?
    next_low_pct = ((low - prev_close) / prev_close * 100).dropna()
    
    # Remove extreme outliers (beyond 99th percentile)
    if len(next_high_pct) > 5:
        upper_clip = next_high_pct.quantile(0.99)
        lower_clip = next_low_pct.quantile(0.01)
        next_high_pct = next_high_pct.clip(upper=upper_clip)
        next_low_pct = next_low_pct.clip(lower=lower_clip)
    
    # 3. Use percentiles for prediction range
    # 75th percentile for high (optimistic but realistic)
    # 25th percentile for low (pessimistic but realistic)
    base_high_pct = next_high_pct.quantile(0.75) if len(next_high_pct) > 5 else 2.0
    base_low_pct = next_low_pct.quantile(0.25) if len(next_low_pct) > 5 else -2.0
    
    # 4. Determine directional bias (small shift, NOT amplification)
    bias = 0
    if overall_signal == "bullish":
        bias += 0.3
    elif overall_signal == "bearish":
        bias -= 0.3
    
    # Adjust with sentiment (-1 to 1)
    bias += sentiment_score * 0.15
    
    # Adjust with ML confidence (smaller weight)
    if overall_signal == "bullish":
        bias += ml_confidence * 0.15
    elif overall_signal == "bearish":
        bias -= ml_confidence * 0.15
    
    # Clamp bias to reasonable range
    bias = max(-0.6, min(0.6, bias))
    
    # 5. Apply bias as a SHIFT to the range (not amplification)
    # Bias shifts both high and low by a small percentage of ATR
    atr_pct = (atr / current_price) * 100  # ATR as percentage
    shift_pct = bias * atr_pct * 0.15  # Small shift (max ~0.5% of price)
    
    # Final predicted percentages
    pred_high_pct = base_high_pct + shift_pct
    pred_low_pct = base_low_pct + shift_pct
    
    # 6. Apply hard caps based on realistic IDX daily limits
    # Normal IDX daily limit is ±20-25%, but realistic daily moves are much smaller
    max_move_pct = min(atr_pct * 0.8, 7.0)  # Cap at 7% or 80% of ATR%
    
    pred_high_pct = min(pred_high_pct, max_move_pct)
    pred_low_pct = max(pred_low_pct, -max_move_pct)
    
    # Ensure high is above current price and low is below for meaningful range
    pred_high_pct = max(pred_high_pct, 0.5)  # At least +0.5%
    pred_low_pct = min(pred_low_pct, -0.5)   # At least -0.5%
    
    # 7. Calculate final prices
    pred_high = current_price * (1 + pred_high_pct / 100)
    pred_low = current_price * (1 + pred_low_pct / 100)
    
    # Safety: Low shouldn't go below IDX minimum
    if pred_low < 50:
        pred_low = 50
    
    return {
        "high": round_to_idx_tick(pred_high),
        "low": round_to_idx_tick(pred_low),
        "bias": round(bias, 2),
        "volatility": round(atr, 2)
    }

def generate_forecast_reasons(
    symbol: str,
    df: pd.DataFrame, # Added dataframe arg for calc
    ta_signals: Dict[str, Any],
    commodity_analysis: Optional[Dict[str, Any]],
    news_sentiment: Dict[str, Any],
    ml_prediction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive forecast with detailed reasoning and trading plan
    """
    reasons = []
    bullish_factors = 0
    bearish_factors = 0
    
    current_price = df['Close'].iloc[-1]
    
    # Calculate Support & Resistance
    sr_levels = calculate_support_resistance(df, is_commodity=symbol.endswith('=F'))
    
    # Get stock/commodity info
    is_commodity = symbol in COMMODITY_NEWS_MAP
    
    # Smart Commodity Detection
    from services.stock_service import ALL_STOCKS
    stock_info = ALL_STOCKS.get(symbol, {})
    stock_name = stock_info.get("name", "")
    stock_sector = stock_info.get("sector", "")
    
    commodity_info = detect_commodity_link(symbol, stock_name, stock_sector)
    # Safely get commodity name, handling None values
    if is_commodity:
        commodity_name = COMMODITY_NEWS_MAP[symbol]["name"]
    elif commodity_info and commodity_info.get("commodity"):
        commodity_name = commodity_info["commodity"].replace("_", " ").title()
    else:
        commodity_name = None
    
    # 1. Technical Analysis Signals
    if ta_signals and "signals" in ta_signals:
        overall_signal = ta_signals["signals"].get("overall", {})
        signal = overall_signal.get("signal", "neutral")
        strength = overall_signal.get("strength", 0)
        
        if signal == "buy":
            bullish_factors += 2 * strength
            reasons.append({
                "category": "Technical Analysis",
                "signal": "bullish",
                "detail": f"Technical indicators show BUY signal (RSI, MACD, Moving Averages aligned)"
            })
        elif signal == "sell":
            bearish_factors += 2 * strength
            reasons.append({
                "category": "Technical Analysis",
                "signal": "bearish",
                "detail": f"Technical indicators show SELL signal (overbought conditions detected)"
            })
        else:
            reasons.append({
                "category": "Technical Analysis",
                "signal": "neutral",
                "detail": "Technical indicators are mixed, no clear direction"
            })
        
        # Add specific indicator details
        rsi = ta_signals.get("rsi", 50)
        if rsi < 30:
            reasons.append({
                "category": "RSI Indicator",
                "signal": "bullish",
                "detail": f"RSI at {rsi:.1f} indicates oversold conditions - potential bounce"
            })
            bullish_factors += 0.5
        elif rsi > 70:
            reasons.append({
                "category": "RSI Indicator",
                "signal": "bearish",
                "detail": f"RSI at {rsi:.1f} indicates overbought conditions - potential pullback"
            })
            bearish_factors += 0.5
    
    # 2. Commodity Price Correlation (Only for stocks)
    if not is_commodity and commodity_analysis and commodity_analysis.get("available"):
        trend = commodity_analysis.get("trend", "sideways")
        monthly_change = commodity_analysis.get("monthlyChange", 0)
        description = commodity_analysis.get("description", "stable")
        
        if trend in ["uptrend", "strong_uptrend"]:
            bullish_factors += 1.5
            reasons.append({
                "category": f"{commodity_name} Price",
                "signal": "bullish",
                "detail": f"{commodity_name} prices are {description} ({monthly_change:+.1f}% this month) - positive for {symbol.replace('.JK', '')}"
            })
        elif trend in ["downtrend", "strong_downtrend"]:
            bearish_factors += 1.5
            reasons.append({
                "category": f"{commodity_name} Price",
                "signal": "bearish",
                "detail": f"{commodity_name} prices are {description} ({monthly_change:+.1f}% this month) - negative for {symbol.replace('.JK', '')}"
            })
        else:
            reasons.append({
                "category": f"{commodity_name} Price",
                "signal": "neutral",
                "detail": f"{commodity_name} prices are {description} - limited impact on {symbol.replace('.JK', '')}"
            })
    elif is_commodity:
        # For commodities themselves, price trend IS the factor
        # We can add a "Macro Trend" factor here if we had broader index data, 
        # but for now we rely on the Technical Analysis section above which covers price action.
        pass
    
    # 3. News Sentiment
    if news_sentiment and news_sentiment.get("available"):
        sentiment = news_sentiment.get("overallSentiment", "neutral")
        description = news_sentiment.get("description", "mixed")
        
        if sentiment == "positive":
            bullish_factors += 1
            headlines = news_sentiment.get("keyHeadlines", [])
            headline_text = headlines[0]["title"][:60] + "..." if headlines else "positive market news"
            reasons.append({
                "category": "Global Sentiment" if is_commodity else "News Sentiment",
                "signal": "bullish",
                "detail": f"Market news is {description}: \"{headline_text}\""
            })
        elif sentiment == "negative":
            bearish_factors += 1
            headlines = news_sentiment.get("keyHeadlines", [])
            headline_text = headlines[0]["title"][:60] + "..." if headlines else "concerning market news"
            reasons.append({
                "category": "Global Sentiment" if is_commodity else "News Sentiment",
                "signal": "bearish",
                "detail": f"Market news is {description}: \"{headline_text}\""
            })
        else:
            reasons.append({
                "category": "Global Sentiment" if is_commodity else "News Sentiment",
                "signal": "neutral",
                "detail": f"News sentiment is {description} with no clear directional bias"
            })
    
    # 4. ML Prediction - Always factor in (scaled by confidence)
    if ml_prediction:
        ml_signal = ml_prediction.get("signal", "neutral")
        ml_confidence = ml_prediction.get("confidence", 0.5)
        predicted_change = ml_prediction.get("predictedChange", 0)
        
        # Scale contribution by confidence (even low confidence contributes something)
        weight = ml_confidence * 1.5  # Max ~1.5 impact
        
        if ml_signal == "bullish":
            bullish_factors += weight
            if ml_confidence > 0.4:  # Only show in reasons if reasonably confident
                reasons.append({
                    "category": "ML Prediction",
                    "signal": "bullish",
                    "detail": f"Machine learning model predicts {predicted_change:+.1f}% move with {ml_confidence*100:.0f}% confidence"
                })
        elif ml_signal == "bearish":
            bearish_factors += weight
            if ml_confidence > 0.4:
                reasons.append({
                    "category": "ML Prediction",
                    "signal": "bearish",
                    "detail": f"Machine learning model predicts {predicted_change:+.1f}% move with {ml_confidence*100:.0f}% confidence"
                })
    
    # 5. Price Momentum (stock-specific factor)
    if len(df) >= 5:
        recent_return = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100
        if recent_return > 3:
            bullish_factors += 0.5
            reasons.append({
                "category": "Price Momentum",
                "signal": "bullish",
                "detail": f"Stock up {recent_return:.1f}% in the last 5 days - positive momentum"
            })
        elif recent_return < -3:
            bearish_factors += 0.5
            reasons.append({
                "category": "Price Momentum",
                "signal": "bearish", 
                "detail": f"Stock down {abs(recent_return):.1f}% in the last 5 days - negative momentum"
            })
    
    # Calculate overall forecast
    total_score = bullish_factors - bearish_factors
    max_score = bullish_factors + bearish_factors
    
    if max_score == 0:
        confidence = 0.5
        overall_signal = "neutral"
    else:
        confidence = 0.5 + (abs(total_score) / max_score) * 0.4
        overall_signal = "bullish" if total_score > 0.5 else "bearish" if total_score < -0.5 else "neutral"
    
    # Generate summary
    bullish_reasons = [r for r in reasons if r["signal"] == "bullish"]
    bearish_reasons = [r for r in reasons if r["signal"] == "bearish"]
    
    if overall_signal == "bullish":
        summary = f"BULLISH outlook based on {len(bullish_reasons)} positive factors"
        if commodity_name and commodity_analysis and commodity_analysis.get("available"):
            if commodity_analysis.get("trend") in ["uptrend", "strong_uptrend"]:
                summary += f" including rising {commodity_name} prices"
    elif overall_signal == "bearish":
        summary = f"BEARISH outlook based on {len(bearish_reasons)} negative factors"
        if commodity_name and commodity_analysis and commodity_analysis.get("available"):
            if commodity_analysis.get("trend") in ["downtrend", "strong_downtrend"]:
                summary += f" including falling {commodity_name} prices"
    else:
        summary = "NEUTRAL outlook - mixed signals from different factors"
    
    # Generate Trading Plan
    trading_plan = generate_trading_plan(
        current_price=current_price,
        signal=overall_signal,
        s1=sr_levels.get("s1"),
        s2=sr_levels.get("s2"),
        r1=sr_levels.get("r1"),
        r2=sr_levels.get("r2")
    )
    
    # Calculate validity
    validity = calculate_validity(df, ta_signals, news_sentiment, sr_levels)

    # Calculate Next Day Prediction
    next_day_pred = calculate_next_day_prediction(
        df=df,
        sentiment_score=news_sentiment.get("score", 0) if news_sentiment else 0,
        overall_signal=overall_signal,
        ml_confidence=confidence
    )
    print(f"DEBUG: Next Day Prediction for {symbol}: {next_day_pred}") # DEBUG LOG

    return {
        "overallSignal": overall_signal,
        "confidence": round(confidence, 3),
        "validity": validity,
        "summary": summary,
        "reasons": reasons,
        "factorBreakdown": {
            "bullishFactors": round(bullish_factors, 2),
            "bearishFactors": round(bearish_factors, 2),
            "netScore": round(total_score, 2)
        },
        "commodityCorrelation": {
            "commodity": commodity_name if commodity_name else None,
            "analysis": commodity_analysis if commodity_analysis and commodity_analysis.get("available") else None
        },
        "supportResistance": sr_levels,
        "tradingPlan": trading_plan,
        "nextDayPrediction": next_day_pred
    }

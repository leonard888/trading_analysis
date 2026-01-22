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
    
    # Property & Hospitality
    "BKSL.JK": {"commodity": None, "commodity_symbol": None, "sector": "Property"},
    "BUVA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Hospitality"},
    "MINA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Property & Hospitality"},
    "CDIA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Others"}, # Fallback for unknown
    "CDIA.JK": {"commodity": None, "commodity_symbol": None, "sector": "Others"}, # Fallback for unknown
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

from analysis.support_resistance import calculate_support_resistance, generate_trading_plan

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
    sr_levels = calculate_support_resistance(df)
    
    # Get stock/commodity info
    is_commodity = symbol in COMMODITY_NEWS_MAP
    commodity_info = STOCK_COMMODITY_MAP.get(symbol, {})
    commodity_name = COMMODITY_NEWS_MAP[symbol]["name"] if is_commodity else commodity_info.get("commodity", "").replace("_", " ").title()
    
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
    
    # 4. ML Prediction
    if ml_prediction:
        ml_signal = ml_prediction.get("signal", "neutral")
        ml_confidence = ml_prediction.get("confidence", 0.5)
        predicted_change = ml_prediction.get("predictedChange", 0)
        
        if ml_signal == "bullish" and ml_confidence > 0.6:
            bullish_factors += ml_confidence
            reasons.append({
                "category": "ML Prediction",
                "signal": "bullish",
                "detail": f"Machine learning model predicts {predicted_change:+.1f}% move with {ml_confidence*100:.0f}% confidence"
            })
        elif ml_signal == "bearish" and ml_confidence > 0.6:
            bearish_factors += ml_confidence
            reasons.append({
                "category": "ML Prediction",
                "signal": "bearish",
                "detail": f"Machine learning model predicts {predicted_change:+.1f}% move with {ml_confidence*100:.0f}% confidence"
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
    
    return {
        "overallSignal": overall_signal,
        "confidence": round(confidence, 3),
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
        "tradingPlan": trading_plan
    }

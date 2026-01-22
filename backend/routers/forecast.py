"""
Forecast Router - Enhanced API endpoints for ML-based predictions with reasoning
"""

from fastapi import APIRouter, Query, HTTPException
import yfinance as yf
import pandas as pd
from ml.lstm_model import predict_prices
from ml.ensemble_model import get_ensemble_forecast
from analysis.technical_indicators import get_all_indicators
from services.forecast_service import (
    STOCK_COMMODITY_MAP,
    COMMODITY_NEWS_MAP,
    get_commodity_trend,
    analyze_news_sentiment,
    generate_forecast_reasons
)
from services.news_service import get_all_news, get_news_for_stock

router = APIRouter()

@router.get("/{symbol}")
async def get_forecast(
    symbol: str,
    days: int = Query(5, description="Number of days to forecast (1-30)"),
    period: str = Query("6mo", description="Historical data period for training")
):
    """
    Get comprehensive ML-based price forecast with reasoning
    """
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 30")
    
    # Ensure symbol has .JK suffix for IDX stocks
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Get closing prices
        prices = df['Close'].tolist()
        
        # LSTM prediction
        lstm_forecast = predict_prices(prices, days)
        
        # Get technical indicators
        indicators = get_all_indicators(df)
        
        # Ensemble prediction
        ensemble_result = get_ensemble_forecast(df, indicators)
        
        # Get commodity correlation if applicable
        commodity_info = STOCK_COMMODITY_MAP.get(symbol, {})
        commodity_analysis = None
        if commodity_info:
            commodity_symbol = commodity_info.get("commodity_symbol")
            if commodity_symbol:
                commodity_analysis = get_commodity_trend(commodity_symbol)
        
        # Get news and analyze sentiment
        commodity_news_info = COMMODITY_NEWS_MAP.get(symbol)
        keywords = commodity_news_info.get("keywords") if commodity_news_info else None
        
        news_articles = get_news_for_stock(symbol, limit=15, keywords=keywords)
        if not news_articles:
            # Fallback to general news
            news_articles = get_all_news(limit=20)
        news_sentiment = analyze_news_sentiment(news_articles)
        
        enhanced_forecast = generate_forecast_reasons(
            symbol=symbol,
            df=df,
            ta_signals=indicators,
            commodity_analysis=commodity_analysis,
            news_sentiment=news_sentiment,
            ml_prediction=ensemble_result
        )
        
        return {
            "symbol": symbol,
            "currentPrice": round(prices[-1], 2),
            "forecast": {
                "signal": enhanced_forecast["overallSignal"],
                "confidence": enhanced_forecast["confidence"],
                "summary": enhanced_forecast["summary"],
                "reasons": enhanced_forecast["reasons"],
                "factorBreakdown": enhanced_forecast["factorBreakdown"]
            },
            "supportResistance": enhanced_forecast.get("supportResistance"),
            "tradingPlan": enhanced_forecast.get("tradingPlan"),
            "commodityCorrelation": enhanced_forecast.get("commodityCorrelation"),
            "predictions": {
                "lstm": lstm_forecast,
                "ensemble": ensemble_result
            },
            "technicalSignals": indicators.get("signals", {}),
            "newsSentiment": news_sentiment,
            "dataPoints": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/quick")
async def get_quick_forecast(
    symbol: str
):
    """
    Get quick enhanced forecast with reasoning (no LSTM training)
    """
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo")
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Get technical indicators
        indicators = get_all_indicators(df)
        
        # Quick ensemble prediction
        ensemble_result = get_ensemble_forecast(df, indicators, train_if_needed=False)
        
        # Get commodity correlation if applicable
        commodity_info = STOCK_COMMODITY_MAP.get(symbol, {})
        commodity_analysis = None
        if commodity_info:
            commodity_symbol = commodity_info.get("commodity_symbol")
            if commodity_symbol:
                commodity_analysis = get_commodity_trend(commodity_symbol)
        
        # Get news and analyze sentiment
        commodity_news_info = COMMODITY_NEWS_MAP.get(symbol)
        keywords = commodity_news_info.get("keywords") if commodity_news_info else None
        
        news_articles = get_news_for_stock(symbol, limit=10, keywords=keywords)
        if not news_articles:
            news_articles = get_all_news(limit=15)
        news_sentiment = analyze_news_sentiment(news_articles)
        
        # Generate comprehensive forecast with reasons
        enhanced_forecast = generate_forecast_reasons(
            symbol=symbol,
            df=df,
            ta_signals=indicators,
            commodity_analysis=commodity_analysis,
            news_sentiment=news_sentiment,
            ml_prediction=ensemble_result
        )
        
        return {
            "symbol": symbol,
            "currentPrice": round(df['Close'].iloc[-1], 2),
            "forecast": {
                "signal": enhanced_forecast["overallSignal"],
                "confidence": enhanced_forecast["confidence"],
                "summary": enhanced_forecast["summary"],
                "reasons": enhanced_forecast["reasons"],
                "factorBreakdown": enhanced_forecast["factorBreakdown"]
            },
            "supportResistance": enhanced_forecast.get("supportResistance"),
            "tradingPlan": enhanced_forecast.get("tradingPlan"),
            "commodityCorrelation": enhanced_forecast.get("commodityCorrelation"),
            "signals": indicators.get("signals", {}),
            "newsSentiment": news_sentiment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/reasons")
async def get_forecast_reasons(
    symbol: str
):
    """
    Get only the forecast reasons breakdown
    """
    forecast = await get_quick_forecast(symbol)
    return {
        "symbol": symbol,
        "signal": forecast["forecast"]["signal"],
        "confidence": forecast["forecast"]["confidence"],
        "summary": forecast["forecast"]["summary"],
        "reasons": forecast["forecast"]["reasons"],
        "commodityCorrelation": forecast.get("commodityCorrelation")
    }

"""
Analysis Router - API endpoints for technical analysis
"""

from fastapi import APIRouter, Query, HTTPException
import yfinance as yf
import pandas as pd
from analysis.technical_indicators import get_all_indicators
from analysis.pattern_detection import detect_all_patterns

router = APIRouter()

@router.get("/{symbol}")
async def get_analysis(
    symbol: str,
    period: str = Query("3mo", description="Data period for analysis")
):
    """
    Get full technical analysis for a stock
    """
    # Ensure symbol has .JK suffix for IDX stocks
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Get technical indicators
        indicators = get_all_indicators(df)
        
        # Get pattern detection
        patterns = detect_all_patterns(df)
        
        return {
            "symbol": symbol,
            "indicators": indicators,
            "patterns": patterns,
            "dataPoints": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/indicators")
async def get_indicators_only(
    symbol: str,
    period: str = Query("3mo", description="Data period")
):
    """
    Get only technical indicators
    """
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        indicators = get_all_indicators(df)
        return {"symbol": symbol, "indicators": indicators}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/patterns")
async def get_patterns_only(
    symbol: str,
    period: str = Query("3mo", description="Data period")
):
    """
    Get only pattern detection results
    """
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        patterns = detect_all_patterns(df)
        return {"symbol": symbol, "patterns": patterns}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

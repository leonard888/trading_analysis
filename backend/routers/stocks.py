"""
Stocks Router - API endpoints for stock data
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from services.stock_service import (
    get_stock_data, 
    search_stocks, 
    get_multiple_stocks,
    get_all_sectors,
    DEFAULT_STOCKS
)

router = APIRouter()

@router.get("/{symbol}")
async def get_stock(
    symbol: str,
    period: str = Query("1mo", description="Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="Data interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo")
):
    """
    Get stock data for a specific symbol
    """
    data = get_stock_data(symbol, period, interval)
    
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    
    return data

@router.get("/")
async def get_default_stocks():
    """
    Get all pre-configured default stocks
    """
    symbols = list(DEFAULT_STOCKS.keys())
    return get_multiple_stocks(symbols)

@router.get("/search/query")
async def search_stock(
    q: str = Query(..., description="Search query (symbol or company name)")
):
    """
    Search for stocks by symbol or company name
    """
    results = search_stocks(q)
    return {"query": q, "results": results}

@router.get("/info/sectors")
async def get_sectors():
    """
    Get list of available sectors
    """
    return {"sectors": get_all_sectors()}

@router.get("/batch/multiple")
async def get_batch_stocks(
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """
    Get data for multiple stocks at once
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    return get_multiple_stocks(symbol_list)

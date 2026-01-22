"""
News Router - API endpoints for financial news
"""

from fastapi import APIRouter, Query
from typing import Optional
from services.news_service import (
    get_all_news,
    get_news_for_stock,
    get_available_sources
)

router = APIRouter()

@router.get("/")
async def get_news(
    category: Optional[str] = Query(None, description="Filter by category: global, indonesia"),
    limit: int = Query(50, description="Maximum number of articles")
):
    """
    Get aggregated news from all sources
    """
    news = get_all_news(category, limit)
    return {"articles": news, "count": len(news)}

@router.get("/sources")
async def list_sources():
    """
    Get list of available news sources
    """
    return {"sources": get_available_sources()}

@router.get("/stock/{symbol}")
async def get_stock_news(
    symbol: str,
    limit: int = Query(20, description="Maximum number of articles")
):
    """
    Get news related to a specific stock
    """
    news = get_news_for_stock(symbol, limit)
    return {"symbol": symbol, "articles": news, "count": len(news)}

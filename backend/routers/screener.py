"""
Screener Router - API endpoints for stock screening
"""

from fastapi import APIRouter
from services.screener_service import scan_all_stocks

router = APIRouter()

@router.get("/scan")
async def scan_stocks():
    """
    Scan all IDX stocks and return ranked by sentiment score.
    Returns top bullish and bearish stocks with filters-ready data.
    """
    return scan_all_stocks()

"""
Commodities Router - API endpoints for commodity prices
"""

from fastapi import APIRouter, Query, HTTPException
from services.commodity_service import (
    get_commodity_data,
    get_all_commodities,
    get_available_commodities
)

router = APIRouter()

@router.get("/")
async def list_commodities():
    """
    Get all available commodities with current prices
    """
    return get_all_commodities()

@router.get("/available")
async def available_commodities():
    """
    Get list of available commodity types
    """
    return get_available_commodities()

@router.get("/{commodity_type}")
async def get_commodity(
    commodity_type: str,
    period: str = Query("1mo", description="Data period"),
    interval: str = Query("1d", description="Data interval")
):
    """
    Get price data for a specific commodity
    """
    data = get_commodity_data(commodity_type, period, interval)
    
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    
    return data

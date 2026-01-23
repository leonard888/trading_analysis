"""
Position Router - API endpoints for position analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.position_advisor_service import analyze_position

router = APIRouter()


class PositionRequest(BaseModel):
    symbol: str
    avg_price: float
    quantity: int
    remaining_balance: Optional[float] = 0


@router.post("/analyze")
async def analyze_stock_position(request: PositionRequest):
    """
    Analyze a stock position and get action recommendation
    
    - **symbol**: Stock symbol (e.g., BBCA, ADRO)
    - **avg_price**: Your average purchase price
    - **quantity**: Number of shares held
    - **remaining_balance**: Available cash in IDR for averaging (optional)
    """
    result = analyze_position(
        symbol=request.symbol,
        avg_price=request.avg_price,
        quantity=request.quantity,
        remaining_balance=request.remaining_balance
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/tick-size/{price}")
async def get_tick_size(price: float):
    """
    Get the IDX tick size for a given price
    """
    from services.position_advisor_service import get_idx_tick_size, round_to_tick
    
    tick_size = get_idx_tick_size(price)
    rounded_price = round_to_tick(price)
    
    return {
        "price": price,
        "tickSize": tick_size,
        "roundedPrice": rounded_price
    }

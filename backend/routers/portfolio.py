"""
Portfolio Router - API endpoints for managing user portfolio positions
Positions are stored persistently and analyzed dynamically
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

from services.position_advisor_service import analyze_position

router = APIRouter()

# Use absolute path based on script location for reliable file access
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_SCRIPT_DIR), "data")
PORTFOLIO_FILE = os.path.join(_DATA_DIR, "portfolio.json")


def _ensure_data_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load_portfolio() -> Dict[str, Dict[str, Any]]:
    """Load portfolio from JSON file"""
    _ensure_data_dir()
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    return {}


def _save_portfolio(portfolio: Dict[str, Dict[str, Any]]):
    """Save portfolio to JSON file"""
    _ensure_data_dir()
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2)


class PositionRequest(BaseModel):
    symbol: str
    avg_price: float
    quantity: int  # In lots (1 lot = 100 shares)
    remaining_balance: Optional[float] = 0


class PositionUpdate(BaseModel):
    avg_price: Optional[float] = None
    quantity: Optional[int] = None
    remaining_balance: Optional[float] = None


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol to include .JK suffix"""
    symbol = symbol.upper()
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    return symbol


@router.get("/")
async def get_portfolio():
    """
    Get all portfolio positions with their current analysis
    """
    portfolio = _load_portfolio()
    positions = []
    
    for symbol, position_data in portfolio.items():
        try:
            # Get fresh analysis for each position
            analysis = analyze_position(
                symbol=symbol,
                avg_price=position_data["avgPrice"],
                quantity=position_data["quantity"],
                remaining_balance=position_data.get("remainingBalance", 0)
            )
            
            positions.append({
                "symbol": symbol,
                "position": position_data,
                "analysis": analysis,
                "addedAt": position_data.get("addedAt")
            })
        except Exception as e:
            # If analysis fails, still include position with error
            positions.append({
                "symbol": symbol,
                "position": position_data,
                "analysis": {"error": str(e)},
                "addedAt": position_data.get("addedAt")
            })
    
    return {
        "positions": positions,
        "count": len(positions),
        "lastUpdated": datetime.now().isoformat()
    }


@router.post("/add")
async def add_position(request: PositionRequest):
    """
    Add a new position to portfolio
    """
    portfolio = _load_portfolio()
    symbol = _normalize_symbol(request.symbol)
    
    if symbol in portfolio:
        raise HTTPException(
            status_code=400, 
            detail=f"{symbol} already in portfolio. Use PUT to update."
        )
    
    portfolio[symbol] = {
        "avgPrice": request.avg_price,
        "quantity": request.quantity,
        "remainingBalance": request.remaining_balance,
        "addedAt": datetime.now().isoformat()
    }
    
    _save_portfolio(portfolio)
    
    # Get initial analysis
    analysis = analyze_position(
        symbol=symbol,
        avg_price=request.avg_price,
        quantity=request.quantity,
        remaining_balance=request.remaining_balance
    )
    
    return {
        "message": f"Added {symbol} to portfolio",
        "symbol": symbol,
        "position": portfolio[symbol],
        "analysis": analysis
    }


@router.put("/{symbol}")
async def update_position(symbol: str, update: PositionUpdate):
    """
    Update an existing position
    """
    portfolio = _load_portfolio()
    symbol = _normalize_symbol(symbol)
    
    if symbol not in portfolio:
        raise HTTPException(status_code=404, detail=f"{symbol} not in portfolio")
    
    # Update only provided fields
    if update.avg_price is not None:
        portfolio[symbol]["avgPrice"] = update.avg_price
    if update.quantity is not None:
        portfolio[symbol]["quantity"] = update.quantity
    if update.remaining_balance is not None:
        portfolio[symbol]["remainingBalance"] = update.remaining_balance
    
    portfolio[symbol]["updatedAt"] = datetime.now().isoformat()
    
    _save_portfolio(portfolio)
    
    # Get fresh analysis
    analysis = analyze_position(
        symbol=symbol,
        avg_price=portfolio[symbol]["avgPrice"],
        quantity=portfolio[symbol]["quantity"],
        remaining_balance=portfolio[symbol].get("remainingBalance", 0)
    )
    
    return {
        "message": f"Updated {symbol}",
        "symbol": symbol,
        "position": portfolio[symbol],
        "analysis": analysis
    }


@router.delete("/{symbol}")
async def remove_position(symbol: str):
    """
    Remove a position from portfolio (sell)
    """
    portfolio = _load_portfolio()
    symbol = _normalize_symbol(symbol)
    
    if symbol not in portfolio:
        raise HTTPException(status_code=404, detail=f"{symbol} not in portfolio")
    
    removed = portfolio.pop(symbol)
    _save_portfolio(portfolio)
    
    return {
        "message": f"Removed {symbol} from portfolio",
        "symbol": symbol,
        "removedPosition": removed
    }


@router.get("/analyze/{symbol}")
async def analyze_single_position(symbol: str):
    """
    Get fresh analysis for a single position
    """
    portfolio = _load_portfolio()
    symbol = _normalize_symbol(symbol)
    
    if symbol not in portfolio:
        raise HTTPException(status_code=404, detail=f"{symbol} not in portfolio")
    
    position_data = portfolio[symbol]
    
    analysis = analyze_position(
        symbol=symbol,
        avg_price=position_data["avgPrice"],
        quantity=position_data["quantity"],
        remaining_balance=position_data.get("remainingBalance", 0)
    )
    
    return {
        "symbol": symbol,
        "position": position_data,
        "analysis": analysis
    }

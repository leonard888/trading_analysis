"""
Watchlist Router - API endpoints for managing user watchlist
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os

router = APIRouter()

# Use absolute path based on script location for reliable file access
# This ensures the file is always found regardless of cwd
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_SCRIPT_DIR), "data")
WATCHLIST_FILE = os.path.join(_DATA_DIR, "watchlist.json")

def _ensure_data_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)

def _load_watchlist() -> List[str]:
    _ensure_data_dir()
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r') as f:
            return json.load(f)
    return []

def _save_watchlist(symbols: List[str]):
    _ensure_data_dir()
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(symbols, f)

class WatchlistItem(BaseModel):
    symbol: str

class WatchlistUpdate(BaseModel):
    symbols: List[str]

@router.get("/")
async def get_watchlist():
    """
    Get user's watchlist
    """
    symbols = _load_watchlist()
    return {"symbols": symbols, "count": len(symbols)}

@router.post("/add")
async def add_to_watchlist(item: WatchlistItem):
    """
    Add a symbol to watchlist
    """
    symbols = _load_watchlist()
    
    # Normalize symbol
    symbol = item.symbol.upper()
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    if symbol not in symbols:
        symbols.append(symbol)
        _save_watchlist(symbols)
        return {"message": f"Added {symbol} to watchlist", "symbols": symbols}
    
    return {"message": f"{symbol} already in watchlist", "symbols": symbols}

@router.post("/remove")
async def remove_from_watchlist(item: WatchlistItem):
    """
    Remove a symbol from watchlist
    """
    symbols = _load_watchlist()
    
    symbol = item.symbol.upper()
    if not symbol.endswith('.JK') and not symbol.endswith('=F'):
        symbol = f"{symbol}.JK"
    
    if symbol in symbols:
        symbols.remove(symbol)
        _save_watchlist(symbols)
        return {"message": f"Removed {symbol} from watchlist", "symbols": symbols}
    
    raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")

@router.put("/")
async def update_watchlist(update: WatchlistUpdate):
    """
    Replace entire watchlist
    """
    symbols = [s.upper() for s in update.symbols]
    symbols = [s if s.endswith('.JK') or s.endswith('=F') else f"{s}.JK" for s in symbols]
    
    _save_watchlist(symbols)
    return {"message": "Watchlist updated", "symbols": symbols}

@router.delete("/")
async def clear_watchlist():
    """
    Clear entire watchlist
    """
    _save_watchlist([])
    return {"message": "Watchlist cleared", "symbols": []}

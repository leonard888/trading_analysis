"""
Stock Service - Fetches IDX stock data via yfinance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from cachetools import TTLCache
import json

# Cache stock data for 5 minutes
_cache = TTLCache(maxsize=100, ttl=300)

# Pre-configured IDX stocks
DEFAULT_STOCKS = {
    # Commodity stocks
    "BUMI.JK": {"name": "Bumi Resources", "sector": "Coal"},
    "ADRO.JK": {"name": "Adaro Energy", "sector": "Coal"},
    "ANTM.JK": {"name": "Aneka Tambang", "sector": "Mining"},
    "NCKL.JK": {"name": "Trimegah Bangun Persada", "sector": "Nickel"},
    "BRMS.JK": {"name": "Bumi Resources Minerals", "sector": "Mining"},
    "ARCI.JK": {"name": "Archi Indonesia", "sector": "Gold Mining"},
    "ELSA.JK": {"name": "Elnusa", "sector": "Oil & Gas"},
    # Blue chips
    "BBCA.JK": {"name": "Bank Central Asia", "sector": "Banking"},
    "BBRI.JK": {"name": "Bank Rakyat Indonesia", "sector": "Banking"},
    "TLKM.JK": {"name": "Telkom Indonesia", "sector": "Telecom"},
    "BMRI.JK": {"name": "Bank Mandiri", "sector": "Banking"},
    "BBNI.JK": {"name": "Bank Negara Indonesia", "sector": "Banking"},
    # Technology
    "GOTO.JK": {"name": "GoTo Gojek Tokopedia", "sector": "Technology"},
    "BUKA.JK": {"name": "Bukalapak", "sector": "Technology"},
    "EMTK.JK": {"name": "Elang Mahkota Teknologi", "sector": "Technology"},
    # Consumer
    "UNVR.JK": {"name": "Unilever Indonesia", "sector": "Consumer"},
    "ICBP.JK": {"name": "Indofood CBP", "sector": "Consumer"},
    "MYOR.JK": {"name": "Mayora Indah", "sector": "Consumer"},
    # Healthcare
    "SIDO.JK": {"name": "Sido Muncul", "sector": "Healthcare"},
    "KLBF.JK": {"name": "Kalbe Farma", "sector": "Healthcare"},
    "INAF.JK": {"name": "Indofarma", "sector": "Healthcare"},
    
    # New Additions
    "BULL.JK": {"name": "Buana Lintas Lautan", "sector": "Transportation"},
    "NINE.JK": {"name": "Techno9 Indonesia", "sector": "Technology"},
    "BUVA.JK": {"name": "Bukit Uluwatu Villa", "sector": "Property"},
    "INET.JK": {"name": "Sinergi Inti Andalan Prima", "sector": "Technology"},
    "DEWA.JK": {"name": "Darma Henwa", "sector": "Infrastructure"},
    "MINA.JK": {"name": "Sanurhasta Mitra", "sector": "Property"},
    "MLPL.JK": {"name": "Multipolar", "sector": "Holding"},
    "GTSI.JK": {"name": "GTS Internasional", "sector": "Transportation"},
    "HUMI.JK": {"name": "Humpuss Maritim Internasional", "sector": "Transportation"},
    "CDIA.JK": {"name": "Cicadas Perkasa", "sector": "Industrial"},
    "TPIA.JK": {"name": "Chandra Asri Petrochemical", "sector": "Basic Industry"},
    "PTRO.JK": {"name": "Petrosea", "sector": "Infrastructure"},
    "HRTA.JK": {"name": "Hartadinata Abadi", "sector": "Consumer"},
    "BRPT.JK": {"name": "Barito Pacific", "sector": "Basic Industry"},
    "BREN.JK": {"name": "Barito Renewables Energy", "sector": "Infrastructure"},
    "BKSL.JK": {"name": "Sentul City", "sector": "Property"},
}

def get_stock_data(
    symbol: str, 
    period: str = "1mo",
    interval: str = "1d"
) -> Dict[str, Any]:
    """
    Get stock data for a given symbol
    
    Args:
        symbol: Stock symbol (e.g., BBCA.JK for IDX stocks)
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    """
    cache_key = f"{symbol}_{period}_{interval}"
    
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        # Ensure symbol has .JK suffix for IDX stocks
        if not symbol.endswith('.JK') and not symbol.endswith('=F'):
            symbol = f"{symbol}.JK"
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": f"No data found for {symbol}", "symbol": symbol}
        
        # Get stock info
        info = ticker.info
        
        # Format data for frontend
        data = {
            "symbol": symbol,
            "name": info.get("longName", DEFAULT_STOCKS.get(symbol, {}).get("name", symbol)),
            "sector": DEFAULT_STOCKS.get(symbol, {}).get("sector", info.get("sector", "Unknown")),
            "currency": info.get("currency", "IDR"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previousClose": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "dayHigh": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "dayLow": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "marketCap": info.get("marketCap"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "history": []
        }
        
        # Add historical data
        for idx, row in hist.iterrows():
            data["history"].append({
                "time": int(idx.timestamp()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            })
        
        _cache[cache_key] = data
        return data
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

def search_stocks(query: str) -> List[Dict[str, str]]:
    """
    Search for IDX stocks by name or symbol
    """
    query = query.upper()
    results = []
    
    for symbol, info in DEFAULT_STOCKS.items():
        if query in symbol or query in info["name"].upper():
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "sector": info["sector"]
            })
    
    return results[:10]  # Limit to 10 results

def get_multiple_stocks(symbols: List[str]) -> List[Dict[str, Any]]:
    """
    Get data for multiple stocks at once
    """
    results = []
    for symbol in symbols:
        data = get_stock_data(symbol, period="1d")
        if "error" not in data:
            results.append({
                "symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "price": data["currentPrice"],
                "change": ((data["currentPrice"] or 0) - (data["previousClose"] or 0)),
                "changePercent": (
                    ((data["currentPrice"] or 0) - (data["previousClose"] or 0)) 
                    / (data["previousClose"] or 1) * 100
                )
            })
    return results

def get_all_sectors() -> List[str]:
    """
    Get list of all available sectors
    """
    sectors = set()
    for info in DEFAULT_STOCKS.values():
        sectors.add(info["sector"])
    return sorted(list(sectors))

"""
Mini Bloomberg Terminal - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# ... existing imports ...
from routers import stocks, commodities, news, forecast, analysis, watchlist, position, portfolio, screener

app = FastAPI(
    title="Trading Forecast API",
    description="Mini Bloomberg Terminal with ML-powered forecasting",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Custom static files handler with no-cache headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add no-cache headers for static files
        if request.url.path.startswith('/js/') or request.url.path.startswith('/styles/'):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Mount static directories
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/styles", StaticFiles(directory=os.path.join(FRONTEND_DIR, "styles")), name="styles")

# Include routers
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(commodities.router, prefix="/api/commodities", tags=["Commodities"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(position.router, prefix="/api/position", tags=["Position"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(screener.router, prefix="/api/screener", tags=["Screener"])

@app.get("/")
async def read_index():
    response = FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))
    # Prevent caching to ensure latest files are served
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Disable reload when running via launcher (pythonw) to avoid subprocess issues
    # The reloader spawns child processes that fail silently with pythonw
    # For development, run directly with: python main.py --reload
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

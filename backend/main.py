"""
Mini Bloomberg Terminal - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import stocks, commodities, news, forecast, analysis, watchlist, position

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

# Include routers
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(commodities.router, prefix="/api/commodities", tags=["Commodities"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(position.router, prefix="/api/position", tags=["Position"])

@app.get("/")
async def root():
    return {"message": "Trading Forecast API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

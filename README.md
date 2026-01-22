# Trading Forecast Terminal

A mini Bloomberg Terminal with ML-powered forecasting for Indonesian stocks (IDX) and commodities.

![Terminal Preview](https://via.placeholder.com/800x400?text=Trading+Forecast+Terminal)

## Features

- 📈 **Real-time Charts** - Interactive candlestick charts with TradingView Lightweight Charts
- 🔮 **ML Forecasting** - LSTM + Random Forest ensemble predictions
- 📊 **Technical Analysis** - RSI, MACD, Bollinger Bands, pattern detection
- 📰 **News Aggregation** - CNBC, Bloomberg, Reuters + Indonesian sources
- 🔍 **Stock Search** - Search any IDX stock (banking, tech, mining, etc.)
- 💰 **Commodities** - Gold, Oil, Silver, Copper price tracking

## Quick Start

### Windows
```batch
# Double-click start.bat or run:
.\start.bat
```

### Manual Start
```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Start backend server
python main.py

# 3. Open frontend in browser
# Open frontend/index.html
```

## Project Structure

```
trading_analysis/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # API entry point
│   ├── requirements.txt    # Python dependencies
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic
│   ├── analysis/           # Technical analysis
│   └── ml/                 # Machine learning models
│
├── frontend/               # Static web frontend
│   ├── index.html         # Main dashboard
│   ├── styles/            # CSS styles
│   └── js/                # JavaScript modules
│
└── start.bat              # Windows startup script
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stocks/{symbol}` | Get stock data |
| `GET /api/stocks/search/query?q=` | Search stocks |
| `GET /api/commodities/{type}` | Get commodity prices |
| `GET /api/news/` | Get aggregated news |
| `GET /api/analysis/{symbol}` | Technical analysis |
| `GET /api/forecast/{symbol}` | ML predictions |

## Supported Stocks

### Commodity Stocks
- BUMI, ADRO, ANTM, NCKL, BRMS, ARCI, ELSA

### Blue Chips
- BBCA, BBRI, BMRI, TLKM, and more...

### Search for Any IDX Stock
Use the search bar to add stocks from any sector!

## Tech Stack

- **Backend**: Python, FastAPI, yfinance, scikit-learn, TensorFlow
- **Frontend**: HTML5, CSS3, JavaScript, TradingView Charts
- **Data Sources**: Yahoo Finance, RSS feeds

## License

MIT License

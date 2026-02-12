/**
 * API Module - Handles all backend communication
 */

const API_BASE = 'http://localhost:8000/api';

const api = {
    /**
     * Fetch stock data
     */
    async getStock(symbol, period = '1mo', interval = '1d') {
        try {
            const response = await fetch(
                `${API_BASE}/stocks/${symbol}?period=${period}&interval=${interval}`
            );
            if (!response.ok) throw new Error('Stock not found');
            return await response.json();
        } catch (error) {
            console.error('Error fetching stock:', error);
            throw error;
        }
    },

    /**
     * Get all default stocks
     */
    async getDefaultStocks() {
        try {
            const response = await fetch(`${API_BASE}/stocks/`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching default stocks:', error);
            return [];
        }
    },

    /**
     * Search stocks
     */
    async searchStocks(query) {
        try {
            const response = await fetch(
                `${API_BASE}/stocks/search/query?q=${encodeURIComponent(query)}`
            );
            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.error('Error searching stocks:', error);
            return [];
        }
    },

    /**
     * Fetch commodity data
     */
    async getCommodity(type, period = '1mo', interval = '1d') {
        try {
            const response = await fetch(
                `${API_BASE}/commodities/${type}?period=${period}&interval=${interval}`
            );
            if (!response.ok) throw new Error('Commodity not found');
            return await response.json();
        } catch (error) {
            console.error('Error fetching commodity:', error);
            throw error;
        }
    },

    /**
     * Get all commodities
     */
    async getAllCommodities() {
        try {
            const response = await fetch(`${API_BASE}/commodities/`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching commodities:', error);
            return [];
        }
    },

    /**
     * Get commodity forecast with price predictions
     */
    async getCommodityForecast(type) {
        try {
            const response = await fetch(`${API_BASE}/commodities/${type}/forecast`);
            if (!response.ok) throw new Error('Commodity forecast not found');
            return await response.json();
        } catch (error) {
            console.error('Error fetching commodity forecast:', error);
            throw error;
        }
    },

    /**
     * Get news
     */
    async getNews(category = null, limit = 50) {
        try {
            let url = `${API_BASE}/news/?limit=${limit}`;
            if (category) url += `&category=${category}`;
            const response = await fetch(url);
            const data = await response.json();
            return data.articles || [];
        } catch (error) {
            console.error('Error fetching news:', error);
            return [];
        }
    },

    /**
     * Get news for specific stock
     */
    async getStockNews(symbol, limit = 20) {
        try {
            const response = await fetch(
                `${API_BASE}/news/stock/${symbol}?limit=${limit}`
            );
            const data = await response.json();
            return data.articles || [];
        } catch (error) {
            console.error('Error fetching stock news:', error);
            return [];
        }
    },

    /**
     * Get technical analysis
     */
    async getAnalysis(symbol, period = '3mo') {
        try {
            const response = await fetch(
                `${API_BASE}/analysis/${symbol}?period=${period}`
            );
            if (!response.ok) throw new Error('Analysis failed');
            return await response.json();
        } catch (error) {
            console.error('Error fetching analysis:', error);
            throw error;
        }
    },

    /**
     * Get forecast
     */
    async getForecast(symbol, days = 5) {
        try {
            const response = await fetch(
                `${API_BASE}/forecast/${symbol}?days=${days}`
            );
            if (!response.ok) throw new Error('Forecast failed');
            return await response.json();
        } catch (error) {
            console.error('Error fetching forecast:', error);
            throw error;
        }
    },

    /**
     * Get quick forecast (no ML training)
     */
    async getQuickForecast(symbol) {
        try {
            const response = await fetch(`${API_BASE}/forecast/${symbol}/quick?_t=${Date.now()}`);
            if (!response.ok) throw new Error('Quick forecast failed');
            return await response.json();
        } catch (error) {
            console.error('Error fetching quick forecast:', error);
            throw error;
        }
    },

    /**
     * Watchlist operations
     */
    async getWatchlist() {
        try {
            const response = await fetch(`${API_BASE}/watchlist/`);
            const data = await response.json();
            return data.symbols || [];
        } catch (error) {
            console.error('Error fetching watchlist:', error);
            return [];
        }
    },

    async addToWatchlist(symbol) {
        try {
            const response = await fetch(`${API_BASE}/watchlist/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            return await response.json();
        } catch (error) {
            console.error('Error adding to watchlist:', error);
            throw error;
        }
    },

    async removeFromWatchlist(symbol) {
        try {
            const response = await fetch(`${API_BASE}/watchlist/remove`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            return await response.json();
        } catch (error) {
            console.error('Error removing from watchlist:', error);
            throw error;
        }
    },

    /**
     * Analyze position for recommendation
     */
    async analyzePosition(symbol, avgPrice, quantity, remainingBalance = 0) {
        try {
            const response = await fetch(`${API_BASE}/position/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    avg_price: avgPrice,
                    quantity: quantity,
                    remaining_balance: remainingBalance
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Position analysis failed');
            }
            return await response.json();
        } catch (error) {
            console.error('Error analyzing position:', error);
            throw error;
        }
    },

    // ==================== Portfolio API ====================

    /**
     * Get all portfolio positions with analysis
     */
    async getPortfolio() {
        try {
            const response = await fetch(`${API_BASE}/portfolio/?_t=${Date.now()}`);
            if (!response.ok) throw new Error('Failed to get portfolio');
            return await response.json();
        } catch (error) {
            console.error('Error getting portfolio:', error);
            throw error;
        }
    },

    /**
     * Add a position to portfolio
     */
    async addPortfolioPosition(symbol, avgPrice, quantity, remainingBalance = 0) {
        try {
            const response = await fetch(`${API_BASE}/portfolio/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    avg_price: avgPrice,
                    quantity: quantity,
                    remaining_balance: remainingBalance
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to add position');
            }
            return await response.json();
        } catch (error) {
            console.error('Error adding position:', error);
            throw error;
        }
    },

    /**
     * Update a portfolio position
     */
    async updatePortfolioPosition(symbol, avgPrice, quantity, remainingBalance) {
        try {
            const response = await fetch(`${API_BASE}/portfolio/${encodeURIComponent(symbol)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    avg_price: avgPrice,
                    quantity: quantity,
                    remaining_balance: remainingBalance
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update position');
            }
            return await response.json();
        } catch (error) {
            console.error('Error updating position:', error);
            throw error;
        }
    },

    /**
     * Remove a position from portfolio (sell)
     */
    async removePortfolioPosition(symbol) {
        try {
            const response = await fetch(`${API_BASE}/portfolio/${encodeURIComponent(symbol)}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to remove position');
            }
            return await response.json();
        } catch (error) {
            console.error('Error removing position:', error);
            throw error;
        }
    },

    // ==================== Screener API ====================

    // Scan all stocks for screener
    async scanStocks() {
        try {
            const response = await fetch(`${API_BASE}/screener/scan`);
            if (!response.ok) throw new Error('Scan failed');
            return await response.json();
        } catch (error) {
            console.error('Error scanning stocks:', error);
            throw error;
        }
    }
};

// Export for use in other modules
window.api = api;

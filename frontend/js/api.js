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
            const response = await fetch(`${API_BASE}/forecast/${symbol}/quick`);
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
    }
};

// Export for use in other modules
window.api = api;

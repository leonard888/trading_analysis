/**
 * Main Application Module
 */

class TradingApp {
    constructor() {
        this.chart = null;
        this.currentSymbol = null;
        this.currentPeriod = '6mo';
        this.newsCategory = null;

        // Default watchlist
        this.defaultWatchlist = [
            'FAST.JK', 'BREN.JK', 'BRPT.JK', 'TPIA.JK', 'HRTA.JK',
            'ADRO.JK', 'PTRO.JK', 'DEWA.JK', 'BUMI.JK',
            'BULL.JK', 'GTSI.JK', 'HUMI.JK', 'BKSL.JK',
            'MLPL.JK', 'INET.JK', 'NINE.JK', 'ANTM.JK',
            'CDIA.JK', 'MINA.JK', 'BUVA.JK', 'BBCA.JK'
        ];

        // Default commodities
        this.defaultCommodities = [
            { symbol: 'GC=F', name: 'Gold' },
            { symbol: 'CL=F', name: 'Crude Oil' },
            { symbol: 'SI=F', name: 'Silver' },
            { symbol: 'MTF=F', name: 'Coal' },
            { symbol: '^SPGSNI', name: 'Nickel' },
            { symbol: 'HG=F', name: 'Copper' }
        ];
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('🚀 Initializing Trading Forecast Terminal...');

        // Initialize chart
        this.chart = new TradingChart('chartContainer');
        this.chart.init();

        // Setup event listeners
        this.setupEventListeners();

        // Start clock
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);

        // Load initial data
        await this.loadInitialData();

        console.log('✅ Trading Forecast Terminal ready!');
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('searchInput');
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.handleSearch(e.target.value);
            }, 300);
        });

        searchInput.addEventListener('focus', () => {
            const results = document.getElementById('searchResults');
            if (results.children.length > 0) {
                results.classList.add('active');
            }
        });

        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                document.getElementById('searchResults').classList.remove('active');
            }
        });

        // Period buttons
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentPeriod = e.target.dataset.period;
                if (this.currentSymbol) {
                    this.loadStockData(this.currentSymbol, this.currentPeriod);
                }
            });
        });

        // News tabs
        document.querySelectorAll('.news-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.news-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.newsCategory = e.target.dataset.category || null;
                this.loadNews();
            });
        });

        // Refresh watchlist
        document.getElementById('refreshWatchlist')?.addEventListener('click', () => {
            this.loadWatchlist();
        });

        // Portfolio Management - Show add form
        document.getElementById('showAddPositionBtn')?.addEventListener('click', () => {
            this.showAddPositionForm();
        });

        // Portfolio Management - Cancel add
        document.getElementById('cancelAddPositionBtn')?.addEventListener('click', () => {
            this.hideAddPositionForm();
        });

        // Portfolio Management - Confirm add
        document.getElementById('confirmAddPositionBtn')?.addEventListener('click', () => {
            this.addPortfolioPosition();
        });
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        this.showLoading(true);

        try {
            // Load watchlist (includes commodities now)
            await this.loadWatchlist();

            // Load news
            await this.loadNews();

            // Load portfolio positions
            await this.loadPortfolio();

            // Load first stock
            if (this.defaultWatchlist.length > 0) {
                await this.selectStock(this.defaultWatchlist[0]);
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
        }

        this.showLoading(false);
    }

    /**
     * Load watchlist (Stocks and Commodities)
     * Fetches saved watchlist from backend and merges with defaults
     */
    async loadWatchlist() {
        try {
            // Fetch saved watchlist from backend
            const savedWatchlist = await window.api.getWatchlist();

            if (savedWatchlist && savedWatchlist.length > 0) {
                // Use saved watchlist (user has customized it)
                this.defaultWatchlist = savedWatchlist;
            } else {
                // First time: save default watchlist to backend
                for (const symbol of this.defaultWatchlist) {
                    await window.api.addToWatchlist(symbol);
                }
            }
        } catch (error) {
            console.error('Error loading watchlist from backend:', error);
            // Continue with default watchlist if backend fails
        }

        await this.loadSection('stockWatchlist', this.defaultWatchlist);
        await this.loadSection('commodityWatchlist', this.defaultCommodities, true);
    }

    /**
     * Helper to load a watchlist section
     */
    async loadSection(elementId, items, isCommodity = false) {
        const container = document.getElementById(elementId);
        if (!container) return;

        container.innerHTML = '<div class="loading-spinner small"></div>';

        try {
            container.innerHTML = '';

            for (const item of items) {
                // Determine symbol and display name
                const symbol = isCommodity ? item.symbol : item;
                const displayName = isCommodity ? item.name : null;

                try {
                    // Fetch data
                    const stockData = await window.api.getStock(symbol);
                    if (displayName) stockData.name = displayName; // Override name for commodities

                    // Determine commodity type key if needed
                    let commodityType = null;
                    if (isCommodity) {
                        // Find key from defaultCommodities by symbol
                        const found = this.defaultCommodities.find(c => c.symbol === symbol);
                        if (found) {
                            // Map symbol back to type key (e.g. 'gold' from GC=F)
                            // Since defaultCommodities is an array of {symbol, name}, we need the key.
                            // Actually COMMODITIES keys are just lower case? 
                            // The selectCommodity expects 'gold', 'silver', etc.
                            // We used defaultCommodities array which lost the keys. 
                            // Let's infer type from name or symbol roughly or pass it better.
                            // Simplified: Just pass isCommodity=true and let createWatchlistItem handle it.
                            // But selectCommodity needs the type string (e.g. 'gold').
                            // Let's modify defaultCommodities iteration or mapping.
                        }
                    }

                    const el = this.createWatchlistItem(stockData, isCommodity, item);
                    container.appendChild(el);

                    // Set active if matches current
                    if (this.currentSymbol === symbol) {
                        el.classList.add('active');
                    }
                } catch (e) {
                    console.error(`Failed to load ${symbol}`, e);
                }
            }
        } catch (error) {
            console.error(`Error loading section ${elementId}:`, error);
            container.innerHTML = '<div class="error-message">Failed to load</div>';
        }
    }

    /**
     * Create watchlist item element
     */
    createWatchlistItem(data, isCommodity = false, originalItem = null) {
        const item = document.createElement('div');
        item.className = `watchlist-item ${data.symbol === this.currentSymbol ? 'active' : ''}`;
        item.dataset.symbol = data.symbol;

        const changeClass = data.changePercent >= 0 ? 'positive' : 'negative';
        const changeSign = data.changePercent >= 0 ? '+' : '';

        // Use name if available (especially for commodities)
        const displayName = data.name || data.symbol.replace('.JK', '').replace('=F', '');

        item.innerHTML = `
            <div class="item-info">
                <span class="symbol">${data.symbol.replace('.JK', '').replace('=F', '')}</span>
                <span class="name">${displayName}</span>
            </div>
            <div class="item-price">
                <span class="price">${this.formatPrice(data.currentPrice)}</span>
                <span class="change ${changeClass}">${data.changePercent ? (changeSign + data.changePercent.toFixed(2) + '%') : '-'}</span>
            </div>
            ${!isCommodity ? '<button class="remove-btn" title="Remove from watchlist">×</button>' : ''}
        `;

        // Handle remove button click
        const removeBtn = item.querySelector('.remove-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFromWatchlist(data.symbol);
            });
        }

        item.addEventListener('click', () => {
            // Update active state across all lists
            document.querySelectorAll('.watchlist-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            if (isCommodity && originalItem) {
                // Infer type for selectCommodity
                // defaultCommodities was [{symbol, name}, ...]. 
                // We need to map back to keys: gold, silver, oil etc.
                // Or we can just try to lowercase the first word of name? 
                // "Gold Futures" -> "Gold" -> "gold"
                // "Crude Oil..." -> "Oil" -> "oil"
                // This is brittle. Better if we stored the type key in defaultCommodities.

                // Better approach: Let's fix defaultCommodities structure in constructor
                // But for now, let's map known symbols to types
                const symbolMap = {
                    'GC=F': 'gold', 'SI=F': 'silver', 'CL=F': 'oil', 'BZ=F': 'brent',
                    'HG=F': 'copper', 'PL=F': 'platinum', 'PA=F': 'palladium',
                    'NG=F': 'natural_gas', 'MTF=F': 'coal', '^SPGSNI': 'nickel'
                };
                const type = symbolMap[data.symbol] || data.symbol;
                this.selectCommodity(type);
            } else {
                this.selectStock(data.symbol);
            }
        });

        return item;
    }



    /**
     * Load news
     */
    async loadNews() {
        const newsEl = document.getElementById('newsList');
        newsEl.innerHTML = '<div class="loading-text">Loading news...</div>';

        try {
            let articles = [];

            try {
                articles = await window.api.getNews(this.newsCategory, 20);
            } catch {
                // Show placeholder
                articles = [];
            }

            if (articles.length === 0) {
                newsEl.innerHTML = `
                    <div class="news-placeholder">
                        <p>Unable to load news.</p>
                        <p>Make sure the backend is running.</p>
                    </div>
                `;
                return;
            }

            newsEl.innerHTML = articles.map(article => `
                <div class="news-item" onclick="window.open('${article.link}', '_blank')">
                    <div class="news-title">${article.title}</div>
                    <div class="news-meta">
                        <span class="news-source">${article.source}</span>
                        <span class="news-sentiment ${article.sentiment?.label || 'neutral'}">
                            ${article.sentiment?.label || 'neutral'}
                        </span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading news:', error);
            newsEl.innerHTML = '<div class="error-text">Failed to load news</div>';
        }
    }

    /**
     * Handle search
     */
    async handleSearch(query) {
        const resultsEl = document.getElementById('searchResults');

        if (!query || query.length < 2) {
            resultsEl.classList.remove('active');
            resultsEl.innerHTML = '';
            return;
        }

        try {
            let results = [];

            try {
                results = await window.api.searchStocks(query);
            } catch {
                // Fallback: filter default watchlist
                results = this.defaultWatchlist
                    .filter(s => s.toLowerCase().includes(query.toLowerCase()))
                    .map(symbol => ({
                        symbol,
                        name: symbol.replace('.JK', ''),
                        sector: 'IDX'
                    }));
            }

            if (results.length === 0) {
                resultsEl.innerHTML = '<div class="search-result-item">No results found</div>';
            } else {
                resultsEl.innerHTML = results.map(r => {
                    const isInWatchlist = this.defaultWatchlist.includes(r.symbol);
                    return `
                    <div class="search-result-item" data-symbol="${r.symbol}">
                        <div class="result-info">
                            <span class="symbol">${r.symbol.replace('.JK', '')}</span>
                            <span class="name">${r.name}</span>
                        </div>
                        <div class="result-actions">
                            <span class="sector">${r.sector}</span>
                            ${!isInWatchlist ? `<button class="add-watchlist-btn" title="Add to Watchlist">+</button>` : '<span class="in-watchlist">✓</span>'}
                        </div>
                    </div>
                `}).join('');

                resultsEl.querySelectorAll('.search-result-item').forEach(item => {
                    // Handle add to watchlist button
                    const addBtn = item.querySelector('.add-watchlist-btn');
                    if (addBtn) {
                        addBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            this.addToWatchlist(item.dataset.symbol);
                            resultsEl.classList.remove('active');
                            document.getElementById('searchInput').value = '';
                        });
                    }

                    // Handle click on the item itself (select stock)
                    item.addEventListener('click', () => {
                        this.selectStock(item.dataset.symbol);
                        resultsEl.classList.remove('active');
                        document.getElementById('searchInput').value = '';
                    });
                });
            }

            resultsEl.classList.add('active');
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    /**
     * Select and load a stock
     */
    async selectStock(symbol) {
        this.currentSymbol = symbol;

        // Update active state in watchlist
        document.querySelectorAll('.watchlist-item').forEach(item => {
            item.classList.toggle('active', item.dataset.symbol === symbol);
        });

        // Update header
        document.getElementById('stockSymbol').textContent = symbol;
        document.getElementById('stockName').textContent = 'Loading...';

        // Load data
        await this.loadStockData(symbol, this.currentPeriod);

        // Load analysis and forecast
        this.loadAnalysis(symbol);
        this.loadForecast(symbol);
    }

    /**
     * Select and load a commodity
     */
    async selectCommodity(type) {
        const symbol = type.toUpperCase() + '=F';
        this.currentSymbol = symbol;
        this.currentCommodityType = type;

        document.getElementById('stockSymbol').textContent = symbol;
        document.getElementById('stockName').textContent = type.charAt(0).toUpperCase() + type.slice(1);

        try {
            const data = await window.api.getCommodity(type, this.currentPeriod);

            if (data && data.history) {
                this.chart.updateData(data);
                this.updatePriceDisplay(data);
            }

            // Load commodity forecast
            this.loadCommodityForecast(type);
        } catch (error) {
            console.error('Error loading commodity:', error);
        }
    }

    /**
     * Load stock data
     */
    async loadStockData(symbol, period) {
        try {
            const data = await window.api.getStock(symbol, period);

            if (data && data.history) {
                // Update chart
                this.chart.updateData(data);

                // Update UI
                document.getElementById('stockName').textContent = data.name || symbol;
                this.updatePriceDisplay(data);

                // Add SMA overlay if enough data
                if (data.history.length >= 20) {
                    this.chart.addSMALine(data.history, 20, '#58a6ff');
                }
            }
        } catch (error) {
            console.error('Error loading stock data:', error);
            document.getElementById('stockName').textContent = symbol;
            document.getElementById('currentPrice').textContent = 'Data unavailable';
        }
    }

    /**
     * Update price display
     */
    updatePriceDisplay(data) {
        const priceEl = document.getElementById('currentPrice');
        const changeEl = document.getElementById('priceChange');

        const price = data.currentPrice || (data.history && data.history.length > 0
            ? data.history[data.history.length - 1].close
            : null);

        const prevClose = data.previousClose || (data.history && data.history.length > 1
            ? data.history[data.history.length - 2].close
            : price);

        if (price) {
            priceEl.textContent = this.formatPrice(price);

            if (prevClose) {
                const change = price - prevClose;
                const changePercent = (change / prevClose) * 100;

                changeEl.textContent = `${change >= 0 ? '+' : ''}${this.formatPrice(change)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
                changeEl.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
            }
        } else {
            priceEl.textContent = '-';
            changeEl.textContent = '-';
            changeEl.className = 'price-change';
        }
    }

    /**
     * Load technical analysis
     */
    async loadAnalysis(symbol) {
        try {
            const data = await window.api.getAnalysis(symbol);

            if (data && data.indicators) {
                this.updateIndicators(data.indicators);
                this.updateSignals(data.indicators.signals);
            }

            if (data && data.patterns) {
                this.updatePatterns(data.patterns);
            }
        } catch (error) {
            console.error('Error loading analysis:', error);
            this.resetIndicators();
        }
    }

    /**
     * Update indicators display
     */
    updateIndicators(indicators) {
        document.getElementById('rsiValue').textContent = indicators.rsi?.toFixed(2) || '-';
        document.getElementById('macdValue').textContent = indicators.macd?.value?.toFixed(4) || '-';
        document.getElementById('sma20Value').textContent = indicators.sma20?.toLocaleString() || '-';
        document.getElementById('sma50Value').textContent = indicators.sma50?.toLocaleString() || '-';
        document.getElementById('bbUpperValue').textContent = indicators.bollingerBands?.upper?.toLocaleString() || '-';
        document.getElementById('bbLowerValue').textContent = indicators.bollingerBands?.lower?.toLocaleString() || '-';
    }

    /**
     * Reset indicators display
     */
    resetIndicators() {
        ['rsiValue', 'macdValue', 'sma20Value', 'sma50Value', 'bbUpperValue', 'bbLowerValue'].forEach(id => {
            document.getElementById(id).textContent = '-';
        });
    }

    /**
     * Update signals display
     */
    updateSignals(signals) {
        const signalsEl = document.getElementById('signalsContent');

        if (!signals) {
            signalsEl.innerHTML = '<div class="signal-placeholder">No signals available</div>';
            return;
        }

        const signalItems = Object.entries(signals)
            .filter(([key]) => key !== 'overall')
            .map(([key, value]) => {
                const displayName = key.replace(/([A-Z])/g, ' $1').trim();
                return `
                    <div class="signal-item">
                        <span class="signal-name">${displayName}</span>
                        <span class="signal-badge ${value.signal}">${value.signal.toUpperCase()}</span>
                    </div>
                `;
            });

        // Add overall signal at top
        if (signals.overall) {
            signalItems.unshift(`
                <div class="signal-item" style="border: 1px solid var(--accent-blue); border-radius: 8px;">
                    <span class="signal-name"><strong>Overall Signal</strong></span>
                    <span class="signal-badge ${signals.overall.signal}">${signals.overall.signal.toUpperCase()}</span>
                </div>
            `);
        }

        signalsEl.innerHTML = signalItems.join('');
    }

    /**
     * Update patterns display
     */
    updatePatterns(patterns) {
        const patternsEl = document.getElementById('patternsContent');

        if (!patterns || !patterns.detectedPatterns || patterns.detectedPatterns.length === 0) {
            patternsEl.innerHTML = '<div class="pattern-placeholder">No patterns detected</div>';
            return;
        }

        patternsEl.innerHTML = patterns.detectedPatterns.map(p => `
            <div class="pattern-item">
                <div class="pattern-name">${p.pattern.replace(/_/g, ' ').toUpperCase()}</div>
                <div class="pattern-type">${p.type} - Confidence: ${(p.confidence * 100).toFixed(0)}%</div>
            </div>
        `).join('');
    }

    /**
     * Load forecast
     */
    async loadForecast(symbol) {
        const forecastEl = document.getElementById('forecastContent');
        forecastEl.innerHTML = '<div class="forecast-placeholder">Loading forecast...</div>';

        try {
            const data = await window.api.getQuickForecast(symbol);

            if (data && data.forecast) {
                const forecast = data.forecast;
                console.log('Forecast Data:', forecast); // Debug log
                console.log('Next Day Prediction:', forecast.nextDayPrediction); // Debug log
                const signalClass = forecast.signal === 'bullish' ? 'bullish' :
                    forecast.signal === 'bearish' ? 'bearish' : '';

                // Build reasons HTML
                let reasonsHtml = '';
                if (forecast.reasons && forecast.reasons.length > 0) {
                    reasonsHtml = `
                        <div class="forecast-reasons">
                            <div class="reasons-title">📋 Reasoning</div>
                            ${forecast.reasons.map(r => `
                                <div class="reason-item ${r.signal}">
                                    <span class="reason-category">${r.category}</span>
                                    <span class="reason-badge ${r.signal}">${r.signal === 'bullish' ? '🟢' : r.signal === 'bearish' ? '🔴' : '⚪'}</span>
                                    <div class="reason-detail">${r.detail}</div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                // Commodity correlation HTML
                let commodityHtml = '';
                if (data.commodityCorrelation && data.commodityCorrelation.commodity && data.commodityCorrelation.analysis) {
                    const comm = data.commodityCorrelation;
                    commodityHtml = `
                        <div class="commodity-correlation">
                            <div class="correlation-title">⛏️ ${comm.commodity} Correlation</div>
                            <div class="correlation-data">
                                <span>Price: $${comm.analysis.currentPrice}</span>
                                <span class="${comm.analysis.monthlyChange >= 0 ? 'positive' : 'negative'}">
                                    ${comm.analysis.monthlyChange >= 0 ? '+' : ''}${comm.analysis.monthlyChange?.toFixed(1)}% (month)
                                </span>
                            </div>
                        </div>
                    `;
                }

                forecastEl.innerHTML = `
                    <!-- Fear & Greed Gauge -->
                    <div class="fear-greed-gauge">
                        <div class="gauge-title">Sentiment Index</div>
                        <div class="gauge-wrapper">
                            <div class="gauge-body">
                                <div class="gauge-inner"></div>
                            </div>
                            <div class="gauge-needle" id="gaugeNeedle"></div>
                        </div>
                        <div class="gauge-labels">
                            <span class="gauge-label fear">Fear</span>
                            <span class="gauge-label greed">Greed</span>
                        </div>
                        <div class="gauge-value">
                            <span class="gauge-score" id="gaugeScore">--</span>
                            <span class="gauge-status" id="gaugeStatus">Loading...</span>
                        </div>
                    </div>

                    <div class="forecast-card ${signalClass}">
                        <div class="forecast-signal ${signalClass}">
                            ${forecast.signal === 'bullish' ? '📈' : forecast.signal === 'bearish' ? '📉' : '➡️'}
                            ${forecast.signal.toUpperCase()}
                        </div>
                        <div class="forecast-confidence">
                            Confidence: ${(forecast.confidence * 100).toFixed(1)}%
                        </div>
                        <div class="forecast-summary">
                            ${forecast.summary || ''}
                        </div>
                        <div class="forecast-validity" style="font-size: 0.85em; opacity: 0.8; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                            Valid until: ${forecast.validity || '1 week'}
                        </div>
                        
                        <!-- Next Day Prediction -->
                        ${forecast.nextDayPrediction && forecast.nextDayPrediction.high ? `
                        <div class="next-day-prediction" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="font-size: 0.9em; margin-bottom: 4px; color: var(--text-secondary);">📅 Prediction for Tomorrow</div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="text-align: left;">
                                    <div style="font-size: 0.8em; color: var(--text-muted);">Low</div>
                                    <div style="font-weight: 600; color: var(--accent-red);">${this.formatPrice(forecast.nextDayPrediction.low)}</div>
                                </div>
                                <div style="flex-grow: 1; height: 4px; background: rgba(255,255,255,0.1); margin: 0 12px; border-radius: 2px; position: relative;">
                                    <div style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 6px; height: 6px; background: var(--text-muted); border-radius: 50%;"></div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.8em; color: var(--text-muted);">High</div>
                                    <div style="font-weight: 600; color: var(--accent-green);">${this.formatPrice(forecast.nextDayPrediction.high)}</div>
                                </div>
                            </div>
                            <div style="font-size: 0.75em; text-align: center; margin-top: 4px; opacity: 0.7;">
                                Volatility: ±${this.formatPrice(forecast.nextDayPrediction.volatility)}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    ${commodityHtml}

                    <!-- Trading Plan Section -->
                    ${data.tradingPlan ? `
                    <div class="trading-plan-section ${data.tradingPlan.action?.toLowerCase()}">
                        <div class="section-title">🛡️ Trading Plan</div>
                        <div class="plan-grid">
                            <div class="plan-item action">
                                <span class="label">Action</span>
                                <span class="value ${data.tradingPlan.action?.toLowerCase()}">${data.tradingPlan.action}</span>
                            </div>
                            <div class="plan-item">
                                <span class="label">Entry Zone</span>
                                <span class="value">${data.tradingPlan.entry_zone || '-'}</span>
                            </div>
                            <div class="plan-item profit">
                                <span class="label">Take Profit</span>
                                <span class="value">${data.tradingPlan.take_profit ? this.formatPrice(data.tradingPlan.take_profit) : '-'}</span>
                            </div>
                            <div class="plan-item loss">
                                <span class="label">Stop Loss</span>
                                <span class="value">${data.tradingPlan.stop_loss ? this.formatPrice(data.tradingPlan.stop_loss) : '-'}</span>
                            </div>
                            <div class="plan-item rr-ratio">
                                <span class="label">Risk/Reward</span>
                                <span class="value">${data.tradingPlan.risk_reward || '-'}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}

                    <!-- Support & Resistance Section -->
                    ${data.supportResistance ? `
                    <div class="sr-section">
                        <div class="section-title">📊 Key Levels</div>
                        <div class="sr-grid">
                            <div class="sr-row resistance">
                                <span>R2</span>
                                <span>${this.formatPrice(data.supportResistance.r2)}</span>
                            </div>
                            <div class="sr-row resistance">
                                <span>R1</span>
                                <span>${this.formatPrice(data.supportResistance.r1)}</span>
                            </div>
                            <div class="sr-row pivot">
                                <span>Pivot</span>
                                <span>${this.formatPrice(data.supportResistance.pivot)}</span>
                            </div>
                            <div class="sr-row support">
                                <span>S1</span>
                                <span>${this.formatPrice(data.supportResistance.s1)}</span>
                            </div>
                            <div class="sr-row support">
                                <span>S2</span>
                                <span>${this.formatPrice(data.supportResistance.s2)}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${reasonsHtml}
                `;

                // Update Fear & Greed gauge
                this.updateFearGreedGauge(forecast.signal, forecast.confidence);
            } else {
                forecastEl.innerHTML = '<div class="forecast-placeholder">Forecast unavailable</div>';
            }
        } catch (error) {
            console.error('Error loading forecast:', error);
            forecastEl.innerHTML = '<div class="forecast-placeholder">Unable to load forecast</div>';
        }
    }

    /**
     * Load commodity forecast
     */
    async loadCommodityForecast(type) {
        const forecastEl = document.getElementById('forecastContent');
        forecastEl.innerHTML = '<div class="forecast-placeholder">Loading commodity forecast...</div>';

        try {
            const data = await window.api.getCommodityForecast(type);

            if (data && data.forecast) {
                // Update indicators if available
                if (data.indicators) {
                    this.updateIndicators(data.indicators);
                    this.updateSignals(data.indicators.signals);
                }

                // Update patterns
                this.updatePatterns(data.patterns);

                const forecast = data.forecast;
                const signalClass = forecast.signal === 'bullish' ? 'bullish' :
                    forecast.signal === 'bearish' ? 'bearish' : '';

                forecastEl.innerHTML = `
                    <div class="forecast-card ${signalClass}">
                        <div class="forecast-signal ${signalClass}">
                            ${forecast.signal === 'bullish' ? '📈' : forecast.signal === 'bearish' ? '📉' : '➡️'}
                            ${forecast.signal.toUpperCase()}
                        </div>
                        <div class="forecast-confidence">
                            Confidence: ${(forecast.confidence * 100).toFixed(1)}%
                            <span style="font-size: 0.8em; opacity: 0.8; margin-left: 8px;">• Valid until: ${forecast.validity || '1 week'}</span>
                        </div>
                        <div class="forecast-summary">
                            Predicted Change: <span class="${forecast.predictedChange >= 0 ? 'positive' : 'negative'}">
                                ${forecast.predictedChange > 0 ? '+' : ''}${forecast.predictedChange}%
                            </span>
                        </div>
                        <div class="position-targets" style="margin-top: 10px;">
                            <div class="target-item">
                                <span class="label">Target (Bull)</span>
                                <span class="value">${this.formatPrice(forecast.bullishTarget)}</span>
                            </div>
                            <div class="target-item">
                                <span class="label">Target (Bear)</span>
                                <span class="value">${this.formatPrice(forecast.bearishTarget)}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Support & Resistance Section -->
                    ${data.supportResistance ? `
                    <div class="sr-section">
                        <div class="section-title">📊 Key Levels</div>
                        <div class="sr-grid">
                            ${data.supportResistance.r2 ? `
                            <div class="sr-row resistance">
                                <span>R2</span>
                                <span>${this.formatPrice(data.supportResistance.r2)}</span>
                            </div>` : ''}
                            ${data.supportResistance.r1 ? `
                            <div class="sr-row resistance">
                                <span>R1</span>
                                <span>${this.formatPrice(data.supportResistance.r1)}</span>
                            </div>` : ''}
                            ${data.supportResistance.pivot ? `
                            <div class="sr-row pivot">
                                <span>Pivot</span>
                                <span>${this.formatPrice(data.supportResistance.pivot)}</span>
                            </div>` : ''}
                            ${data.supportResistance.s1 ? `
                            <div class="sr-row support">
                                <span>S1</span>
                                <span>${this.formatPrice(data.supportResistance.s1)}</span>
                            </div>` : ''}
                            ${data.supportResistance.s2 ? `
                            <div class="sr-row support">
                                <span>S2</span>
                                <span>${this.formatPrice(data.supportResistance.s2)}</span>
                            </div>` : ''}
                        </div>
                    </div>
                    ` : ''}

                    <!-- Technical Signals -->
                    <div class="forecast-reasons">
                        <div class="reasons-title">Technical Signals</div>
                        ${data.technicalSignals ? Object.entries(data.technicalSignals)
                        .filter(([k]) => k !== 'overall')
                        .map(([k, v]) => `
                            <div class="position-reason-item">
                                <span style="text-transform:capitalize">${k.replace(/([A-Z])/g, ' $1').trim()}:</span> 
                                <span class="${v.signal}" style="margin-left:auto; font-weight:600">${v.signal.toUpperCase()}</span>
                            </div>
                        `).join('') : ''}
                    </div>
                `;
            } else {
                forecastEl.innerHTML = '<div class="forecast-placeholder">Commodity forecast unavailable</div>';
            }
        } catch (error) {
            console.error('Error loading commodity forecast:', error);
            forecastEl.innerHTML = '<div class="forecast-placeholder">Unable to load commodity forecast</div>';
        }
    }

    /**
     * Format price for display
     */
    formatPrice(price) {
        if (price === null || price === undefined) return '-';
        if (price >= 1000) {
            return price.toLocaleString('id-ID');
        }
        return price.toFixed(2);
    }

    /**
     * Update clock
     */
    updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        document.getElementById('currentTime').textContent = timeStr;

        // Update market status (IDX: 09:00 - 16:00 WIB, Mon-Fri)
        const hours = now.getHours();
        const day = now.getDay();
        const isMarketOpen = day >= 1 && day <= 5 && hours >= 9 && hours < 16;

        const statusEl = document.getElementById('marketStatus');
        const dotEl = document.querySelector('.status-dot');

        if (isMarketOpen) {
            statusEl.textContent = 'Market Open';
            dotEl.classList.add('open');
        } else {
            statusEl.textContent = 'Market Closed';
            dotEl.classList.remove('open');
        }
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }

    /**
     * Analyze current position for recommendation
     */
    async analyzePosition() {
        if (!this.currentSymbol) {
            this.updatePositionResult({ error: 'Please select a stock first' });
            return;
        }

        const avgPrice = parseFloat(document.getElementById('avgPriceInput').value);
        const quantity = parseInt(document.getElementById('quantityInput').value);
        const balance = parseFloat(document.getElementById('balanceInput').value) || 0;

        if (!avgPrice || avgPrice <= 0) {
            this.updatePositionResult({ error: 'Please enter a valid average price' });
            return;
        }

        if (!quantity || quantity <= 0) {
            this.updatePositionResult({ error: 'Please enter a valid quantity' });
            return;
        }

        const resultEl = document.getElementById('positionResult');
        resultEl.innerHTML = '<div class="position-placeholder">Analyzing position...</div>';

        try {
            const result = await window.api.analyzePosition(
                this.currentSymbol,
                avgPrice,
                quantity,
                balance
            );
            this.updatePositionResult(result);
        } catch (error) {
            console.error('Position analysis error:', error);
            this.updatePositionResult({ error: error.message || 'Analysis failed' });
        }
    }

    /**
     * Update position advisor result display
     */
    updatePositionResult(result) {
        const resultEl = document.getElementById('positionResult');

        if (result.error) {
            resultEl.innerHTML = `<div class="position-error">${result.error}</div>`;
            return;
        }

        const action = result.action.toLowerCase();
        const pnlClass = result.position.pnlPercent >= 0 ? 'positive' : 'negative';
        const pnlSign = result.position.pnlPercent >= 0 ? '+' : '';

        // Action emoji mapping
        const actionEmoji = {
            'hold': '⏸️',
            'cut_loss': '🛑',
            'take_profit': '💰',
            'average_down': '⬇️',
            'average_up': '⬆️'
        };

        // Format action display name
        const actionDisplay = result.action.replace('_', ' ');

        resultEl.innerHTML = `
            <div class="position-result-card action-${action}">
                <div class="position-action">
                    <span class="action-badge ${action}">
                        ${actionEmoji[action] || '📊'} ${actionDisplay}
                    </span>
                    <span class="position-confidence">
                        ${(result.confidence * 100).toFixed(0)}% confidence
                    </span>
                </div>

                <div class="position-pnl">
                    <span class="pnl-label">P/L</span>
                    <span class="pnl-value ${pnlClass}">
                        ${pnlSign}${this.formatPrice(result.position.pnl)} (${pnlSign}${result.position.pnlPercent.toFixed(2)}%)
                    </span>
                </div>

                <div class="position-targets">
                    <div class="target-item">
                        <span class="label">Current</span>
                        <span class="value">${this.formatPrice(result.position.currentPrice)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Target</span>
                        <span class="value">${result.targets.targetRange ? result.targets.targetRange : this.formatPrice(result.targets.targetPrice)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Stop Loss</span>
                        <span class="value">${this.formatPrice(result.targets.stopLoss)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Support</span>
                        <span class="value">${this.formatPrice(result.targets.support1)}</span>
                    </div>
                </div>

                ${result.averaging.potentialLots > 0 ? `
                <div class="position-targets">
                    <div class="target-item">
                        <span class="label">Can Buy</span>
                        <span class="value">${result.averaging.potentialLots} lots</span>
                    </div>
                    <div class="target-item">
                        <span class="label">New Avg</span>
                        <span class="value">${this.formatPrice(result.averaging.newAvgPrice)}</span>
                    </div>
                </div>
                ` : ''}

                ${result.entryAdvisor && result.entryAdvisor.suggestedEntry ? `
                <div class="position-targets" style="border-top: 1px solid var(--border-primary); padding-top: 8px; margin-top: 8px;">
                    <div class="target-item">
                        <span class="label">📍 Entry</span>
                        <span class="value">${this.formatPrice(result.entryAdvisor.suggestedEntry)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Zone</span>
                        <span class="value">${result.entryAdvisor.entryZone || '-'}</span>
                    </div>
                </div>
                <div class="position-reason-item" style="font-size: 0.75rem; color: var(--accent-blue);">
                    ${result.entryAdvisor.waitForDip ? '⏳ ' : '✅ '}${result.entryAdvisor.reasoning || ''}
                </div>
                ` : ''}

                <div class="position-reasons">
                    <div class="position-reasons-title">Analysis</div>
                    ${result.reasons.map(r => `
                        <div class="position-reason-item">${r}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Analyze Position
     */
    async analyzePosition() {
        const avgPrice = parseFloat(document.getElementById('avgPriceInput').value);
        const quantity = parseFloat(document.getElementById('quantityInput').value);
        const balance = parseFloat(document.getElementById('balanceInput').value);

        if (!this.currentSymbol || !avgPrice || !quantity) {
            alert('Please select a stock and enter valid position details');
            return;
        }

        const resultEl = document.getElementById('positionResult');
        resultEl.innerHTML = '<div class="position-placeholder">Analyzing position...</div>';

        try {
            const result = await window.api.analyzePosition(
                this.currentSymbol,
                avgPrice,
                quantity,
                balance || 0
            );

            this.renderPositionResult(result);
        } catch (error) {
            console.error('Error analyzing position:', error);
            resultEl.innerHTML = `<div class="position-placeholder" style="color: var(--accent-red)">Error: ${error.message || 'Analysis failed'}</div>`;
        }
    }

    /**
     * Render Position Analysis Result
     */
    renderPositionResult(result) {
        const resultEl = document.getElementById('positionResult');
        if (!result) return;

        const action = result.action === 'BUY' || result.action === 'AVERAGE_UP' ? 'buy' :
            result.action === 'SELL' || result.action === 'TAKE_PROFIT' || result.action === 'CUT_LOSS' ? 'sell' :
                result.action === 'HOLD' || result.action === 'WAIT_TO_BUY' ? 'hold' : 'neutral';

        const actionDisplay = result.action.replace(/_/g, ' ');
        const pnlClass = result.position && result.position.pnl >= 0 ? 'positive' : 'negative';
        const pnlSign = result.position && result.position.pnl >= 0 ? '+' : '';

        const actionEmoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '✋',
            'AVERAGE_DOWN': '📉',
            'AVERAGE_UP': '🚀',
            'TAKE_PROFIT': '💰',
            'CUT_LOSS': '✂️',
            'WAIT_TO_BUY': '⏳'
        };

        resultEl.innerHTML = `
            <div class="position-result-card action-${action}">
                <div class="position-action">
                    <span class="action-badge ${action}">
                        ${actionEmoji[result.action] || '📊'} ${actionDisplay}
                    </span>
                    <span class="position-confidence">
                        ${(result.confidence * 100).toFixed(0)}% confidence
                    </span>
                </div>

                <div class="position-pnl">
                    <span class="pnl-label">P/L</span>
                    <span class="pnl-value ${pnlClass}">
                        ${pnlSign}${this.formatPrice(result.position.pnl)} (${pnlSign}${result.position.pnlPercent.toFixed(2)}%)
                    </span>
                </div>

                <div class="position-targets">
                    <div class="target-item">
                        <span class="label">Current</span>
                        <span class="value">${this.formatPrice(result.position.currentPrice)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Target</span>
                        <span class="value">${result.targets.targetRange ? result.targets.targetRange : this.formatPrice(result.targets.targetPrice)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Stop Loss</span>
                        <span class="value">${this.formatPrice(result.targets.stopLoss)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Support</span>
                        <span class="value">${this.formatPrice(result.targets.support1)}</span>
                    </div>
                    <div class="target-item">
                        <span class="label">Resist</span>
                        <span class="value">${this.formatPrice(result.targets.resistance1)}</span>
                    </div>
                </div>

                ${result.averaging && result.averaging.potentialLots > 0 ? `
                <div class="position-targets" style="margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                    <div class="target-item">
                        <span class="label">Can Buy</span>
                        <span class="value">${result.averaging.potentialLots} lots</span>
                    </div>
                    <div class="target-item">
                        <span class="label">New Avg</span>
                        <span class="value">${this.formatPrice(result.averaging.newAvgPrice)}</span>
                    </div>
                </div>
                ` : ''}

                <div class="position-reasons">
                    <div class="position-reasons-title">Analysis</div>
                    ${result.reasons.map(r => `
                        <div class="position-reason-item">${r}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Update Fear & Greed gauge based on forecast signal and confidence
     * @param {string} signal - 'bullish', 'bearish', or 'neutral'
     * @param {number} confidence - 0 to 1
     */
    updateFearGreedGauge(signal, confidence) {
        const needle = document.getElementById('gaugeNeedle');
        const scoreEl = document.getElementById('gaugeScore');
        const statusEl = document.getElementById('gaugeStatus');

        if (!needle || !scoreEl || !statusEl) return;

        // Calculate score: 0 = Extreme Fear, 50 = Neutral, 100 = Extreme Greed
        // Bearish with high confidence = low score (fear)
        // Bullish with high confidence = high score (greed)
        let score;
        if (signal === 'bullish') {
            // Bullish: 50-100 range based on confidence
            score = 50 + (confidence * 50);
        } else if (signal === 'bearish') {
            // Bearish: 0-50 range based on confidence
            score = 50 - (confidence * 50);
        } else {
            // Neutral
            score = 50;
        }

        // Clamp score between 0 and 100
        score = Math.max(0, Math.min(100, score));

        // Determine status and class based on score
        let status, statusClass;
        if (score <= 20) {
            status = 'Extreme Fear';
            statusClass = 'extreme-fear';
        } else if (score <= 40) {
            status = 'Fear';
            statusClass = 'fear';
        } else if (score <= 60) {
            status = 'Neutral';
            statusClass = 'neutral';
        } else if (score <= 80) {
            status = 'Greed';
            statusClass = 'greed';
        } else {
            status = 'Extreme Greed';
            statusClass = 'extreme-greed';
        }

        // Calculate needle rotation (-90deg = 0, 0deg = 50, +90deg = 100)
        // Needle rotates from -90deg (left/fear) to +90deg (right/greed)
        const rotation = -90 + (score * 1.8); // 180deg range / 100 = 1.8

        // Animate after a short delay to ensure DOM is ready
        setTimeout(() => {
            needle.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
            scoreEl.textContent = Math.round(score);
            scoreEl.className = `gauge-score ${statusClass}`;
            statusEl.textContent = status;
            statusEl.className = `gauge-status ${statusClass}`;
        }, 100);
    }

    /**
     * Add a stock to watchlist
     */
    async addToWatchlist(symbol) {
        // Normalize symbol
        if (!symbol.endsWith('.JK')) {
            symbol = symbol.toUpperCase() + '.JK';
        }

        // Check if already in watchlist
        if (this.defaultWatchlist.includes(symbol)) {
            console.log(`${symbol} already in watchlist`);
            return;
        }

        try {
            // Save to backend first
            await window.api.addToWatchlist(symbol);

            // Add to local watchlist
            this.defaultWatchlist.push(symbol);
            console.log(`Added ${symbol} to watchlist (saved to backend)`);

            // Reload watchlist to show the new stock
            await this.loadSection('stockWatchlist', this.defaultWatchlist);

            // Select the newly added stock
            await this.selectStock(symbol);
        } catch (error) {
            console.error('Failed to add to watchlist:', error);
        }
    }

    /**
     * Remove a stock from watchlist
     */
    async removeFromWatchlist(symbol) {
        const index = this.defaultWatchlist.indexOf(symbol);
        if (index === -1) {
            console.log(`${symbol} not in watchlist`);
            return;
        }

        try {
            // Remove from backend first
            await window.api.removeFromWatchlist(symbol);

            // Remove from local watchlist
            this.defaultWatchlist.splice(index, 1);
            console.log(`Removed ${symbol} from watchlist (saved to backend)`);

            // Reload watchlist
            await this.loadSection('stockWatchlist', this.defaultWatchlist);

            // If the removed stock was the current one, select the first stock
            if (this.currentSymbol === symbol && this.defaultWatchlist.length > 0) {
                await this.selectStock(this.defaultWatchlist[0]);
            }
        } catch (error) {
            console.error('Failed to remove from watchlist:', error);
        }
    }

    // ==================== Portfolio Management ====================

    /**
     * Load portfolio positions from backend
     */
    async loadPortfolio() {
        const container = document.getElementById('portfolioPositions');
        if (!container) return;

        container.innerHTML = '<div class="portfolio-loading">Loading portfolio...</div>';

        try {
            const data = await window.api.getPortfolio();
            this.renderPortfolio(data.positions || []);

            // Set up auto-refresh every 30 seconds
            if (this.portfolioRefreshInterval) {
                clearInterval(this.portfolioRefreshInterval);
            }
            this.portfolioRefreshInterval = setInterval(() => {
                this.loadPortfolio();
            }, 30000);
        } catch (error) {
            console.error('Error loading portfolio:', error);
            container.innerHTML = '<div class="portfolio-empty">Failed to load portfolio</div>';
        }
    }

    /**
     * Render portfolio positions
     */
    renderPortfolio(positions) {
        const container = document.getElementById('portfolioPositions');
        const summaryEl = document.getElementById('portfolioSummary');

        if (!positions || positions.length === 0) {
            container.innerHTML = '<div class="portfolio-empty">No positions yet. Click ➕ to add.</div>';
            if (summaryEl) summaryEl.style.display = 'none';
            return;
        }

        let totalPnL = 0;
        let html = '';

        for (const item of positions) {
            const { symbol, position, analysis } = item;
            const hasError = analysis && analysis.error;

            if (!hasError && analysis && analysis.position) {
                totalPnL += analysis.position.pnl || 0;

                const pnl = analysis.position.pnl || 0;
                const pnlPercent = analysis.position.pnlPercent || 0;
                const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                const pnlSign = pnl >= 0 ? '+' : '';

                const action = (analysis.action || 'HOLD').toLowerCase().replace('_', '-');
                const actionDisplay = (analysis.action || 'HOLD').replace(/_/g, ' ');

                const actionEmoji = {
                    'hold': '✋',
                    'cut-loss': '✂️',
                    'take-profit': '💰',
                    'average-down': '📉',
                    'average-up': '🚀',
                    'wait-to-buy': '⏳'
                };

                html += `
                    <div class="portfolio-position-item" data-symbol="${symbol}">
                        <div class="position-header">
                            <div class="position-symbol">
                                <span class="symbol">${symbol.replace('.JK', '')}</span>
                                <span class="position-details">@ ${this.formatPrice(position.avgPrice)} × ${position.quantity} lot</span>
                            </div>
                            <span class="action-badge ${action}">${actionEmoji[action] || '📊'} ${actionDisplay}</span>
                        </div>
                        <div class="position-metrics">
                            <div class="metric">
                                <span class="label">P/L</span>
                                <span class="value ${pnlClass}">${pnlSign}${this.formatPrice(pnl)} (${pnlSign}${pnlPercent.toFixed(2)}%)</span>
                            </div>
                            <div class="metric">
                                <span class="label">Current</span>
                                <span class="value">${this.formatPrice(analysis.position.currentPrice)}</span>
                            </div>
                            <div class="metric">
                                <span class="label">Target</span>
                                <span class="value">${analysis.targets?.targetRange || this.formatPrice(analysis.targets?.targetPrice || 0)}</span>
                            </div>
                            <div class="metric">
                                <span class="label">SL</span>
                                <span class="value">${this.formatPrice(analysis.targets?.stopLoss || 0)}</span>
                            </div>
                        </div>
                        <div class="position-actions">
                            <button class="btn-small btn-sell" onclick="window.app.removePortfolioPosition('${symbol}')">Sell</button>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div class="portfolio-position-item error" data-symbol="${symbol}">
                        <div class="position-header">
                            <span class="symbol">${symbol.replace('.JK', '')}</span>
                            <span class="position-error-msg">${hasError ? analysis.error : 'Loading...'}</span>
                        </div>
                        <div class="position-actions">
                            <button class="btn-small btn-sell" onclick="window.app.removePortfolioPosition('${symbol}')">Remove</button>
                        </div>
                    </div>
                `;
            }
        }

        container.innerHTML = html;

        // Update summary
        if (summaryEl) {
            const totalPnLEl = document.getElementById('totalPnL');
            const pnlClass = totalPnL >= 0 ? 'positive' : 'negative';
            const pnlSign = totalPnL >= 0 ? '+' : '';
            totalPnLEl.innerHTML = `<span class="${pnlClass}">${pnlSign}${this.formatPrice(totalPnL)}</span>`;
            summaryEl.style.display = 'block';
        }
    }

    /**
     * Show add position form
     */
    showAddPositionForm() {
        const form = document.getElementById('addPositionForm');
        if (form) {
            form.style.display = 'block';
            // Pre-fill with current stock if selected
            const symbolInput = document.getElementById('newPositionSymbol');
            if (symbolInput && this.currentSymbol) {
                symbolInput.value = this.currentSymbol.replace('.JK', '');
            }
        }
    }

    /**
     * Hide add position form
     */
    hideAddPositionForm() {
        const form = document.getElementById('addPositionForm');
        if (form) {
            form.style.display = 'none';
            // Clear inputs
            document.getElementById('newPositionSymbol').value = '';
            document.getElementById('newPositionAvgPrice').value = '';
            document.getElementById('newPositionQuantity').value = '';
        }
    }

    /**
     * Add a new position to portfolio
     */
    async addPortfolioPosition() {
        const symbol = document.getElementById('newPositionSymbol').value.trim();
        const avgPrice = parseFloat(document.getElementById('newPositionAvgPrice').value);
        const quantity = parseInt(document.getElementById('newPositionQuantity').value);

        if (!symbol) {
            alert('Please enter a stock symbol');
            return;
        }
        if (!avgPrice || avgPrice <= 0) {
            alert('Please enter a valid average price');
            return;
        }
        if (!quantity || quantity <= 0) {
            alert('Please enter a valid quantity');
            return;
        }

        try {
            await window.api.addPortfolioPosition(symbol, avgPrice, quantity);
            this.hideAddPositionForm();
            await this.loadPortfolio();
        } catch (error) {
            console.error('Error adding position:', error);
            alert('Failed to add position: ' + (error.message || 'Unknown error'));
        }
    }

    /**
     * Remove a position from portfolio (sell)
     */
    async removePortfolioPosition(symbol) {
        if (!confirm(`Are you sure you want to remove ${symbol} from your portfolio?`)) {
            return;
        }

        try {
            await window.api.removePortfolioPosition(symbol);
            await this.loadPortfolio();
        } catch (error) {
            console.error('Error removing position:', error);
            alert('Failed to remove position: ' + (error.message || 'Unknown error'));
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TradingApp();
    window.app.init();
});

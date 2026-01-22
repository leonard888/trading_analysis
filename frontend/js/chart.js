/**
 * Chart Module - TradingView Lightweight Charts wrapper
 */

class TradingChart {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.smaLine = null;
        this.currentSymbol = null;
    }

    /**
     * Initialize the chart
     */
    init() {
        // Clear existing chart
        if (this.chart) {
            this.chart.remove();
        }

        // Create chart with dark theme
        this.chart = LightweightCharts.createChart(this.container, {
            width: this.container.clientWidth,
            height: this.container.clientHeight || 400,
            layout: {
                background: { type: 'solid', color: '#161b22' },
                textColor: '#8b949e',
            },
            grid: {
                vertLines: { color: '#21262d' },
                horzLines: { color: '#21262d' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    width: 1,
                    color: '#58a6ff',
                    style: LightweightCharts.LineStyle.Dashed,
                },
                horzLine: {
                    width: 1,
                    color: '#58a6ff',
                    style: LightweightCharts.LineStyle.Dashed,
                },
            },
            rightPriceScale: {
                borderColor: '#30363d',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.2,
                },
            },
            timeScale: {
                borderColor: '#30363d',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // Create candlestick series
        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#3fb950',
            downColor: '#f85149',
            borderUpColor: '#3fb950',
            borderDownColor: '#f85149',
            wickUpColor: '#3fb950',
            wickDownColor: '#f85149',
        });

        // Create volume series
        this.volumeSeries = this.chart.addHistogramSeries({
            color: '#58a6ff',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
                top: 0.85,
                bottom: 0,
            },
        });

        // Handle resize
        window.addEventListener('resize', () => this.handleResize());

        return this;
    }

    /**
     * Handle container resize
     */
    handleResize() {
        if (this.chart) {
            this.chart.applyOptions({
                width: this.container.clientWidth,
                height: this.container.clientHeight || 400,
            });
        }
    }

    /**
     * Update chart with new data
     */
    updateData(data) {
        if (!data || !data.history || data.history.length === 0) {
            console.warn('No data to display');
            return;
        }

        this.currentSymbol = data.symbol;

        // Format candlestick data
        const candleData = data.history.map(item => ({
            time: item.time,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
        }));

        // Format volume data
        const volumeData = data.history.map(item => ({
            time: item.time,
            value: item.volume,
            color: item.close >= item.open
                ? 'rgba(63, 185, 80, 0.5)'
                : 'rgba(248, 81, 73, 0.5)',
        }));

        // Update series
        this.candleSeries.setData(candleData);
        this.volumeSeries.setData(volumeData);

        // Fit content
        this.chart.timeScale().fitContent();
    }

    /**
     * Add SMA line overlay
     */
    addSMALine(prices, period = 20, color = '#58a6ff') {
        if (this.smaLine) {
            this.chart.removeSeries(this.smaLine);
        }

        const smaData = this.calculateSMA(prices, period);

        this.smaLine = this.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        });

        this.smaLine.setData(smaData);
    }

    /**
     * Calculate SMA
     */
    calculateSMA(data, period) {
        const result = [];

        for (let i = period - 1; i < data.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j].close;
            }
            result.push({
                time: data[i].time,
                value: sum / period,
            });
        }

        return result;
    }

    /**
     * Add markers for patterns
     */
    addPatternMarkers(patterns) {
        if (!patterns || patterns.length === 0) return;

        const markers = patterns.map(pattern => ({
            time: pattern.time || Date.now() / 1000,
            position: pattern.type === 'bullish' ? 'belowBar' : 'aboveBar',
            color: pattern.type === 'bullish' ? '#3fb950' : '#f85149',
            shape: pattern.type === 'bullish' ? 'arrowUp' : 'arrowDown',
            text: pattern.pattern,
        }));

        this.candleSeries.setMarkers(markers);
    }

    /**
     * Clear chart
     */
    clear() {
        if (this.candleSeries) {
            this.candleSeries.setData([]);
        }
        if (this.volumeSeries) {
            this.volumeSeries.setData([]);
        }
        if (this.smaLine) {
            this.chart.removeSeries(this.smaLine);
            this.smaLine = null;
        }
    }

    /**
     * Destroy chart
     */
    destroy() {
        if (this.chart) {
            this.chart.remove();
            this.chart = null;
        }
    }
}

// Export
window.TradingChart = TradingChart;

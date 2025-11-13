/**
 * Aegis Dashboard - Modular JavaScript
 *
 * This file is structured for easy migration to React/Hugo in the future.
 * Each section is self-contained and can be converted to a component.
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    GITHUB_CSV_URL: 'https://raw.githubusercontent.com/ducroq/Aegis/master/data/history/risk_scores.csv',
    RISK_THRESHOLDS: {
        RED: 5.0,      // Updated from 8.0 (calibrated threshold based on 2000-2024 backtest)
        YELLOW: 4.0    // Updated from 6.5 (calibrated threshold based on 2000-2024 backtest)
    },
    CHART_COLORS: {
        PRIMARY: '#667eea',
        GREEN: '#10b981',
        YELLOW: '#f59e0b',
        RED: '#ef4444'
    }
};

// ============================================================================
// DATA LOADING MODULE
// ============================================================================

const DataLoader = {
    /**
     * Fetch and parse CSV data from GitHub
     * @returns {Promise<Array>} Parsed CSV data
     */
    async loadData() {
        try {
            const response = await fetch(CONFIG.GITHUB_CSV_URL);

            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
            }

            const csvText = await response.text();

            // Parse CSV using PapaParse
            const parsed = Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true
            });

            if (parsed.errors.length > 0) {
                console.error('CSV parsing errors:', parsed.errors);
            }

            const data = parsed.data;

            if (data.length === 0) {
                throw new Error('No data found in CSV file');
            }

            console.log('✓ Data loaded successfully:', data.length, 'data points');
            return data;

        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }
};

// ============================================================================
// RISK CALCULATION MODULE
// ============================================================================

const RiskCalculator = {
    /**
     * Get risk tier and color based on score
     * @param {number} score - Risk score (0-10)
     * @returns {Object} {tier, color}
     */
    getRiskTier(score) {
        if (score >= CONFIG.RISK_THRESHOLDS.RED) {
            return { tier: 'RED', color: CONFIG.CHART_COLORS.RED };
        }
        if (score >= CONFIG.RISK_THRESHOLDS.YELLOW) {
            return { tier: 'YELLOW', color: CONFIG.CHART_COLORS.YELLOW };
        }
        return { tier: 'GREEN', color: CONFIG.CHART_COLORS.GREEN };
    }
};

// ============================================================================
// UI UPDATE MODULE
// ============================================================================

const UIUpdater = {
    /**
     * Update status bar with latest data
     * @param {Array} data - Full dataset
     */
    updateStatusBar(data) {
        const latest = data[data.length - 1];
        const riskScore = latest.overall_risk;
        const { tier, color } = RiskCalculator.getRiskTier(riskScore);

        document.getElementById('currentRisk').textContent = riskScore.toFixed(2);
        document.getElementById('currentRisk').style.color = color;

        document.getElementById('riskTier').textContent = tier;
        document.getElementById('riskTier').style.color = color;

        document.getElementById('lastUpdated').textContent = latest.date;
        document.getElementById('footerUpdate').textContent = `Data as of ${latest.date}`;
    },

    /**
     * Show/hide loading/error states
     */
    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        document.getElementById('charts').style.display = 'none';
    },

    showError(message) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = `Error: ${message}`;
        document.getElementById('charts').style.display = 'none';
    },

    showCharts() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('charts').style.display = 'block';
    }
};

// ============================================================================
// CHART RENDERING MODULE
// ============================================================================

const ChartRenderer = {
    /**
     * Create risk timeline chart
     * @param {Array} data - Full dataset
     */
    createRiskTimeline(data) {
        const dates = data.map(d => d.date);
        const scores = data.map(d => d.overall_risk);

        // Color markers by risk tier
        const colors = scores.map(score => {
            const { color } = RiskCalculator.getRiskTier(score);
            return color;
        });

        const trace = {
            x: dates,
            y: scores,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Risk Score',
            line: { color: CONFIG.CHART_COLORS.PRIMARY, width: 3 },
            marker: { size: 6, color: colors },
            hovertemplate: '<b>%{x}</b><br>Risk: %{y:.2f}/10<extra></extra>'
        };

        // Threshold lines
        const yellowLine = {
            x: dates,
            y: Array(dates.length).fill(CONFIG.RISK_THRESHOLDS.YELLOW),
            type: 'scatter',
            mode: 'lines',
            name: 'Yellow Threshold',
            line: { color: CONFIG.CHART_COLORS.YELLOW, width: 1, dash: 'dash' },
            hoverinfo: 'skip'
        };

        const redLine = {
            x: dates,
            y: Array(dates.length).fill(CONFIG.RISK_THRESHOLDS.RED),
            type: 'scatter',
            mode: 'lines',
            name: 'Red Threshold',
            line: { color: CONFIG.CHART_COLORS.RED, width: 1, dash: 'dash' },
            hoverinfo: 'skip'
        };

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score (0-10)', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: -0.2 },
            hovermode: 'x unified'
        };

        Plotly.newPlot('riskTimeline', [trace, yellowLine, redLine], layout, {responsive: true});
    },

    /**
     * Create dimension radar chart
     * @param {Array} data - Full dataset
     */
    createDimensionRadar(data) {
        const latest = data[data.length - 1];

        const dimensions = ['Recession', 'Credit', 'Valuation', 'Liquidity', 'Positioning'];
        const values = [
            latest.recession || 0,
            latest.credit || 0,
            latest.valuation || 0,
            latest.liquidity || 0,
            latest.positioning || 0
        ];

        const trace = {
            type: 'scatterpolar',
            r: values,
            theta: dimensions,
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            line: { color: CONFIG.CHART_COLORS.PRIMARY, width: 2 },
            marker: { size: 8, color: CONFIG.CHART_COLORS.PRIMARY },
            hovertemplate: '<b>%{theta}</b><br>Score: %{r:.2f}/10<extra></extra>'
        };

        const layout = {
            height: 400,
            margin: { t: 40, r: 80, b: 40, l: 80 },
            polar: {
                radialaxis: {
                    visible: true,
                    range: [0, 10],
                    tickvals: [0, 2, 4, 6, 8, 10]
                }
            },
            showlegend: false
        };

        Plotly.newPlot('dimensionRadar', [trace], layout, {responsive: true});
    },

    /**
     * Create dimension bar chart
     * @param {Array} data - Full dataset
     */
    createDimensionBars(data) {
        const latest = data[data.length - 1];

        const dimensions = ['Recession', 'Credit', 'Valuation', 'Liquidity', 'Positioning'];
        const values = [
            latest.recession || 0,
            latest.credit || 0,
            latest.valuation || 0,
            latest.liquidity || 0,
            latest.positioning || 0
        ];

        const colors = values.map(v => {
            const { color } = RiskCalculator.getRiskTier(v);
            return color;
        });

        const trace = {
            x: dimensions,
            y: values,
            type: 'bar',
            marker: { color: colors, line: { color: '#333', width: 1 } },
            hovertemplate: '<b>%{x}</b><br>Score: %{y:.2f}/10<extra></extra>'
        };

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 80, l: 60 },
            xaxis: { title: 'Dimension', tickangle: -45 },
            yaxis: { title: 'Risk Score (0-10)', range: [0, 10] },
            showlegend: false
        };

        Plotly.newPlot('dimensionBars', [trace], layout, {responsive: true});
    },

    /**
     * Create historical dimensions timeline
     * @param {Array} data - Full dataset
     */
    createDimensionTimeline(data) {
        const dates = data.map(d => d.date);

        const traces = [
            {
                name: 'Recession',
                x: dates,
                y: data.map(d => d.recession || null),
                type: 'scatter',
                mode: 'lines',
                line: { width: 2 }
            },
            {
                name: 'Credit',
                x: dates,
                y: data.map(d => d.credit || null),
                type: 'scatter',
                mode: 'lines',
                line: { width: 2 }
            },
            {
                name: 'Valuation',
                x: dates,
                y: data.map(d => d.valuation || null),
                type: 'scatter',
                mode: 'lines',
                line: { width: 2 }
            },
            {
                name: 'Liquidity',
                x: dates,
                y: data.map(d => d.liquidity || null),
                type: 'scatter',
                mode: 'lines',
                line: { width: 2 }
            },
            {
                name: 'Positioning',
                x: dates,
                y: data.map(d => d.positioning || null),
                type: 'scatter',
                mode: 'lines',
                line: { width: 2 }
            }
        ];

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score (0-10)', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: -0.2 },
            hovermode: 'x unified'
        };

        Plotly.newPlot('dimensionTimeline', traces, layout, {responsive: true});
    }
};

// ============================================================================
// MAIN APPLICATION
// ============================================================================

const DashboardApp = {
    /**
     * Initialize and render dashboard
     */
    async init() {
        try {
            UIUpdater.showLoading();

            // Load data
            const data = await DataLoader.loadData();

            // Update UI
            UIUpdater.showCharts();
            UIUpdater.updateStatusBar(data);

            // Render all charts
            ChartRenderer.createRiskTimeline(data);
            ChartRenderer.createDimensionRadar(data);
            ChartRenderer.createDimensionBars(data);
            ChartRenderer.createDimensionTimeline(data);

            console.log('✓ Dashboard initialized successfully');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            UIUpdater.showError(error.message + '. Check console for details.');
        }
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

// Start dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    DashboardApp.init();
});

// Export for potential future module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DashboardApp, DataLoader, ChartRenderer, RiskCalculator };
}

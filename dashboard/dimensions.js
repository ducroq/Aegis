/**
 * Aegis Dashboard - Dimensions Page
 * Detailed breakdown of each risk component
 */

// Configuration with updated calibrated thresholds
const CONFIG = {
    GITHUB_CSV_URL: '/data/historical_risk_scores.csv',
    RISK_THRESHOLDS: {
        RED: 5.0,
        YELLOW: 4.0
    },
    CHART_COLORS: {
        PRIMARY: '#667eea',
        GREEN: '#10b981',
        YELLOW: '#f59e0b',
        RED: '#ef4444',
        DIMENSIONS: {
            recession: '#ef4444',
            credit: '#f59e0b',
            valuation: '#8b5cf6',
            liquidity: '#3b82f6',
            positioning: '#10b981'
        }
    },
    WEIGHTS: {
        recession: 0.30,
        credit: 0.25,
        valuation: 0.20,
        liquidity: 0.15,
        positioning: 0.10
    },
    DIMENSION_INFO: {
        recession: {
            name: 'Recession Risk',
            emoji: '📉',
            weight: '30%',
            description: 'Monitors unemployment claims velocity, ISM PMI regime crosses, and dual yield curve inversions.',
            indicators: ['Unemployment Claims YoY', 'ISM PMI', '10Y-2Y Yield Spread']
        },
        credit: {
            name: 'Credit Stress',
            emoji: '💳',
            weight: '25%',
            description: 'Tracks high-yield spread velocity (70%) and level (30%), investment-grade spreads, and bank lending standards.',
            indicators: ['HY Spread Velocity', 'HY Spread Level', 'BBB Spreads', 'TED Spread']
        },
        valuation: {
            name: 'Valuation Extremes',
            emoji: '📊',
            weight: '20%',
            description: 'Monitors CAPE ratio, Buffett indicator (Market Cap/GDP), and forward P/E ratios.',
            indicators: ['CAPE Ratio', 'Buffett Indicator', 'Forward P/E']
        },
        liquidity: {
            name: 'Liquidity Conditions',
            emoji: '💧',
            weight: '15%',
            description: 'Tracks Fed funds rate changes, M2 velocity, VIX levels, and dollar liquidity conditions.',
            indicators: ['Fed Funds Rate', 'M2 Velocity', 'VIX', 'Dollar Liquidity']
        },
        positioning: {
            name: 'Positioning & Speculation',
            emoji: '🎯',
            weight: '10%',
            description: 'Monitors CFTC positioning (S&P 500, Treasury, VIX futures) for contrarian signals and complacency.',
            indicators: ['CFTC S&P Net Position', 'CFTC Treasury Position', 'VIX Futures']
        }
    }
};

// Global state
let fullData = [];
let currentDimension = 'all';

// Data loading
const DataLoader = {
    async loadData() {
        try {
            const response = await fetch(CONFIG.GITHUB_CSV_URL);
            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.status}`);
            }
            const csvText = await response.text();
            const parsed = Papa.parse(csvText, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true
            });
            if (parsed.data.length === 0) {
                throw new Error('No data found');
            }
            console.log('✓ Dimension data loaded:', parsed.data.length, 'points');
            return parsed.data;
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }
};

// Risk calculations
const RiskCalculator = {
    getRiskTier(score) {
        if (score >= CONFIG.RISK_THRESHOLDS.RED) {
            return { tier: 'RED', color: CONFIG.CHART_COLORS.RED };
        }
        if (score >= CONFIG.RISK_THRESHOLDS.YELLOW) {
            return { tier: 'YELLOW', color: CONFIG.CHART_COLORS.YELLOW };
        }
        return { tier: 'GREEN', color: CONFIG.CHART_COLORS.GREEN };
    },

    getLatestScores(data) {
        const latest = data[data.length - 1];
        return {
            recession: latest.recession || 0,
            credit: latest.credit || 0,
            valuation: latest.valuation || 0,
            liquidity: latest.liquidity || 0,
            positioning: latest.positioning || 0
        };
    }
};

// UI updates
const UIUpdater = {
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
    },

    updateDimensionScores(data) {
        const scores = RiskCalculator.getLatestScores(data);

        for (const [dim, score] of Object.entries(scores)) {
            const element = document.getElementById(`${dim}Score`);
            if (element) {
                element.textContent = score.toFixed(2);
                const { color } = RiskCalculator.getRiskTier(score);
                element.style.color = color;
            }
        }
    }
};

// Chart rendering
const ChartRenderer = {
    createDimensionBars(data) {
        const scores = RiskCalculator.getLatestScores(data);
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];

        const trace = {
            x: dimensions.map(d => CONFIG.DIMENSION_INFO[d].name),
            y: dimensions.map(d => scores[d]),
            type: 'bar',
            marker: {
                color: dimensions.map(d => CONFIG.CHART_COLORS.DIMENSIONS[d])
            },
            text: dimensions.map(d => scores[d].toFixed(2)),
            textposition: 'auto',
            hovertemplate: '<b>%{x}</b><br>Score: %{y:.2f}/10<extra></extra>'
        };

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 100, l: 60 },
            xaxis: { title: '', tickangle: -45 },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            showlegend: false
        };

        Plotly.newPlot('dimensionBars', [trace], layout, { responsive: true });
    },

    createWeightsPie(data) {
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];

        const trace = {
            labels: dimensions.map(d => CONFIG.DIMENSION_INFO[d].name),
            values: dimensions.map(d => CONFIG.WEIGHTS[d] * 100),
            type: 'pie',
            marker: {
                colors: dimensions.map(d => CONFIG.CHART_COLORS.DIMENSIONS[d])
            },
            textinfo: 'label+percent',
            hovertemplate: '<b>%{label}</b><br>Weight: %{value}%<extra></extra>'
        };

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 20, l: 20 },
            showlegend: false
        };

        Plotly.newPlot('weightsPie', [trace], layout, { responsive: true });
    },

    createDimensionComparison(data) {
        // Show last 60 data points (approximately 5 years of monthly data)
        const recentData = data.slice(-60);
        const dates = recentData.map(d => d.date);
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];

        const traces = dimensions.map(dim => ({
            x: dates,
            y: recentData.map(d => d[dim] || 0),
            type: 'scatter',
            mode: 'lines',
            name: CONFIG.DIMENSION_INFO[dim].name,
            line: {
                width: 2,
                color: CONFIG.CHART_COLORS.DIMENSIONS[dim]
            },
            hovertemplate: `<b>${CONFIG.DIMENSION_INFO[dim].name}</b><br>%{x}<br>Score: %{y:.2f}/10<extra></extra>`
        }));

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            hovermode: 'x unified',
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot('dimensionComparison', traces, layout, { responsive: true });
    },

    createDimensionTimeline(dimension, data) {
        const dates = data.map(d => d.date);
        const scores = data.map(d => d[dimension] || 0);

        const trace = {
            x: dates,
            y: scores,
            type: 'scatter',
            mode: 'lines',
            line: {
                width: 3,
                color: CONFIG.CHART_COLORS.DIMENSIONS[dimension]
            },
            fill: 'tozeroy',
            fillcolor: `${CONFIG.CHART_COLORS.DIMENSIONS[dimension]}33`,
            hovertemplate: '<b>%{x}</b><br>Score: %{y:.2f}/10<extra></extra>'
        };

        // Add threshold lines
        const yellowLine = {
            x: [dates[0], dates[dates.length - 1]],
            y: [CONFIG.RISK_THRESHOLDS.YELLOW, CONFIG.RISK_THRESHOLDS.YELLOW],
            type: 'scatter',
            mode: 'lines',
            line: { color: CONFIG.CHART_COLORS.YELLOW, width: 2, dash: 'dash' },
            name: 'YELLOW Threshold',
            hoverinfo: 'skip'
        };

        const redLine = {
            x: [dates[0], dates[dates.length - 1]],
            y: [CONFIG.RISK_THRESHOLDS.RED, CONFIG.RISK_THRESHOLDS.RED],
            type: 'scatter',
            mode: 'lines',
            line: { color: CONFIG.CHART_COLORS.RED, width: 2, dash: 'dash' },
            name: 'RED Threshold',
            hoverinfo: 'skip'
        };

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            showlegend: true,
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot(`${dimension}Chart`, [trace, yellowLine, redLine], layout, { responsive: true });
    },

    displayIndicators(dimension) {
        const info = CONFIG.DIMENSION_INFO[dimension];
        const elementId = `${dimension}Indicators`;
        const element = document.getElementById(elementId);

        if (!element) return;

        const html = `
            <div style="padding: 15px;">
                <h3 style="margin-bottom: 15px; color: ${CONFIG.CHART_COLORS.DIMENSIONS[dimension]};">
                    Key Indicators
                </h3>
                <ul style="list-style: none; padding: 0;">
                    ${info.indicators.map(indicator => `
                        <li style="padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
                            <span style="font-weight: 500;">${indicator}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;

        element.innerHTML = html;
    },

    displaySignals(dimension, data) {
        const latest = data[data.length - 1];
        const score = latest[dimension] || 0;
        const elementId = `${dimension}Signals`;
        const element = document.getElementById(elementId);

        if (!element) return;

        const signals = [];

        // Generate signals based on score thresholds
        if (score >= CONFIG.RISK_THRESHOLDS.RED) {
            signals.push({
                level: 'CRITICAL',
                text: `${CONFIG.DIMENSION_INFO[dimension].name} at RED level (${score.toFixed(1)}/10) - severe risk detected`
            });
        } else if (score >= CONFIG.RISK_THRESHOLDS.YELLOW) {
            signals.push({
                level: 'WARNING',
                text: `${CONFIG.DIMENSION_INFO[dimension].name} at YELLOW level (${score.toFixed(1)}/10) - elevated risk`
            });
        }

        // Check trend (compare to 4 weeks ago if available)
        if (data.length >= 4) {
            const fourWeeksAgo = data[data.length - 4][dimension] || 0;
            const change = score - fourWeeksAgo;

            if (change > 1.0) {
                signals.push({
                    level: 'WARNING',
                    text: `Rising rapidly: +${change.toFixed(1)} points in 4 weeks`
                });
            } else if (change < -1.0) {
                signals.push({
                    level: 'INFO',
                    text: `Improving: ${change.toFixed(1)} points in 4 weeks`
                });
            }
        }

        if (signals.length === 0) {
            element.innerHTML = '<p style="padding: 20px; text-align: center; color: #10b981;">✓ No active warnings - conditions are normal</p>';
        } else {
            const html = signals.map(s => {
                const colorClass = s.level === 'CRITICAL' ? 'critical' : s.level === 'WARNING' ? 'warning' : 'info';
                return `<div class="signal-item ${colorClass}">${s.level}: ${s.text}</div>`;
            }).join('');
            element.innerHTML = html;
        }
    }
};

// Tab switching
const TabManager = {
    init() {
        const tabs = document.querySelectorAll('.dim-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Update active state
                tabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');

                // Switch views
                const dimension = e.target.dataset.dimension;
                this.showDimension(dimension);
            });
        });
    },

    showDimension(dimension) {
        currentDimension = dimension;

        // Hide all views
        const views = document.querySelectorAll('.dimension-view');
        views.forEach(view => view.style.display = 'none');

        if (dimension === 'all') {
            // Show all dimensions view
            document.getElementById('allDimensions').style.display = 'block';
        } else {
            // Show specific dimension view
            document.getElementById(`${dimension}View`).style.display = 'block';

            // Render charts for this dimension if not already done
            if (fullData.length > 0) {
                ChartRenderer.createDimensionTimeline(dimension, fullData);
                ChartRenderer.displayIndicators(dimension);
                ChartRenderer.displaySignals(dimension, fullData);
            }
        }
    }
};

// Main app
const DimensionsApp = {
    async init() {
        try {
            UIUpdater.showLoading();
            fullData = await DataLoader.loadData();

            UIUpdater.showCharts();
            UIUpdater.updateDimensionScores(fullData);

            // Initialize tab manager
            TabManager.init();

            // Render initial "All Dimensions" view
            ChartRenderer.createDimensionBars(fullData);
            ChartRenderer.createWeightsPie(fullData);
            ChartRenderer.createDimensionComparison(fullData);

            console.log('✓ Dimensions page initialized');
        } catch (error) {
            console.error('Failed to initialize:', error);
            UIUpdater.showError(error.message);
        }
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    DimensionsApp.init();
});

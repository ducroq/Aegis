/**
 * Aegis Dashboard - Overview Page
 * Shows current risk status and recent trends
 */

// Configuration with updated calibrated thresholds
const CONFIG = {
    GITHUB_CSV_URL: '/data/risk_scores.csv',
    RISK_THRESHOLDS: {
        RED: 5.0,      // Updated from 8.0
        YELLOW: 4.0    // Updated from 6.5
    },
    CHART_COLORS: {
        PRIMARY: '#667eea',
        GREEN: '#10b981',
        YELLOW: '#f59e0b',
        RED: '#ef4444'
    }
};

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
            console.log('✓ Data loaded:', parsed.data.length, 'points');
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

    getTrend(data) {
        const len = data.length;
        if (len < 2) return { arrow: '→', text: 'STABLE', change: 0 };

        const current = data[len - 1].overall_risk;
        const fourWeeksAgo = len >= 4 ? data[len - 4].overall_risk : data[0].overall_risk;
        const change = current - fourWeeksAgo;

        if (change > 0.5) return { arrow: '↑↑', text: 'RISING', change };
        if (change > 0.1) return { arrow: '↑', text: 'UP', change };
        if (change < -0.5) return { arrow: '↓↓', text: 'FALLING', change };
        if (change < -0.1) return { arrow: '↓', text: 'DOWN', change };
        return { arrow: '→', text: 'STABLE', change };
    }
};

// UI updates
const UIUpdater = {
    updateStatusBar(data) {
        const latest = data[data.length - 1];
        const riskScore = latest.overall_risk;
        const { tier, color } = RiskCalculator.getRiskTier(riskScore);
        const trend = RiskCalculator.getTrend(data);

        document.getElementById('currentRisk').textContent = riskScore.toFixed(2);
        document.getElementById('currentRisk').style.color = color;
        document.getElementById('currentRisk').className = `status-value ${tier.toLowerCase()}`;

        document.getElementById('riskTier').textContent = tier;
        document.getElementById('riskTier').style.color = color;
        document.getElementById('riskTier').className = `status-value ${tier.toLowerCase()}`;

        document.getElementById('trendIndicator').textContent = `${trend.arrow} ${trend.text}`;
        document.getElementById('trendIndicator').style.color = trend.change > 0 ? CONFIG.CHART_COLORS.RED : CONFIG.CHART_COLORS.GREEN;

        document.getElementById('lastUpdated').textContent = latest.date;

        // Show alert banner if risk is elevated
        if (riskScore >= CONFIG.RISK_THRESHOLDS.YELLOW) {
            const banner = document.getElementById('alertBanner');
            banner.style.display = 'flex';
            if (tier === 'RED') {
                banner.classList.add('red');
            }
            const message = tier === 'RED'
                ? `Risk score ${riskScore.toFixed(1)}/10 exceeds RED threshold (${CONFIG.RISK_THRESHOLDS.RED}). SEVERE risk - consider major defensive positioning.`
                : `Risk score ${riskScore.toFixed(1)}/10 exceeds YELLOW threshold (${CONFIG.RISK_THRESHOLDS.YELLOW}). Elevated risk - review portfolio, build cash.`;
            document.getElementById('alertMessage').textContent = message;
        }
    },

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

// Chart rendering
const ChartRenderer = {
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

    createRiskGauge(data) {
        const latest = data[data.length - 1];
        const riskScore = latest.overall_risk;
        const { tier, color } = RiskCalculator.getRiskTier(riskScore);

        const trace = {
            type: 'indicator',
            mode: 'gauge+number',
            value: riskScore,
            number: { suffix: ' / 10', font: { size: 40 } },
            gauge: {
                axis: { range: [0, 10], tickwidth: 2 },
                bar: { color: color, thickness: 0.75 },
                bgcolor: '#f0f0f0',
                borderwidth: 2,
                bordercolor: '#333',
                steps: [
                    { range: [0, CONFIG.RISK_THRESHOLDS.YELLOW], color: 'rgba(16, 185, 129, 0.1)' },
                    { range: [CONFIG.RISK_THRESHOLDS.YELLOW, CONFIG.RISK_THRESHOLDS.RED], color: 'rgba(245, 158, 11, 0.1)' },
                    { range: [CONFIG.RISK_THRESHOLDS.RED, 10], color: 'rgba(239, 68, 68, 0.1)' }
                ],
                threshold: {
                    line: { color: 'red', width: 4 },
                    thickness: 0.75,
                    value: CONFIG.RISK_THRESHOLDS.RED
                }
            }
        };

        const layout = {
            height: 400,
            margin: { t: 40, r: 40, b: 40, l: 40 }
        };

        Plotly.newPlot('riskGauge', [trace], layout, {responsive: true});
    },

    createRecentTrend(data) {
        // Show last 30 data points
        const recentData = data.slice(-30);
        const dates = recentData.map(d => d.date);
        const scores = recentData.map(d => d.overall_risk);

        const colors = scores.map(score => {
            const { color } = RiskCalculator.getRiskTier(score);
            return color;
        });

        const trace = {
            x: dates,
            y: scores,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: CONFIG.CHART_COLORS.PRIMARY, width: 3 },
            marker: { size: 6, color: colors },
            hovertemplate: '<b>%{x}</b><br>Risk: %{y:.2f}/10<extra></extra>'
        };

        const layout = {
            height: 300,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            showlegend: false,
            hovermode: 'x unified'
        };

        Plotly.newPlot('recentTrend', [trace], layout, {responsive: true});
    },

    displayKeySignals(data) {
        const latest = data[data.length - 1];
        const signalsDiv = document.getElementById('keySignals');

        // Collect signals from dimensions
        const signals = [];

        if (latest.recession >= 6.0) {
            signals.push({ level: 'WARNING', text: `Recession risk elevated (${latest.recession.toFixed(1)}/10)` });
        }
        if (latest.credit >= 6.0) {
            signals.push({ level: 'WARNING', text: `Credit stress elevated (${latest.credit.toFixed(1)}/10)` });
        }
        if (latest.valuation >= 6.0) {
            signals.push({ level: 'WARNING', text: `Valuations extended (${latest.valuation.toFixed(1)}/10)` });
        }
        if (latest.liquidity >= 6.0) {
            signals.push({ level: 'WARNING', text: `Liquidity tightening (${latest.liquidity.toFixed(1)}/10)` });
        }
        if (latest.positioning >= 6.0) {
            signals.push({ level: 'WARNING', text: `Positioning extreme (${latest.positioning.toFixed(1)}/10)` });
        }

        if (signals.length === 0) {
            signalsDiv.innerHTML = '<p style="padding: 20px; text-align: center; color: #10b981;">✓ No active warnings - risk conditions are normal</p>';
        } else {
            const html = signals.map(s =>
                `<div class="signal-item ${s.level.toLowerCase()}">${s.level}: ${s.text}</div>`
            ).join('');
            signalsDiv.innerHTML = html;
        }
    }
};

// Main app
const OverviewApp = {
    async init() {
        try {
            UIUpdater.showLoading();
            const data = await DataLoader.loadData();

            UIUpdater.showCharts();
            UIUpdater.updateStatusBar(data);

            ChartRenderer.createDimensionRadar(data);
            ChartRenderer.createRiskGauge(data);
            ChartRenderer.createRecentTrend(data);
            ChartRenderer.displayKeySignals(data);

            console.log('✓ Overview page initialized');
        } catch (error) {
            console.error('Failed to initialize:', error);
            UIUpdater.showError(error.message);
        }
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    OverviewApp.init();
});

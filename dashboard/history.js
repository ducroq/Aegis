/**
 * Aegis Dashboard - History Page
 * Deep dive into historical trends and backtest results
 */

// Configuration with updated calibrated thresholds
const CONFIG = {
    GITHUB_CSV_URL: 'https://raw.githubusercontent.com/ducroq/Aegis/master/data/history/risk_scores.csv',
    RISK_THRESHOLDS: {
        RED: 5.0,      // Updated from 8.0
        YELLOW: 4.0    // Updated from 6.5
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
    MAJOR_EVENTS: [
        { date: '2000-03-01', label: 'Dot-Com Peak', color: '#ef4444' },
        { date: '2001-09-01', label: '9/11', color: '#ef4444' },
        { date: '2008-09-01', label: 'Lehman Collapse', color: '#ef4444' },
        { date: '2020-03-01', label: 'COVID Crash', color: '#ef4444' },
        { date: '2022-01-01', label: 'Bear Market', color: '#f59e0b' }
    ]
};

// Global state
let fullData = [];
let currentPeriod = 'all';

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
            console.log('✓ Historical data loaded:', parsed.data.length, 'points');
            return parsed.data;
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }
};

// Time range filtering
const TimeFilter = {
    filterByPeriod(data, period) {
        if (period === 'all') return data;

        const now = new Date();
        const latestDate = new Date(data[data.length - 1].date);
        let startDate;

        switch (period) {
            case '5y':
                startDate = new Date(latestDate);
                startDate.setFullYear(startDate.getFullYear() - 5);
                break;
            case '3y':
                startDate = new Date(latestDate);
                startDate.setFullYear(startDate.getFullYear() - 3);
                break;
            case '1y':
                startDate = new Date(latestDate);
                startDate.setFullYear(startDate.getFullYear() - 1);
                break;
            case 'ytd':
                startDate = new Date(latestDate.getFullYear(), 0, 1);
                break;
            default:
                return data;
        }

        return data.filter(d => new Date(d.date) >= startDate);
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

    calculateStats(data) {
        const scores = data.map(d => d.overall_risk).filter(s => !isNaN(s));

        const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
        const sortedScores = [...scores].sort((a, b) => a - b);
        const median = sortedScores[Math.floor(sortedScores.length / 2)];
        const max = Math.max(...scores);
        const min = Math.min(...scores);

        // Standard deviation
        const variance = scores.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / scores.length;
        const stdDev = Math.sqrt(variance);

        // Percentiles
        const p95 = sortedScores[Math.floor(sortedScores.length * 0.95)];
        const p05 = sortedScores[Math.floor(sortedScores.length * 0.05)];

        // Alert counts
        const yellowAlerts = data.filter(d => d.overall_risk >= CONFIG.RISK_THRESHOLDS.YELLOW).length;
        const redAlerts = data.filter(d => d.overall_risk >= CONFIG.RISK_THRESHOLDS.RED).length;

        return {
            mean: mean.toFixed(2),
            median: median.toFixed(2),
            max: max.toFixed(2),
            min: min.toFixed(2),
            stdDev: stdDev.toFixed(2),
            p95: p95.toFixed(2),
            p05: p05.toFixed(2),
            yellowAlerts,
            redAlerts,
            totalPoints: data.length
        };
    },

    calculateCorrelations(data) {
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];
        const correlations = {};

        for (const dim1 of dimensions) {
            correlations[dim1] = {};
            for (const dim2 of dimensions) {
                if (dim1 === dim2) {
                    correlations[dim1][dim2] = 1.0;
                } else {
                    correlations[dim1][dim2] = this._pearsonCorrelation(
                        data.map(d => d[dim1] || 0),
                        data.map(d => d[dim2] || 0)
                    );
                }
            }
        }

        return correlations;
    },

    _pearsonCorrelation(x, y) {
        const n = x.length;
        const sum_x = x.reduce((a, b) => a + b, 0);
        const sum_y = y.reduce((a, b) => a + b, 0);
        const sum_xy = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sum_x2 = x.reduce((sum, xi) => sum + xi * xi, 0);
        const sum_y2 = y.reduce((sum, yi) => sum + yi * yi, 0);

        const numerator = n * sum_xy - sum_x * sum_y;
        const denominator = Math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y));

        return denominator === 0 ? 0 : numerator / denominator;
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
    }
};

// Chart rendering
const ChartRenderer = {
    createRiskTimeline(data) {
        const dates = data.map(d => d.date);
        const scores = data.map(d => d.overall_risk);

        // Color points based on tier
        const colors = scores.map(score => {
            const { color } = RiskCalculator.getRiskTier(score);
            return color;
        });

        const trace = {
            x: dates,
            y: scores,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: CONFIG.CHART_COLORS.PRIMARY, width: 2 },
            marker: { size: 4, color: colors },
            hovertemplate: '<b>%{x}</b><br>Risk: %{y:.2f}/10<extra></extra>',
            name: 'Overall Risk'
        };

        // Add threshold lines
        const yellowLine = {
            x: [dates[0], dates[dates.length - 1]],
            y: [CONFIG.RISK_THRESHOLDS.YELLOW, CONFIG.RISK_THRESHOLDS.YELLOW],
            type: 'scatter',
            mode: 'lines',
            line: { color: CONFIG.CHART_COLORS.YELLOW, width: 2, dash: 'dash' },
            name: 'YELLOW Threshold (4.0)',
            hoverinfo: 'skip'
        };

        const redLine = {
            x: [dates[0], dates[dates.length - 1]],
            y: [CONFIG.RISK_THRESHOLDS.RED, CONFIG.RISK_THRESHOLDS.RED],
            type: 'scatter',
            mode: 'lines',
            line: { color: CONFIG.CHART_COLORS.RED, width: 2, dash: 'dash' },
            name: 'RED Threshold (5.0)',
            hoverinfo: 'skip'
        };

        // Filter events to only show those within the visible date range
        const startDate = new Date(dates[0]);
        const endDate = new Date(dates[dates.length - 1]);
        const visibleEvents = CONFIG.MAJOR_EVENTS.filter(event => {
            const eventDate = new Date(event.date);
            return eventDate >= startDate && eventDate <= endDate;
        });

        // Add event markers only for visible events
        const eventShapes = visibleEvents.map(event => ({
            type: 'line',
            x0: event.date,
            x1: event.date,
            y0: 0,
            y1: 10,
            line: {
                color: event.color,
                width: 1,
                dash: 'dot'
            }
        }));

        const eventAnnotations = visibleEvents.map(event => ({
            x: event.date,
            y: 9,
            text: event.label,
            showarrow: false,
            textangle: -90,
            font: { size: 10, color: event.color }
        }));

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            hovermode: 'x unified',
            shapes: eventShapes,
            annotations: eventAnnotations,
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot('riskTimeline', [trace, yellowLine, redLine], layout, { responsive: true });
    },

    createDimensionTimeline(data) {
        const dates = data.map(d => d.date);
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];

        const traces = dimensions.map(dim => ({
            x: dates,
            y: data.map(d => d[dim] || 0),
            type: 'scatter',
            mode: 'lines',
            name: dim.charAt(0).toUpperCase() + dim.slice(1),
            line: { width: 2, color: CONFIG.CHART_COLORS.DIMENSIONS[dim] },
            hovertemplate: `<b>${dim}</b><br>%{x}<br>Score: %{y:.2f}/10<extra></extra>`
        }));

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Dimension Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            hovermode: 'x unified',
            legend: { orientation: 'h', y: -0.2 }
        };

        Plotly.newPlot('dimensionTimeline', traces, layout, { responsive: true });
    },

    createAlertHistory(data) {
        // Find all periods where risk was >= YELLOW
        const alertPeriods = data.filter(d => d.overall_risk >= CONFIG.RISK_THRESHOLDS.YELLOW);

        const dates = alertPeriods.map(d => d.date);
        const scores = alertPeriods.map(d => d.overall_risk);
        const tiers = alertPeriods.map(d => {
            const { tier } = RiskCalculator.getRiskTier(d.overall_risk);
            return tier;
        });
        const colors = alertPeriods.map(d => {
            const { color } = RiskCalculator.getRiskTier(d.overall_risk);
            return color;
        });

        const trace = {
            x: dates,
            y: scores,
            type: 'bar',
            marker: { color: colors },
            hovertemplate: '<b>%{x}</b><br>Risk: %{y:.2f}/10<br>Tier: %{text}<extra></extra>',
            text: tiers
        };

        const layout = {
            height: 300,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: false },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            bargap: 0.1
        };

        Plotly.newPlot('alertHistory', [trace], layout, { responsive: true });
    },

    displayStatsTable(data) {
        const stats = RiskCalculator.calculateStats(data);

        const html = `
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #667eea;">Metric</th>
                    <th style="padding: 10px; text-align: right; border-bottom: 2px solid #667eea;">Value</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Total Data Points</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.totalPoints}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Mean Risk Score</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.mean}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Median Risk Score</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.median}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Maximum Risk</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0; color: ${CONFIG.CHART_COLORS.RED}; font-weight: bold;">${stats.max}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Minimum Risk</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0; color: ${CONFIG.CHART_COLORS.GREEN}; font-weight: bold;">${stats.min}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">Standard Deviation</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.stdDev}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">95th Percentile</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.p95}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">5th Percentile</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0;">${stats.p05}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f0f0f0;">YELLOW Alerts (≥4.0)</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #f0f0f0; color: ${CONFIG.CHART_COLORS.YELLOW}; font-weight: bold;">${stats.yellowAlerts}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;">RED Alerts (≥5.0)</td>
                    <td style="padding: 10px; text-align: right; color: ${CONFIG.CHART_COLORS.RED}; font-weight: bold;">${stats.redAlerts}</td>
                </tr>
            </table>
        `;

        document.getElementById('statsTable').innerHTML = html;
    },

    createCorrelationMatrix(data) {
        const correlations = RiskCalculator.calculateCorrelations(data);
        const dimensions = ['recession', 'credit', 'valuation', 'liquidity', 'positioning'];

        // Convert to matrix format for heatmap
        const zValues = dimensions.map(dim1 =>
            dimensions.map(dim2 => correlations[dim1][dim2])
        );

        const trace = {
            z: zValues,
            x: dimensions.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
            y: dimensions.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
            type: 'heatmap',
            colorscale: [
                [0, '#3b82f6'],
                [0.5, '#f8f9fa'],
                [1, '#ef4444']
            ],
            zmid: 0,
            zmin: -1,
            zmax: 1,
            hovertemplate: '%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>',
            showscale: true,
            colorbar: {
                title: 'Correlation',
                titleside: 'right'
            }
        };

        // Add text annotations
        const annotations = [];
        for (let i = 0; i < dimensions.length; i++) {
            for (let j = 0; j < dimensions.length; j++) {
                annotations.push({
                    x: dimensions[j].charAt(0).toUpperCase() + dimensions[j].slice(1),
                    y: dimensions[i].charAt(0).toUpperCase() + dimensions[i].slice(1),
                    text: zValues[i][j].toFixed(2),
                    showarrow: false,
                    font: { color: Math.abs(zValues[i][j]) > 0.5 ? 'white' : 'black' }
                });
            }
        }

        const layout = {
            height: 400,
            margin: { t: 20, r: 20, b: 80, l: 80 },
            annotations: annotations,
            xaxis: { side: 'bottom' },
            yaxis: { autorange: 'reversed' }
        };

        Plotly.newPlot('correlationMatrix', [trace], layout, { responsive: true });
    },

    createEventsTimeline(data) {
        const dates = data.map(d => d.date);
        const scores = data.map(d => d.overall_risk);

        // Create a simple line chart with event overlays
        const trace = {
            x: dates,
            y: scores,
            type: 'scatter',
            mode: 'lines',
            line: { color: CONFIG.CHART_COLORS.PRIMARY, width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(102, 126, 234, 0.2)',
            hovertemplate: '<b>%{x}</b><br>Risk: %{y:.2f}/10<extra></extra>'
        };

        // Define all crisis periods
        const allCrisisPeriods = [
            {
                x0: '2000-03-01',
                x1: '2002-10-01',
                label: { x: '2001-03-01', text: 'Dot-Com<br>Crash' },
                fillcolor: 'rgba(239, 68, 68, 0.1)'
            },
            {
                x0: '2007-10-01',
                x1: '2009-03-01',
                label: { x: '2008-06-01', text: 'Financial<br>Crisis' },
                fillcolor: 'rgba(239, 68, 68, 0.1)'
            },
            {
                x0: '2020-02-01',
                x1: '2020-04-01',
                label: { x: '2020-03-01', text: 'COVID<br>Crash' },
                fillcolor: 'rgba(239, 68, 68, 0.1)'
            },
            {
                x0: '2022-01-01',
                x1: '2022-10-01',
                label: { x: '2022-06-01', text: '2022 Bear<br>Market' },
                fillcolor: 'rgba(245, 158, 11, 0.1)'
            }
        ];

        // Filter crisis periods to only show those within visible date range
        const startDate = new Date(dates[0]);
        const endDate = new Date(dates[dates.length - 1]);

        const visibleCrises = allCrisisPeriods.filter(crisis => {
            const crisisStart = new Date(crisis.x0);
            const crisisEnd = new Date(crisis.x1);
            // Show if any part of the crisis overlaps with visible range
            return crisisEnd >= startDate && crisisStart <= endDate;
        });

        // Build shapes and annotations only for visible crises
        const shapes = visibleCrises.map(crisis => ({
            type: 'rect',
            x0: crisis.x0,
            x1: crisis.x1,
            y0: 0,
            y1: 10,
            fillcolor: crisis.fillcolor,
            line: { width: 0 }
        }));

        const annotations = visibleCrises.map(crisis => ({
            x: crisis.label.x,
            y: 9,
            text: crisis.label.text,
            showarrow: false,
            font: { size: 10 }
        }));

        const layout = {
            height: 300,
            margin: { t: 20, r: 20, b: 60, l: 60 },
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#f0f0f0' },
            yaxis: { title: 'Risk Score', range: [0, 10], showgrid: true, gridcolor: '#f0f0f0' },
            shapes: shapes,
            annotations: annotations,
            showlegend: false
        };

        Plotly.newPlot('eventsTimeline', [trace], layout, { responsive: true });
    }
};

// Time selector event handlers
const TimeSelector = {
    init() {
        const buttons = document.querySelectorAll('.time-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active state
                buttons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Update charts
                currentPeriod = e.target.dataset.period;
                this.updateCharts();
            });
        });
    },

    updateCharts() {
        const filteredData = TimeFilter.filterByPeriod(fullData, currentPeriod);

        ChartRenderer.createRiskTimeline(filteredData);
        ChartRenderer.createDimensionTimeline(filteredData);
        ChartRenderer.createAlertHistory(filteredData);
        ChartRenderer.displayStatsTable(filteredData);
        ChartRenderer.createCorrelationMatrix(filteredData);
        ChartRenderer.createEventsTimeline(filteredData);
    }
};

// Main app
const HistoryApp = {
    async init() {
        try {
            UIUpdater.showLoading();
            fullData = await DataLoader.loadData();

            UIUpdater.showCharts();

            // Initialize time selector
            TimeSelector.init();

            // Render charts with full data
            ChartRenderer.createRiskTimeline(fullData);
            ChartRenderer.createDimensionTimeline(fullData);
            ChartRenderer.createAlertHistory(fullData);
            ChartRenderer.displayStatsTable(fullData);
            ChartRenderer.createCorrelationMatrix(fullData);
            ChartRenderer.createEventsTimeline(fullData);

            console.log('✓ History page initialized');
        } catch (error) {
            console.error('Failed to initialize:', error);
            UIUpdater.showError(error.message);
        }
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    HistoryApp.init();
});

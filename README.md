# Aegis: Real-Time Macro Defense

**Personal early warning system for portfolio risk management**

## Overview

Aegis monitors quantitative macro indicators in real-time and alerts you when conditions suggest defensive portfolio positioning is warranted. Unlike news-based sentiment analysis, Aegis focuses on objective economic data from trusted sources (FRED, BLS, CBOE, etc.).

**Mission:** Preserve capital by detecting elevated risk conditions before major drawdowns.

**Philosophy:** You can't predict crashes, but you can prepare for them.

## Key Features

- **Data-First Architecture**: Direct API access to FRED, Yahoo Finance, Shiller CAPE, ISM surveys
- **Multi-Dimensional Risk Scoring**: Recession indicators, credit stress, valuation extremes, liquidity conditions, geopolitical risk
- **Rare but Actionable Alerts**: Only notifies when risk crosses your personal threshold (2-5 alerts/year expected)
- **Historical Backtesting**: Validate signal accuracy against 2000-2024 market history
- **Simple Dashboard**: Optional web view of current risk levels and trends

## System Architecture

```
Data Sources (APIs)
    ↓
Data Pipeline (FRED, Yahoo Finance, Shiller)
    ↓
Risk Scoring (5 dimensions × weights)
    ↓
Alert Logic (threshold + trend analysis)
    ↓
Notifications (email) + History (time series)
```

## Risk Dimensions

### 1. Recession Risk (30% weight)
- Yield curve inversion (10Y-2Y spread)
- Unemployment trends
- ISM Manufacturing PMI
- Consumer confidence

### 2. Credit Stress (25% weight)
- High-yield credit spreads
- Investment-grade spreads
- Bank lending standards
- Commercial real estate concerns

### 3. Valuation Extremes (20% weight)
- Shiller CAPE ratio
- Market cap / GDP (Buffett indicator)
- Forward P/E relative to history

### 4. Liquidity Conditions (15% weight)
- Fed funds rate trajectory
- M2 money supply growth
- Margin debt levels
- Fed balance sheet changes

### 5. Geopolitical Risk (10% weight)
- Policy uncertainty index
- Commodity price shocks
- Supply chain disruptions
- Major conflict escalation

## Alert Tiers

- **RED (8.0-10.0)**: Severe risk - consider significant defensive positioning
- **YELLOW (6.5-7.9)**: Elevated risk - review portfolio, build cash reserves
- **GREEN (0-6.4)**: Normal conditions - maintain course

**Alert triggers:**
- Risk score ≥ 7.0
- OR risk score ≥ 6.5 AND rising rapidly (>1.0 point in 4 weeks)
- OR multiple dimensions ≥ 8.0 simultaneously

## Data Sources

All sources are free or low-cost APIs:

- **FRED** (Federal Reserve Economic Data): 500,000+ time series, free API
- **Yahoo Finance**: Market prices, ETF data, sector performance
- **Shiller Data**: CAPE ratio, updated monthly
- **ISM**: Manufacturing/Services PMI surveys
- **CBOE**: VIX, VVIX (volatility indicators)
- **BLS**: Employment data, CPI

## Quick Start

### Installation

```bash
# Clone and navigate
cd C:\local_dev\Aegis

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config/credentials/secrets.ini.example config/credentials/secrets.ini
# Edit secrets.ini with your FRED API key

# Test configuration
python src/config/config_manager.py --test
```

### Get FRED API Key (Free)

1. Visit: https://fred.stlouisfed.org/
2. Create free account
3. Request API key: https://fred.stlouisfed.org/docs/api/api_key.html
4. Add to `config/credentials/secrets.ini`

### Run Your First Update

```bash
# Fetch latest data and calculate risk score
python scripts/daily_update.py

# View current risk assessment
python scripts/show_status.py

# Generate weekly report (sends email if alert triggered)
python scripts/weekly_report.py
```

## Configuration

### Indicator Configuration (`config/indicators.yaml`)

Define which FRED series to track, scoring formulas, and historical thresholds.

### Threshold Configuration (`config/thresholds.yaml`)

Set your personal risk tolerance and alert thresholds.

### Secrets (`config/credentials/secrets.ini`)

API keys and email credentials (gitignored).

## Scheduled Automation

### Daily Data Update (Cron/Task Scheduler)

```bash
# Linux/Mac crontab
0 18 * * * cd /path/to/aegis && python scripts/daily_update.py

# Windows Task Scheduler
# Run daily at 6 PM: python C:\local_dev\Aegis\scripts\daily_update.py
```

### Weekly Risk Report

```bash
# Every Monday at 8 AM
0 8 * * 1 cd /path/to/aegis && python scripts/weekly_report.py
```

## Optional Dashboard

```bash
# Launch local web dashboard
python src/dashboard/app.py

# Visit: http://localhost:5000
```

## Backtesting

```bash
# Validate against historical data
python scripts/backtest.py --start-date 2000-01-01 --end-date 2024-12-31

# Output: Alert accuracy, lead time, false positive rate
```

## Project Structure

```
aegis/
├── config/
│   ├── credentials/
│   │   ├── secrets.ini          # API keys (gitignored)
│   │   └── secrets.ini.example  # Template
│   ├── indicators.yaml          # Data sources and scoring rules
│   ├── thresholds.yaml          # Alert configuration
│   └── app.yaml                 # General settings
├── src/
│   ├── config/
│   │   └── config_manager.py    # Configuration loader
│   ├── data/
│   │   ├── fred_client.py       # FRED API wrapper
│   │   ├── market_data.py       # Yahoo Finance integration
│   │   ├── shiller.py           # CAPE ratio scraper
│   │   └── data_manager.py      # Data fetching orchestrator
│   ├── scoring/
│   │   ├── recession.py         # Recession risk calculator
│   │   ├── credit.py            # Credit stress calculator
│   │   ├── valuation.py         # Valuation extreme calculator
│   │   ├── liquidity.py         # Liquidity conditions calculator
│   │   ├── geopolitical.py      # Geopolitical risk (TBD)
│   │   └── aggregator.py        # Weighted risk aggregation
│   ├── alerts/
│   │   ├── alert_logic.py       # Threshold checking & triggers
│   │   └── email_sender.py      # Email notification
│   └── dashboard/
│       ├── app.py               # Flask web dashboard (optional)
│       └── templates/           # HTML templates
├── data/
│   └── history/
│       ├── risk_scores.csv      # Time series of daily scores
│       └── raw_indicators.csv   # Historical indicator values
├── scripts/
│   ├── daily_update.py          # Fetch data, calculate score, log
│   ├── weekly_report.py         # Generate report, send alert if needed
│   ├── show_status.py           # Display current risk assessment
│   └── backtest.py              # Historical validation
├── tests/
│   ├── test_scoring.py          # Unit tests for scoring logic
│   └── test_data.py             # Data pipeline tests
├── docs/
│   ├── methodology.md           # Detailed scoring methodology
│   ├── indicators.md            # Indicator definitions and rationale
│   └── backtest_results.md      # Historical performance
├── .gitignore
├── requirements.txt
├── README.md
└── CLAUDE.md                    # Instructions for Claude Code
```

## Development Workflow

1. **Daily automated update**: Fetch latest data, calculate scores, store history
2. **Weekly review**: Check for alert conditions, send email if triggered
3. **Monthly calibration**: Review track record, adjust weights/thresholds if needed
4. **Quarterly backtest**: Validate against recent data

## Design Principles

### 1. Objectivity Over Narrative
- Use direct data sources, not news commentary
- Clear scoring formulas, not subjective interpretation
- Reproducible calculations

### 2. Simplicity Over Sophistication
- 5 dimensions, not 50
- Linear weighted scoring, not ML black box
- Transparent methodology

### 3. Rare Alerts Over Constant Noise
- High bar for alerts (expect 2-5/year)
- When you get an alert, pay attention
- No weekly newsletters when nothing matters

### 4. Personal Calibration
- Tune thresholds to YOUR risk tolerance
- Track YOUR success rate
- Adjust based on YOUR outcomes

### 5. Backtest Everything
- Validate on historical data before trusting
- Measure: accuracy, lead time, false positive rate
- Iterate based on evidence

## Future Enhancements

- [ ] Add news overlay for Black Swan detection (integrate with NexusMind)
- [ ] Sector rotation signals (defensive vs cyclical)
- [ ] International markets (non-US risk assessment)
- [ ] Options positioning data (put/call ratios)
- [ ] Credit impulse indicators (China, emerging markets)
- [ ] Web dashboard with historical charts
- [ ] Mobile app notifications
- [ ] Multi-user support (share with friends/family)

## License

Personal use. If you build a business on this, consider open-sourcing or licensing appropriately.

## Author

Built for personal capital preservation.

---

**Tagline:** *Protecting portfolios through quantitative macro monitoring*

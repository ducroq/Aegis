# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation Structure

Aegis uses the **AI-Augmented Solo Dev Framework** for progressive disclosure of context:

**Start Here (High-Level Overview):**
- `docs/PROJECT_OVERVIEW.md` - Current status, active focus, quick links
- `docs/ARCHITECTURE.md` - System design, components, data flow
- `README.md` - Quick start and installation

**Current Work:**
- `docs/CURRENT_TASK.md` - What's being worked on right now
- `docs/OPEN_QUESTIONS.md` - Unresolved decisions and blockers
- `docs/ROADMAP.md` - Now/Next/Later priorities

**Deep Dives (Progressive Disclosure):**
- `docs/components/` - Detailed component documentation (FRED client, scorers, aggregator)
- `docs/decisions/` - Architecture Decision Records (ADRs) for major methodology choices
- `docs/INDICATORS_CATALOG.md` - Complete reference of all indicators
- `docs/BACKTESTING_RESULTS.md` - Historical validation metrics
- `docs/METHODOLOGY_EVOLUTION.md` - Timeline of methodology changes

**How to Navigate:**
1. **Quick orientation:** Read `PROJECT_OVERVIEW.md` first (5 min)
2. **Understanding architecture:** Read `ARCHITECTURE.md` (10 min)
3. **Working on specific component:** Check `docs/components/[name].md`
4. **Understanding past decisions:** Check `docs/decisions/` ADRs
5. **Implementation details:** This CLAUDE.md file (below)

---

## Project Overview

**Aegis** is a personal early warning system for portfolio risk management. It monitors quantitative macro indicators from free/low-cost APIs (FRED, Yahoo Finance, Shiller) and alerts the user when risk conditions suggest defensive positioning.

**Core Philosophy:**
- Data > News: Use direct economic data, not news commentary
- Rare alerts: High bar for notifications (2-5 per year expected)
- Objective scoring: Clear formulas, reproducible calculations
- Personal calibration: Tuned to user's risk tolerance

## Architecture

### Data Flow

```
APIs (FRED, Yahoo Finance, Shiller)
    ↓
Data Fetchers (src/data/)
    ↓
Risk Scorers (src/scoring/)
    ↓
Aggregator (weighted score 0-10)
    ↓
Alert Logic (threshold checking)
    ↓
Email Alert + History Storage
```

### Risk Dimensions (5 total, weights sum to 1.0) - ENHANCED

1. **Recession Risk** (0.30):
   - Unemployment claims VELOCITY (YoY % change) - leading indicator
   - ISM PMI regime cross detection (expansion → contraction)
   - Dual yield curve (10Y-2Y + 3M→18M forward spread)

2. **Credit Stress** (0.25):
   - High-yield spread VELOCITY (70% weight) + level (30%)
   - Investment-grade spreads
   - Bank lending standards
   - TED spread

3. **Valuation Extremes** (0.20):
   - CAPE ratio, Buffett indicator, forward P/E

4. **Liquidity Conditions** (0.15):
   - Fed funds rate of change, M2 velocity, margin debt

5. **Positioning & Speculation** (0.10): **NEW**
   - CFTC S&P 500 net speculative positioning (contrarian)
   - CFTC Treasury positioning (squeeze risk)
   - VIX futures positioning (complacency)

**Key Philosophy**: Rate of change > absolute values for leading signals.

Each dimension scored 0-10, then weighted average = overall risk score.

### Alert Tiers

- **RED (8.0-10.0)**: Severe risk - consider major defensive positioning
- **YELLOW (6.5-7.9)**: Elevated risk - review portfolio, build cash
- **GREEN (0-6.4)**: Normal conditions - stay the course

**Alert Triggers:**
- Risk ≥ 7.0
- OR risk ≥ 6.5 AND rising >1.0 point in 4 weeks
- OR 2+ dimensions ≥ 8.0 simultaneously

## Project Status

**Current State:** Core system implemented with Signals #1-6 complete. Historical data backfill completed (300 months: 2000-2024).

**✅ Completed:**
- Core infrastructure (config, data fetchers, scoring engines)
- Signals #1-6 implemented and tested
- **Historical data backfill: 300 months (2000-01-01 to 2024-12-01)**
  - `data/history/risk_scores.csv`: 301 rows, 8 columns
  - `data/history/raw_indicators.csv`: 301 rows, 38 columns
  - Zero failures, all CSV integrity checks passed
- Risk aggregation and alert logic
- Signal #4 (Earnings Recession) backtest script (`scripts/test_earnings_recession_signal.py`)
- Incremental backfill script (`scripts/incremental_backfill.py`)

**🔄 In Progress:**
- Signal #7 (Dollar Liquidity Stress) - data sources added, logic pending (see `TODO_SIGNALS.md`)
- Signal #10 (Retail Capitulation) - requires manual AAII data

**Implementation Priority:**
1. ✅ `src/config/config_manager.py` - COMPLETE
2. ✅ `src/data/` modules - COMPLETE (FRED, Yahoo Finance, Shiller)
3. ✅ `src/scoring/` modules - COMPLETE (Recession, Credit, Valuation, Liquidity, Positioning)
4. ⏳ `scripts/` - Partial (backtest scripts done, daily/weekly pending)
5. ⏳ `src/alerts/` - Partial (logic done, email delivery pending)

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API credentials
# Windows:
copy config\credentials\secrets.ini.example config\credentials\secrets.ini
# Mac/Linux:
cp config/credentials/secrets.ini.example config/credentials/secrets.ini

# Edit secrets.ini and add your FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html

# Test configuration (once config_manager.py is implemented)
python src/config/config_manager.py --test
```

### Daily Workflow (Once Implemented)
```bash
# Fetch latest data and calculate risk score
python scripts/daily_update.py

# View current status
python scripts/show_status.py

# Generate weekly report (with alert if triggered)
python scripts/weekly_report.py
```

### Development & Testing
```bash
# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=src tests/

# Backtest historical data (once implemented)
python scripts/backtest.py --start-date 2000-01-01

# Launch dashboard (optional, lower priority)
python src/dashboard/app.py
```

## Implementation Guidelines

### Code Style & Patterns
- **Type hints**: Use Python type hints for all function signatures
- **Docstrings**: Google-style docstrings for all public functions/classes
- **Error handling**: Graceful degradation for missing data (use last known value)
- **Logging**: Use Python logging module (configured in `config/app.yaml`)
- **Testing**: Write unit tests alongside implementation (pytest)

### Critical Design Principles
1. **Reproducibility**: Same inputs = same outputs. No randomness in scoring.
2. **Transparency**: All scoring thresholds must be in config files, not hardcoded.
3. **Auditability**: Log all data fetches, score calculations, and alert decisions.
4. **Backtest-friendly**: Never use future data (watch for look-ahead bias).
5. **Fail gracefully**: If one indicator fails to fetch, calculate score with available data.

### Module Dependencies
```
config_manager.py (no dependencies, load first)
    ↓
data/*.py (depends on config_manager)
    ↓
scoring/*.py (depends on data modules)
    ↓
alerts/*.py (depends on scoring)
    ↓
scripts/*.py (orchestrates everything)
```

## Configuration System

### File Structure
```
config/
├── app.yaml                 # General settings, dimension weights
├── indicators.yaml          # Data sources, scoring formulas
├── regime_shifts.yaml       # Qualitative event detection rules
└── credentials/
    ├── secrets.ini          # API keys (gitignored)
    └── secrets.ini.example  # Template
```

### Configuration Loading
- Hierarchical config with dot notation (e.g., `config.get("scoring.weights.recession")`)
- Environment variables override file configs (`AEGIS_*` prefix)
- Secrets loaded separately from `secrets.ini` (API keys, email credentials)
- Validation: Check weight sums = 1.0, required fields present

### Example Access
```python
from src.config.config_manager import ConfigManager

config = ConfigManager()
fred_key = config.get_secret("fred_api_key")
recession_weight = config.get("scoring.weights.recession", 0.30)
alert_threshold = config.get("alerts.yellow_threshold", 6.5)
```

## Data Sources

### FRED (Primary Source)
**Library:** `fredapi`
```python
from fredapi import Fred
fred = Fred(api_key=config.get_secret("fred_api_key"))

# Example series
yield_curve = fred.get_series('T10Y2Y')  # 10Y-2Y Treasury spread
unemployment = fred.get_series('UNRATE')
hy_spreads = fred.get_series('BAMLH0A0HYM2')  # High-yield option-adjusted spread
```

**Key Series:**
- `T10Y2Y`: 10Y-2Y yield spread (recession indicator)
- `UNRATE`: Unemployment rate
- `BAMLH0A0HYM2`: High-yield corporate bond spreads
- `BAMLC0A4CBBB`: BBB corporate bond spreads
- `M2SL`: M2 money supply
- `DFF`: Federal funds effective rate

Full list in `config/indicators.yaml`

### Yahoo Finance
**Library:** `yfinance`
```python
import yfinance as yf

# Market data
sp500 = yf.Ticker("^GSPC")
vix = yf.Ticker("^VIX")

# Sector rotation
xlv = yf.download("XLV", period="1y")  # Healthcare (defensive)
xly = yf.download("XLY", period="1y")  # Consumer discretionary (cyclical)
```

### Shiller CAPE
**Source:** http://www.econ.yale.edu/~shiller/data.htm
- Download Excel file monthly
- Parse "Price", "Earnings", "CAPE" columns
- Store in local cache

## Scoring Methodology

### Example: Recession Risk Calculator

```python
# src/scoring/recession.py

def calculate_recession_risk(yield_curve, unemployment, pmi, consumer_confidence):
    """
    Calculate recession risk score (0-10)

    Args:
        yield_curve: 10Y-2Y spread (percentage points)
        unemployment: Unemployment rate (%)
        pmi: ISM Manufacturing PMI (index)
        consumer_confidence: Conference Board index

    Returns:
        float: Risk score 0-10
    """
    score = 0.0

    # Yield curve inversion (strongest signal)
    if yield_curve < -0.5:
        score += 4.0  # Deep inversion
    elif yield_curve < 0:
        score += 2.0  # Shallow inversion

    # Unemployment trend (use 3-month change)
    if unemployment_trend > 0.3:
        score += 3.0  # Rising unemployment
    elif unemployment_trend > 0.1:
        score += 1.5

    # PMI below 50 = contraction
    if pmi < 45:
        score += 2.0  # Deep contraction
    elif pmi < 50:
        score += 1.0  # Mild contraction

    # Consumer confidence dropping
    if consumer_confidence < 90:
        score += 1.0

    return min(score, 10.0)  # Cap at 10
```

**Important:** All scoring functions should:
- Return 0-10 float
- Use clear thresholds from historical data
- Document rationale in comments
- Be backtestable

### Aggregation

```python
# src/scoring/aggregator.py

def calculate_overall_risk(dimension_scores, weights):
    """
    Weighted average of dimension scores

    Args:
        dimension_scores: dict with keys: recession, credit, valuation, liquidity, geopolitical
        weights: dict with same keys (must sum to 1.0)

    Returns:
        float: Overall risk score 0-10
    """
    validate_weights(weights)  # Ensure sum = 1.0

    overall = sum(
        dimension_scores[dim] * weights[dim]
        for dim in dimension_scores
    )

    return round(overall, 2)
```

## Alert System

### Alert Logic

```python
# src/alerts/alert_logic.py

def should_alert(current_score, history, thresholds):
    """
    Determine if alert should be sent

    Args:
        current_score: Today's risk score
        history: List of recent scores (past 4+ weeks)
        thresholds: Config dict with yellow/red thresholds

    Returns:
        tuple: (should_alert: bool, tier: str, reason: str)
    """
    # Threshold alert
    if current_score >= thresholds['red']:
        return (True, 'RED', f'Risk score {current_score:.1f} exceeds RED threshold')

    if current_score >= thresholds['yellow']:
        # Check if rising rapidly
        if len(history) >= 4:
            four_week_change = current_score - history[-4]
            if four_week_change > 1.0:
                return (True, 'YELLOW', f'Risk rising rapidly: +{four_week_change:.1f} in 4 weeks')

        return (True, 'YELLOW', f'Risk score {current_score:.1f} exceeds YELLOW threshold')

    return (False, 'GREEN', 'Risk within normal range')
```

### Email Format

See `src/alerts/email_sender.py` for template. Key sections:
1. **Subject line**: Attention-grabbing for alerts (`⚠️ Portfolio Alert: Risk 7.2/10`)
2. **Risk summary**: Overall score + tier + change from last week
3. **Dimension breakdown**: Individual scores with trend arrows
4. **Key evidence**: Specific data points that triggered alert
5. **Suggested actions**: What to consider (not prescriptive advice)
6. **Track record**: Historical alert accuracy

## Data Storage

### Time Series Format

```csv
# data/history/risk_scores.csv
date,overall_risk,recession,credit,valuation,liquidity,geopolitical,alerted,tier
2025-01-06,7.2,7.5,6.8,8.5,4.0,5.5,true,YELLOW
2025-01-13,7.0,7.3,6.5,8.5,4.2,5.3,false,YELLOW
...
```

### Raw Indicators

```csv
# data/history/raw_indicators.csv
date,yield_curve,unemployment,hy_spreads,cape_ratio,vix,...
2025-01-06,-0.85,3.7,5.2,32.1,18.5,...
...
```

**Retention:** Keep all historical data (small files, valuable for backtesting)

## Testing Strategy

### Unit Tests
```python
# tests/test_scoring.py

def test_recession_risk_inverted_curve():
    """Test that inverted yield curve increases recession score"""
    score = calculate_recession_risk(
        yield_curve=-0.8,  # Inverted
        unemployment=3.5,
        pmi=52,
        consumer_confidence=100
    )
    assert score >= 4.0, "Inverted curve should trigger high score"

def test_recession_risk_normal_conditions():
    """Test that normal conditions give low score"""
    score = calculate_recession_risk(
        yield_curve=1.5,   # Positive spread
        unemployment=4.0,  # Low unemployment
        pmi=54,            # Expansion
        consumer_confidence=110
    )
    assert score <= 2.0, "Normal conditions should give low score"
```

### Backtesting
```python
# scripts/backtest.py

# Load historical data (2000-2024)
# Calculate what risk scores would have been
# Compare to actual market drawdowns:
#   - 2000-2002 Tech bubble (-49%)
#   - 2007-2009 Financial crisis (-57%)
#   - 2020 COVID crash (-34%)
#   - 2022 Bear market (-25%)

# Metrics:
#   - True positives: Alerted before drawdown
#   - False positives: Alerted but no drawdown
#   - Lead time: Days between alert and peak
#   - Missed crashes: Drawdowns without alerts
```

## Common Patterns

### When Adding New Indicators

1. **Find data source**: FRED series ID or other API
2. **Add to config**: `config/indicators.yaml`
3. **Create fetcher**: `src/data/indicator_name.py`
4. **Update scorer**: Add to relevant dimension in `src/scoring/`
5. **Backtest**: Validate on historical data
6. **Document**: Add to `docs/indicators.md`

### When Adjusting Weights

1. **Edit config**: `config/app.yaml` → `scoring.weights.*`
2. **Ensure sum = 1.0**: Validation in `aggregator.py`
3. **Backtest**: Compare old vs new weights on historical data
4. **Track forward**: Monitor next 3-6 months to validate

### When Tuning Thresholds

1. **Check track record**: How many alerts in past 12 months?
2. **Too many alerts** (>6/year): Raise threshold (6.5 → 7.0)
3. **Too few alerts** (<2/year): Lower threshold (7.0 → 6.5)
4. **False alarms**: Increase minimum persistence (e.g., 2 weeks above threshold)

## Current File Status

### ✅ Complete (Configuration & Documentation)
- `config/app.yaml` - Application settings and dimension weights
- `config/indicators.yaml` - Detailed indicator definitions and scoring rules
- `config/regime_shifts.yaml` - Qualitative event detection configuration
- `config/credentials/secrets.ini.example` - Template for API keys
- `README.md` - Project overview and quick start
- `docs/methodology.md` - Detailed scoring methodology with enhancements
- `docs/getting_started.md` - Step-by-step setup guide
- `requirements.txt` - Python dependencies

### 🚧 To Be Implemented (Python Modules)
**Priority 1 - Core Infrastructure:**
- `src/config/config_manager.py` - Load YAML configs and secrets
- `src/data/fred_client.py` - FRED API wrapper
- `src/data/market_data.py` - Yahoo Finance integration
- `src/data/data_manager.py` - Orchestrate all data fetching

**Priority 2 - Scoring Logic:**
- `src/scoring/recession.py` - Recession risk calculator (velocity-based)
- `src/scoring/credit.py` - Credit stress calculator (velocity + level)
- `src/scoring/valuation.py` - Valuation extremes (CAPE, Buffett indicator)
- `src/scoring/liquidity.py` - Liquidity conditions (Fed policy, M2)
- `src/scoring/positioning.py` - CFTC positioning (NEW dimension)
- `src/scoring/aggregator.py` - Weighted risk aggregation
- `src/scoring/regime_shift.py` - LLM-based qualitative overlay (optional)

**Priority 3 - Alerts & Reporting:**
- `src/alerts/alert_logic.py` - Threshold checking and trigger conditions
- `src/alerts/email_sender.py` - Email notification system

**Priority 4 - Scripts (Orchestration):**
- `scripts/daily_update.py` - Fetch data, calculate scores, store history
- `scripts/show_status.py` - Display current risk assessment
- `scripts/weekly_report.py` - Generate report, send alerts if triggered
- `scripts/backtest.py` - Historical validation

**Priority 5 - Testing:**
- `tests/test_config.py` - Config loading tests
- `tests/test_scoring.py` - Scoring function unit tests
- `tests/test_data.py` - Data fetching tests

**Lower Priority:**
- `src/data/shiller.py` - Shiller CAPE data scraper (manual monthly update)
- `src/data/cftc_client.py` - CFTC Commitments of Traders data
- `src/dashboard/app.py` - Optional Flask dashboard

## Important Gotchas

### 1. Data Lag
- GDP: Released quarterly with 1-month lag
- Unemployment: Monthly with 1-week lag
- PMI: Monthly, released first week of month
- CAPE: Monthly update from Shiller

**Strategy:** Use most timely indicators (yield curve, credit spreads update daily)

### 2. Look-Ahead Bias in Backtesting
- Only use data available at time of calculation
- Don't use revised data (e.g., GDP revisions happen months later)
- FRED has "real-time" data for some series

### 3. API Rate Limits
- FRED: No official limit, but be reasonable
- Yahoo Finance: No official API, may break
- Have fallback data sources

### 4. Market Holidays
- FRED data not updated on weekends/holidays
- Handle missing data gracefully
- Use last available value if current day missing

## Future Enhancements (Backlog)

1. **News overlay**: Integrate with NexusMind for Black Swan detection
2. **Options data**: Put/call ratios, skew
3. **Sector rotation**: Defensive vs cyclical performance
4. **International**: Non-US recession indicators
5. **Credit impulse**: Leading indicator from China credit growth
6. **Dashboard**: Flask app with charts (Plotly/Chart.js)
7. **Mobile app**: Push notifications instead of email
8. **Multi-user**: Share with friends/family

## When to Use This System

**Good use cases:**
- Personal portfolio (ETF-based, $20K-$500K)
- Monthly/quarterly rebalancing decisions
- "Should I build cash position?" questions
- Long-term risk management

**Bad use cases:**
- Day trading signals
- Short-term market timing
- Individual stock selection
- Options trading strategies

## Philosophy

**What Aegis is:**
- Early warning system for macro deterioration
- Objective data aggregation with clear methodology
- Personal risk management tool

**What Aegis is NOT:**
- Market timing oracle (can't predict crashes)
- Investment advice (user makes own decisions)
- Get-rich-quick system (about preserving, not growing)
- Black box ML (transparent scoring rules)

## Critical Success Factors

1. **Backtest thoroughly**: Don't trust until validated on 2000-2024 data
2. **Start conservative**: High thresholds initially (avoid false alarms)
3. **Track accuracy**: Log every alert, compare to outcomes
4. **Iterate slowly**: Adjust based on 6-12 months of data, not 1 week
5. **Stay objective**: Don't override system based on gut feel

---

**Remember:** The goal is to avoid major drawdowns (>20%), not to time every 5% dip. Being late to exit is better than false alarms that cause you to miss bull markets.

# Aegis - System Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                             │
├─────────────┬──────────────────┬─────────────────┬──────────────┤
│   FRED API  │  Yahoo Finance   │  Shiller Data   │  CFTC Data   │
│  (Primary)  │   (Market Data)  │  (CAPE Ratio)   │ (Positioning)│
└──────┬──────┴────────┬─────────┴────────┬────────┴──────┬───────┘
       │               │                  │               │
       ▼               ▼                  ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Fetchers Layer                         │
├──────────────┬──────────────┬─────────────┬─────────────────────┤
│ FREDClient   │ MarketData   │ ShillerData │ DataManager         │
│ (Caching,    │ Client       │ Scraper     │ (Orchestration)     │
│  Velocity)   │              │             │                     │
└──────┬───────┴──────┬───────┴──────┬──────┴─────────┬───────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Risk Scoring Layer (0-10)                      │
├──────────┬─────────┬───────────┬──────────┬─────────────────────┤
│Recession │ Credit  │Valuation  │Liquidity │ Positioning         │
│ Scorer   │ Scorer  │ Scorer    │ Scorer   │ Scorer              │
│ (30%)    │ (25%)   │ (20%)     │ (15%)    │ (10%)               │
└────┬─────┴────┬────┴─────┬─────┴────┬─────┴─────┬───────────────┘
     │          │          │          │           │
     └──────────┴──────────┴──────────┴───────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Aggregator     │
              │ (Weighted Score) │
              │    0-10 scale    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Alert Logic     │
              │ (Threshold Check)│
              │ GREEN/YELLOW/RED │
              └────────┬─────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  Email Sender    │      │ History Manager  │
│ (Notifications)  │      │ (CSV Storage)    │
└──────────────────┘      └──────────────────┘
```

## Core Components

### 1. Configuration Manager (`src/config/config_manager.py`)

**Purpose:** Centralized configuration loading and secret management

**Responsibilities:**
- Load YAML configs (app.yaml, indicators.yaml, regime_shifts.yaml)
- Manage secrets from secrets.ini (API keys, email credentials)
- Validate dimension weights sum to 1.0
- Provide dot-notation access to config values

**Key Dependencies:**
- PyYAML for config parsing
- configparser for secrets

**Interface:**
```python
config = ConfigManager()
config.get("scoring.weights.recession", default=0.30)
config.get_secret("fred_api_key")
config.get_all_weights()
config.get_alert_thresholds()
```

### 2. FRED Client (`src/data/fred_client.py`)

**Purpose:** Fetch economic data from FRED API with caching and velocity calculations

**Responsibilities:**
- Fetch time series from FRED
- Cache data locally with TTL
- Calculate velocity (YoY % change, rate of change)
- Compute moving averages

**Key Dependencies:**
- fredapi library
- pandas for time series
- File-based caching

**Interface:**
```python
client = FREDClient(config, cache_dir)
series = client.get_series('T10Y2Y', use_cache=True)
velocity = client.calculate_velocity('ICSA', method='yoy_pct')
ma = client.get_moving_average('UNRATE', window=12)
```

### 3. Market Data Client (`src/data/market_data.py`)

**Purpose:** Fetch market data from Yahoo Finance

**Responsibilities:**
- Download S&P 500, VIX, sector ETFs
- Calculate forward P/E estimates
- Track defensive vs cyclical performance

**Key Dependencies:**
- yfinance library
- pandas

### 4. Data Manager (`src/data/data_manager.py`)

**Purpose:** Orchestrate all data fetching for risk calculation

**Responsibilities:**
- Coordinate fetching from multiple sources
- Assemble indicator dict for scorers
- Handle missing data gracefully

**Key Dependencies:**
- FREDClient, MarketDataClient

**Interface:**
```python
manager = DataManager(config)
indicators = manager.fetch_all_indicators()
# Returns dict with all required data for scoring
```

### 5. Risk Scorers (`src/scoring/*.py`)

**Purpose:** Calculate individual risk dimension scores (0-10 scale)

**Components:**
- **RecessionScorer:** Unemployment velocity, ISM PMI, yield curves
- **CreditScorer:** High-yield spreads (velocity + level), lending standards
- **ValuationScorer:** CAPE ratio, Buffett indicator, forward P/E
- **LiquidityScorer:** Fed funds rate changes, M2 velocity, VIX
- **PositioningScorer:** CFTC net positioning (contrarian indicator)

**Responsibilities:**
- Take indicator dict as input
- Calculate sub-scores for each signal
- Return overall dimension score (0-10) + breakdown

**Interface:**
```python
scorer = RecessionScorer(config)
result = scorer.calculate_score(indicators)
# Returns: {'score': 7.5, 'breakdown': {...}, 'signals': [...]}
```

### 6. Risk Aggregator (`src/scoring/aggregator.py`)

**Purpose:** Combine dimension scores into overall risk score

**Responsibilities:**
- Apply dimension weights (sum to 1.0)
- Calculate weighted average
- Track which dimensions are elevated

**Key Dependencies:**
- All scorer classes

**Interface:**
```python
aggregator = RiskAggregator(config)
overall = aggregator.calculate_overall_risk(dimension_scores)
# Returns: {'score': 7.2, 'tier': 'YELLOW', 'breakdown': {...}}
```

### 7. Alert Logic (`src/alerts/alert_logic.py`)

**Purpose:** Determine if alert should be sent based on risk level

**Responsibilities:**
- Check threshold (RED ≥8.0, YELLOW ≥6.5)
- Check velocity (rising >1.0 points in 4 weeks)
- Check multi-dimension risk (2+ dimensions ≥8.0)
- Suggest actions based on tier

**Key Dependencies:**
- History for trend analysis

**Interface:**
```python
logic = AlertLogic(config)
should_alert, tier, reason = logic.should_alert(current_score, history)
actions = logic.get_suggested_actions(tier)
```

### 8. Email Sender (`src/alerts/email_sender.py`)

**Purpose:** Send formatted email alerts

**Responsibilities:**
- Generate text and HTML email body
- Include risk breakdown, evidence, suggested actions
- Track record of historical alerts

**Key Dependencies:**
- SendGrid or SMTP
- Email templates

### 9. History Manager (`src/alerts/history_manager.py`)

**Purpose:** Store and retrieve historical risk scores

**Responsibilities:**
- Save daily risk scores to CSV
- Load historical data for trend analysis
- Track alert history

**Key Dependencies:**
- pandas for CSV operations

## Data Flow

### Daily Update Flow

```
1. Cron/Scheduler triggers daily_update.py
2. DataManager.fetch_all_indicators()
   ├─ FREDClient fetches economic data (cached)
   ├─ MarketDataClient fetches market data
   └─ Returns indicator dict
3. For each dimension:
   ├─ Scorer.calculate_score(indicators)
   └─ Returns dimension score (0-10)
4. RiskAggregator.calculate_overall_risk(dimension_scores)
   └─ Returns overall score (0-10) + tier
5. AlertLogic.should_alert(current_score, history)
   ├─ If TRUE: EmailSender.send_alert()
   └─ If FALSE: Log score only
6. HistoryManager.save_score(date, scores, tier)
```

### Backtest Flow

```
1. Load historical data (2000-2024)
2. For each date in history:
   ├─ Fetch indicators (as of that date)
   ├─ Calculate risk score
   ├─ Log if alert triggered
   └─ Compare to actual market drawdowns
3. Calculate metrics:
   ├─ True positives (alerts before drawdowns)
   ├─ False positives (alerts without drawdowns)
   ├─ Lead time (days between alert and peak)
   └─ Missed crashes
4. Generate backtest report
```

## Key Principles & Constraints

### Design Principles

1. **Data > News:** Use direct economic data, not news commentary
2. **Reproducibility:** Same inputs always produce same outputs
3. **Transparency:** All thresholds in config files, not hardcoded
4. **Graceful Degradation:** If one indicator fails, continue with available data
5. **Cache Aggressively:** Minimize API calls, respect rate limits
6. **Velocity > Levels:** Rate of change is more predictive than absolute values

### Technical Constraints

- **Platform:** Python 3.9+ (tested on 3.9-3.12)
- **APIs:** Free/low-cost only (FRED, Yahoo Finance, Shiller)
- **Frequency:** Daily updates (not intraday)
- **Latency:** Can tolerate 1-2 day data lag
- **Storage:** Local CSV files for history
- **Alert Rate:** 2-5 alerts per year (high threshold)

### Self-Imposed Rules

- **No Look-Ahead Bias:** Only use data available at calculation time
- **No Overfitting:** Thresholds based on economic theory, not curve-fitted
- **Document All Decisions:** Major methodology changes go in /docs/decisions/
- **Backtest Before Deploy:** Validate all changes against historical data
- **Conservative Thresholds:** Better to miss signals than flood with false alarms

## Layer Separation

### Domain Layer (Business Logic)
- Risk scoring algorithms
- Alert decision logic
- Velocity calculations
- Threshold definitions

### Infrastructure Layer (External Systems)
- FRED API client
- Yahoo Finance client
- Email delivery
- File-based caching

### Application Layer (Orchestration)
- DataManager coordinates fetching
- Aggregator combines scores
- Scripts tie everything together

### Configuration Layer (Settings)
- YAML files for thresholds
- secrets.ini for credentials
- Environment variable overrides

## Extension Points

### Adding New Indicators

1. Add series ID to `config/indicators.yaml`
2. Update relevant scorer in `src/scoring/`
3. Add tests in `tests/test_scoring.py`
4. Document in `/docs/decisions/`
5. Backtest before production

### Adding New Dimension

1. Create new scorer in `src/scoring/`
2. Update weights in `config/app.yaml` (ensure sum=1.0)
3. Update aggregator to include new dimension
4. Create component doc in `/docs/components/`
5. Create ADR explaining rationale

### Changing Alert Thresholds

1. Backtest new thresholds against historical data
2. Document results in `/docs/BACKTESTING_RESULTS.md`
3. Update `config/app.yaml`
4. Create ADR with rationale

## Security Considerations

- **API Keys:** Stored in secrets.ini (gitignored)
- **Email Credentials:** Stored in secrets.ini
- **No PII:** System stores only aggregate data
- **Local Storage:** All data cached locally, not cloud
- **Audit Trail:** All calculations logged

## Performance Characteristics

- **Startup Time:** <1 second (config loading)
- **Daily Update:** 30-60 seconds (with caching)
- **Cold Start:** 2-3 minutes (fetching all data)
- **Memory:** <100MB typical
- **Storage:** ~10MB per year of history

## Future Considerations

- **Scalability:** System designed for single user, not multi-tenant
- **Real-Time:** Could add intraday updates if needed
- **Dashboard:** Optional Flask app for visualization
- **Mobile:** Push notifications instead of email
- **Cloud:** Could deploy to AWS Lambda/Heroku

# Aegis Indicators Catalog

Complete reference of all indicators used in Aegis risk scoring.

## Recession Dimension (30% weight)

### Unemployment Claims Velocity
- **Source:** FRED
- **Series ID:** `ICSA` (Initial Claims)
- **Frequency:** Weekly
- **Calculation:** Year-over-year % change
- **Threshold:** >10% YoY = elevated, >20% YoY = extreme
- **Rationale:** Rapid job loss is strongest recession predictor
- **Lead Time:** 3-6 months before recession
- **Historical Range:** -30% to +200% (COVID spike)

### ISM Manufacturing PMI
- **Source:** FRED
- **Series ID:** `NAPM` or `ISM_MFG`
- **Frequency:** Monthly (first week)
- **Calculation:** Level + regime shift detection
- **Threshold:** <50 = contraction, <48 = deep contraction
- **Rationale:** Manufacturing leading indicator
- **Lead Time:** 6-12 months
- **Historical Range:** 32 (COVID 2020) to 60 (1983)

### Yield Curve (10Y-2Y)
- **Source:** FRED
- **Series ID:** `T10Y2Y`
- **Frequency:** Daily
- **Calculation:** 10-year yield minus 2-year yield
- **Threshold:** <0 = inverted (recession signal)
- **Rationale:** Most reliable recession predictor
- **Lead Time:** 12-18 months
- **Historical Range:** -1.0% to +3.0%

### Yield Curve (10Y-3M)
- **Source:** FRED
- **Series ID:** `T10Y3M`
- **Frequency:** Daily
- **Calculation:** 10-year yield minus 3-month T-bill
- **Threshold:** <0 = inverted
- **Rationale:** Confirmation signal for 10Y-2Y
- **Lead Time:** 12-18 months
- **Historical Range:** -0.5% to +4.0%

### Consumer Sentiment (Optional)
- **Source:** FRED
- **Series ID:** `UMCSENT` (University of Michigan)
- **Frequency:** Monthly
- **Calculation:** Level
- **Threshold:** <70 = pessimistic
- **Rationale:** Consumer spending drives 70% of GDP
- **Lead Time:** 3-6 months
- **Historical Range:** 52 (COVID) to 112 (1999)

---

## Credit Dimension (25% weight)

### High-Yield Spread
- **Source:** FRED
- **Series ID:** `BAMLH0A0HYM2` (ICE BofA High Yield OAS)
- **Frequency:** Daily
- **Calculation:** 70% velocity (20-day rate of change) + 30% level
- **Threshold:**
  - Level: >600 bps = stress, >900 bps = crisis
  - Velocity: >10% widening in 20 days = rapid deterioration
- **Rationale:** Primary credit stress indicator
- **Lead Time:** Weeks to months
- **Historical Range:** 250 bps (2007) to 2200 bps (2008 GFC)

### Investment-Grade BBB Spread
- **Source:** FRED
- **Series ID:** `BAMLC0A4CBBB` (ICE BofA BBB OAS)
- **Frequency:** Daily
- **Calculation:** Level
- **Threshold:** >200 bps = elevated, >300 bps = stress
- **Rationale:** Investment-grade stress = serious risk
- **Lead Time:** Weeks
- **Historical Range:** 100 bps to 500 bps

### TED Spread
- **Source:** FRED
- **Series ID:** `TEDRATE` (3M LIBOR - 3M T-bill)
- **Frequency:** Daily
- **Calculation:** Level
- **Threshold:** >50 bps = elevated, >100 bps = interbank stress
- **Rationale:** Interbank funding stress indicator
- **Lead Time:** Days to weeks
- **Historical Range:** 10 bps to 450 bps (2008)

### Bank Lending Standards
- **Source:** FRED
- **Series ID:** `DRTSCIS` (Senior Loan Officer Survey)
- **Frequency:** Quarterly
- **Calculation:** Net % tightening
- **Threshold:** >20% net tightening = restrictive
- **Rationale:** Credit availability shrinking
- **Lead Time:** 3-6 months
- **Historical Range:** -30% (easing) to +70% (tightening)

---

## Valuation Dimension (20% weight)

### Shiller CAPE Ratio
- **Source:** Robert Shiller (Yale)
- **URL:** http://www.econ.yale.edu/~shiller/data.htm
- **Frequency:** Monthly
- **Calculation:** P/E using 10-year average real earnings
- **Threshold:** >25 = elevated, >30 = bubble territory
- **Rationale:** Long-term valuation measure
- **Lead Time:** Months to years (slow-moving)
- **Historical Range:** 5 (1921) to 44 (1999 dot-com)

### Buffett Indicator
- **Source:** FRED (calculated)
- **Series IDs:** `WILL5000IND` (Wilshire 5000) / `GDP`
- **Frequency:** Quarterly
- **Calculation:** Total market cap / GDP
- **Threshold:** >120% = elevated, >150% = extreme
- **Rationale:** Warren Buffett's preferred valuation metric
- **Lead Time:** Months to years
- **Historical Range:** 40% (1982) to 215% (2021)

### S&P 500 Forward P/E
- **Source:** Yahoo Finance / S&P
- **Calculation:** Price / Next 12-month EPS estimates
- **Threshold:** >20 = elevated, >24 = expensive
- **Rationale:** Forward-looking, less volatile than trailing
- **Lead Time:** Months
- **Historical Range:** 10 (2009) to 28 (1999)

---

## Liquidity Dimension (15% weight)

### Fed Funds Rate Velocity
- **Source:** FRED
- **Series ID:** `DFF` (Effective Federal Funds Rate)
- **Frequency:** Daily
- **Calculation:** 6-month change
- **Threshold:** >200 bps in 6 months = aggressive tightening
- **Rationale:** Rapid rate hikes drain liquidity
- **Lead Time:** 3-9 months
- **Historical Range:** 0% to 20% (1980s)

### M2 Money Supply Velocity
- **Source:** FRED
- **Series ID:** `M2SL`
- **Frequency:** Weekly
- **Calculation:** Year-over-year % change
- **Threshold:** <0% YoY = contracting money supply
- **Rationale:** Money supply contraction = tight conditions
- **Lead Time:** 3-6 months
- **Historical Range:** -5% to +25% YoY

### VIX (CBOE Volatility Index)
- **Source:** Yahoo Finance
- **Ticker:** `^VIX`
- **Frequency:** Real-time (use daily close)
- **Calculation:** Level (10-day moving average to smooth)
- **Threshold:** >25 = elevated, >35 = panic
- **Rationale:** Volatility = liquidity premium
- **Lead Time:** Concurrent to slightly leading
- **Historical Range:** 9 (2017-18) to 82 (2020 COVID)

### Margin Debt (Optional)
- **Source:** FINRA
- **Frequency:** Monthly
- **Calculation:** Year-over-year % change
- **Threshold:** Sharp decline = forced deleveraging
- **Rationale:** Margin calls = forced selling
- **Lead Time:** Concurrent
- **Historical Range:** -20% to +40% YoY

---

## Positioning Dimension (10% weight)

### CFTC S&P 500 Net Positioning
- **Source:** CFTC Commitments of Traders
- **Report:** Legacy Futures (S&P 500)
- **Frequency:** Weekly (Friday release)
- **Calculation:** Net long as percentile of 2-year history
- **Threshold:** >80th percentile = crowded long (contrarian bearish)
- **Rationale:** Extreme positioning amplifies moves
- **Lead Time:** 1-4 weeks
- **Historical Range:** Varies (use percentiles)

### CFTC Treasury Net Positioning
- **Source:** CFTC
- **Report:** 10-Year Treasury Note futures
- **Frequency:** Weekly
- **Calculation:** Net short as percentile
- **Threshold:** >80th percentile = crowded short (squeeze risk)
- **Rationale:** Treasury positioning affects risk appetite
- **Lead Time:** 1-4 weeks

### VIX Futures Positioning (Future)
- **Source:** CFTC
- **Report:** VIX futures
- **Frequency:** Weekly
- **Calculation:** Short interest
- **Threshold:** High short interest = complacency
- **Rationale:** VIX shorts = betting on calm (complacency)
- **Lead Time:** 1-2 weeks

---

## Data Quality Notes

### Update Frequencies
- **Daily:** Yield curves, credit spreads, VIX, fed funds
- **Weekly:** Unemployment claims, M2, CFTC positioning
- **Monthly:** ISM PMI, consumer sentiment, margin debt
- **Quarterly:** GDP, bank lending standards

### Typical Lags
- **0 days:** Market data (VIX, spreads, yields)
- **1-2 days:** FRED economic data
- **1 week:** CFTC positioning
- **2 weeks:** M2, some employment data
- **1 month:** GDP, quarterly data

### Data Revisions
- **Minimal:** Market data (yields, spreads)
- **Moderate:** Employment data (revised 2-3 times)
- **Significant:** GDP (revised for years)

**Backtesting Note:** Use "as reported" data or FRED real-time datasets to avoid look-ahead bias.

---

## Indicator Substitutions

If primary indicator unavailable:

| Primary | Backup Options |
|---------|---------------|
| ICSA (unemployment claims) | U-6 unemployment rate, continuing claims |
| ISM PMI | Chicago PMI, Markit PMI |
| HY spreads (BAMLH0A0HYM2) | HYG ETF spread vs treasuries |
| Shiller CAPE | Trailing P/E, price/sales |
| VIX | MOVE index (bond volatility) |

---

## Adding New Indicators

**Process:**
1. Document in this catalog
2. Add to `config/indicators.yaml`
3. Update relevant scorer
4. Add tests
5. Backtest to validate
6. Create ADR explaining rationale

**Criteria for inclusion:**
- Free/low-cost data
- Historical data >10 years
- Reliable update schedule
- Economically meaningful
- Improves backtest results

---

**Last Updated:** 2025-01-08
**Next Review:** After backtesting, quarterly thereafter

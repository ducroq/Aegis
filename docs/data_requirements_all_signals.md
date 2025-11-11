# Comprehensive Data Requirements for All Signals

**Purpose**: Add ALL missing data fields at once, then run ONE FINAL backfill before implementing remaining signals.

---

## Current Status

### Signals Implemented (1-3)
✅ **Signal #1: Valuation Warning** - Data complete
✅ **Signal #2: Double Inversion** - Data complete
✅ **Signal #3: Real Interest Rates** - Data INCOMPLETE (missing CPI - being backfilled now)

### Signals Planned (4-7)
- Signal #4: Earnings Recession
- Signal #5: Housing Bubble
- Signal #6: Market Breadth (skip - too hard to get data)
- Signal #7: Margin Debt Peak

---

## Data Gap Analysis

### Currently Have (27 columns)

**Recession** (6):
- unemployment_claims, unemployment_claims_velocity_yoy
- ism_pmi
- yield_curve_10y2y, yield_curve_10y3m
- consumer_sentiment

**Credit** (5):
- hy_spread, hy_spread_velocity_20d
- ig_spread_bbb
- ted_spread
- bank_lending_standards

**Valuation** (5):
- sp500_price, sp500_forward_pe
- shiller_cape
- sp500_market_cap
- gdp

**Liquidity** (5):
- fed_funds_rate, fed_funds_velocity_6m
- m2_money_supply, m2_velocity_yoy
- vix
- margin_debt (NULL - no data source yet)

**Positioning** (4):
- sp500_net_speculative, treasury_net_speculative, vix_net_speculative (all NULL - CFTC not implemented)
- vix_proxy

---

## Missing Data for Signal #3 (Real Rates)

### ❌ CPI Inflation (BEING ADDED NOW)
- **FRED Series**: CPIAUCSL
- **Calculation**: YoY % change
- **Fields to add**:
  - `liquidity_cpi_inflation` (level)
  - `liquidity_cpi_inflation_yoy` (YoY %)
- **Status**: Currently being backfilled (2020-2024)

---

## Missing Data for Signal #4 (Earnings Recession)

### ❌ S&P 500 Forward Earnings
- **Current**: Have `valuation_sp500_forward_pe` (forward P/E ratio)
- **Need**: Forward EPS (earnings per share)
- **Calculation**: `Forward EPS = SP500 Price / Forward P/E`
- **Can derive from existing data**: YES!
- **New fields needed**: NONE (can calculate from existing)

**Signal Logic**:
```python
forward_eps = sp500_price / sp500_forward_pe
eps_6m_change = (forward_eps - forward_eps_6m_ago) / forward_eps_6m_ago

if eps_6m_change < -0.10:  # 10% decline in forward earnings
    return EARNINGS_RECESSION_WARNING
```

**Status**: ✅ NO NEW DATA NEEDED

---

## Missing Data for Signal #5 (Housing Bubble)

### ❌ New Home Sales
- **FRED Series**: HSN1F (New One Family Houses Sold)
- **Units**: Thousands, monthly
- **Field**: `valuation_new_home_sales`

### ❌ Housing Affordability Index
- **Option 1**: FRED MORTGAGE30US (30-Year Fixed Rate Mortgage)
- **Option 2**: Calculate affordability = (Median Income / Median Home Price) / Mortgage Rate
- **Simpler approach**: Just use mortgage rates as proxy
- **Field**: `valuation_mortgage_rate_30y`

### ❌ Median Home Price (Optional)
- **FRED Series**: MSPUS (Median Sales Price of Houses Sold)
- **Units**: Dollars
- **Field**: `valuation_median_home_price`

**Signal Logic**:
```python
home_sales_6m_change = (home_sales - home_sales_6m_ago) / home_sales_6m_ago
mortgage_rate = mortgage_rate_30y

if home_sales_6m_change < -0.20 and mortgage_rate > 6.5:
    # Declining sales + high rates = housing stress
    return HOUSING_BUBBLE_WARNING
```

**New Fields Needed**:
1. `valuation_new_home_sales` (HSN1F)
2. `valuation_mortgage_rate_30y` (MORTGAGE30US)
3. `valuation_median_home_price` (MSPUS) - optional

---

## Missing Data for Signal #7 (Margin Debt Peak)

### ❌ Margin Debt
- **Current**: Have `liquidity_margin_debt` but it's NULL (no source)
- **Source**: FINRA publishes monthly margin debt data
- **Problem**: Not available via FRED API
- **Alternative**: Manual CSV download from FINRA
- **Field**: `liquidity_margin_debt` (already exists, need to populate)

**Workaround**:
- FINRA data requires scraping or manual update
- For now, SKIP this signal or use placeholder

**Status**: ⚠️ DIFFICULT - requires non-FRED data source

---

## Signal #6 (Market Breadth) - SKIP

**Reason**: Requires individual stock data (% of S&P 500 above 200-day MA)
- Yahoo Finance doesn't provide this aggregated metric
- Would need to fetch 500 individual stocks daily = too expensive
- **Decision**: SKIP for now

---

## Final Data Requirements Summary

### Must Add Immediately (Before Final Backfill)

**FOR SIGNAL #3 (Real Rates)** - In Progress:
- ✅ `liquidity_cpi_inflation` (CPIAUCSL)
- ✅ `liquidity_cpi_inflation_yoy` (derived)

**FOR SIGNAL #5 (Housing Bubble)**:
- ❌ `valuation_new_home_sales` (HSN1F)
- ❌ `valuation_mortgage_rate_30y` (MORTGAGE30US)
- ❌ `valuation_median_home_price` (MSPUS) - optional

**FOR SIGNAL #4 (Earnings Recession)**:
- ✅ NO NEW DATA (can derive from existing)

**FOR SIGNAL #7 (Margin Debt)**:
- ⚠️ SKIP (requires FINRA data, not easily available)

**FOR SIGNAL #6 (Market Breadth)**:
- ⚠️ SKIP (too expensive to get)

---

## Implementation Plan

### Step 1: Add Missing FRED Series to DataManager

Add to `_fetch_valuation_indicators()`:
```python
# Housing indicators
'new_home_sales': self.fred_client.get_latest_value('HSN1F'),
'mortgage_rate_30y': self.fred_client.get_latest_value('MORTGAGE30US'),
'median_home_price': self.fred_client.get_latest_value('MSPUS'),  # Optional
```

Also add to `_fetch_valuation_indicators_as_of()`:
```python
'new_home_sales': self.fred_client.get_value_as_of('HSN1F', as_of_date),
'mortgage_rate_30y': self.fred_client.get_value_as_of('MORTGAGE30US', as_of_date),
'median_home_price': self.fred_client.get_value_as_of('MSPUS', as_of_date),
```

### Step 2: Run ONE FINAL Backfill

```bash
# Delete old data
rm data/history/*.csv

# Full backfill with ALL data (2000-2024)
python scripts/backfill_history.py --start-date 2000-01-01 --end-date 2024-12-31 --frequency monthly
```

This will take ~60 minutes for 300 months but will be the LAST TIME.

### Step 3: Implement Signals from Harvested Data

Once backfill completes, implement in order:

1. **Signal #4 (Earnings Recession)** - Easy, no new data needed
2. **Signal #5 (Housing Bubble)** - Use new housing data
3. **Validate Signal #3 (Real Rates)** - Now has CPI data

---

## Expected CSV Columns After Final Backfill

Total: 30 columns (27 current + 3 new housing)

```
1. date
2-7. recession_* (6 columns - unchanged)
8-12. credit_* (5 columns - unchanged)
13-17. valuation_sp500_price, sp500_forward_pe, shiller_cape, sp500_market_cap, gdp
18. valuation_new_home_sales (NEW)
19. valuation_mortgage_rate_30y (NEW)
20. valuation_median_home_price (NEW - optional)
21-25. liquidity_fed_funds_rate, fed_funds_velocity_6m, cpi_inflation, cpi_inflation_yoy (NEW), m2_money_supply, m2_velocity_yoy, vix, margin_debt
26-30. positioning_* (4 columns - still NULL, CFTC not implemented)
```

---

## Summary

**Add these 3 fields, then ONE FINAL backfill**:
1. ✅ `liquidity_cpi_inflation_yoy` (in progress)
2. ❌ `valuation_new_home_sales`
3. ❌ `valuation_mortgage_rate_30y`

Then we can rapidly implement:
- Signal #3 validation (real rates)
- Signal #4 (earnings recession)
- Signal #5 (housing bubble)

= **5 signals total** from one comprehensive dataset!

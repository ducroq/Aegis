# TODO: Complete Signal Implementation

## Signal #7: Dollar Liquidity Stress (COMPLETED ✅)

### Completed:
- ✅ Research completed - identified FRED series
- ✅ Added data sources to `src/data/data_manager.py`:
  - `DTWEXBGS` - Trade-Weighted Dollar Index
  - `ROWSLAQ027S` - Fed Foreign Currency Swap Lines
- ✅ Added `_check_dollar_liquidity_stress()` method to `src/scoring/aggregator.py`
- ✅ Integrated check into `calculate_overall_risk()` method
- ✅ Created `scripts/test_dollar_liquidity_signal.py` backtest script
- ✅ Validated against historical data:
  - ✅ 2008 Financial Crisis: 3 warnings (Oct-Dec 2008) - dollar surge +6.5% to +14.9%
  - ✅ 2011 Euro Crisis: 2 warnings (Oct-Nov 2011) - bonus detection
  - ⚠️ 2020 COVID: Not detected (monthly data too coarse for sub-month spike)

### Backtest Results:
- **Total warnings (2006-2024)**: 5 warnings
- **2008 Lehman Crisis**: ✅ Detected Oct-Dec 2008 (dollar +14.9% in 3 months + elevated swap lines)
- **2011 European Crisis**: ✅ Detected Oct-Nov 2011 (dollar +6.5% + elevated swap lines)
- **False positives**: None in normal periods
- **Signal quality**: HIGH - catches severe dollar funding crises

### Notes:
- Signal works well for detecting sustained dollar surges (3+ months)
- Monthly data granularity misses intra-month spikes (2020 COVID was 8% in weeks)
- For early warning, consider daily/weekly data in future enhancement
- Data only available from 2006+ (when DTWEXBGS series begins)

### Previously: Remaining Work (NOW COMPLETED):

#### 1. Add Signal Logic to Aggregator (`src/scoring/aggregator.py`)

Add new method after `_check_housing_bubble()`:

```python
def _check_dollar_liquidity_stress(
    self,
    liquidity_data: Dict[str, Any],
    raw_indicators: 'pd.DataFrame' = None
) -> Dict[str, Any]:
    """
    Check for dollar liquidity stress (global dollar funding shortage).

    Detects rapid dollar strengthening combined with Fed activating swap lines,
    indicating global dollar shortage/funding stress.

    Historical examples: 2008 financial crisis, March 2020 COVID panic.
    """
    dollar_index = liquidity_data.get('dollar_index')
    swap_lines = liquidity_data.get('fed_swap_lines')

    # Need historical data to calculate 3-month change
    if dollar_index is not None and raw_indicators is not None and len(raw_indicators) >= 4:
        try:
            # Get dollar index from 3 months ago
            three_months_ago = raw_indicators.iloc[-4]
            dollar_3m_ago = three_months_ago.get('liquidity_dollar_index')

            if dollar_3m_ago and dollar_3m_ago > 0:
                dollar_change_3m = (dollar_index - dollar_3m_ago) / dollar_3m_ago

                # Also check if swap lines elevated (sign of stress)
                # Calculate historical percentile if we have enough data
                swap_lines_elevated = False
                if len(raw_indicators) >= 24 and swap_lines is not None:
                    # Get past 24 months of swap line data
                    historical_swaps = []
                    for i in range(min(24, len(raw_indicators))):
                        val = raw_indicators.iloc[-(i+1)].get('liquidity_fed_swap_lines')
                        if val is not None:
                            historical_swaps.append(val)

                    if len(historical_swaps) > 0:
                        percentile_90 = sorted(historical_swaps)[int(len(historical_swaps) * 0.9)]
                        swap_lines_elevated = (swap_lines > percentile_90)

                # Trigger conditions
                # HIGH: 5%+ dollar spike + Fed swap lines activated
                if dollar_change_3m > 0.05 and swap_lines_elevated:
                    message = (
                        f"DOLLAR LIQUIDITY STRESS: Severe global dollar shortage. "
                        f"Dollar index surged +{dollar_change_3m*100:.1f}% in 3 months "
                        f"(from {dollar_3m_ago:.2f} to {dollar_index:.2f}) AND Fed activating "
                        f"emergency swap lines (${swap_lines:.1f}B outstanding). "
                        f"Historical precedent: 2008 financial crisis (dollar spike + Lehman), "
                        f"March 2020 COVID panic (8% dollar surge in 2 weeks). "
                        f"Global funding stress can cascade to EM debt crises, foreign bank failures."
                    )
                    return {
                        'active': True,
                        'level': 'HIGH',
                        'message': message,
                        'dollar_change_3m_pct': dollar_change_3m * 100,
                        'current_dollar_index': dollar_index,
                        'dollar_3m_ago': dollar_3m_ago,
                        'swap_lines_outstanding': swap_lines,
                        'swap_lines_elevated': swap_lines_elevated
                    }

                # HIGH: 8%+ dollar spike alone (extreme panic)
                elif dollar_change_3m > 0.08:
                    message = (
                        f"DOLLAR LIQUIDITY STRESS: Extreme dollar surge signals global funding panic. "
                        f"Dollar index spiked +{dollar_change_3m*100:.1f}% in 3 months "
                        f"(from {dollar_3m_ago:.2f} to {dollar_index:.2f}). "
                        f"Rapid dollar strength indicates offshore dollar shortage, "
                        f"forcing EM/foreign banks to scramble for USD funding. "
                        f"Can trigger cascade of margin calls, forced USD asset sales."
                    )
                    return {
                        'active': True,
                        'level': 'HIGH',
                        'message': message,
                        'dollar_change_3m_pct': dollar_change_3m * 100,
                        'current_dollar_index': dollar_index,
                        'dollar_3m_ago': dollar_3m_ago
                    }

        except Exception as e:
            logger.error(f"Error checking dollar liquidity stress: {e}")

    return {'active': False}
```

#### 2. Add Signal Check to `calculate_overall_risk()` method

After the housing bubble check, add:

```python
# Check for dollar liquidity stress (global funding shortage)
dollar_liquidity_warning = self._check_dollar_liquidity_stress(
    data.get('liquidity', {}),
    None  # No historical data in live mode - will be populated during backtest
)
if dollar_liquidity_warning.get('active'):
    warnings.append(dollar_liquidity_warning['message'])
```

#### 3. Create Backtest Script (`scripts/test_dollar_liquidity_signal.py`)

Copy structure from `test_earnings_recession_signal.py`, test periods:
- 2008 Q3-Q4: Dollar spike during Lehman/financial crisis
- March 2020: COVID panic dollar surge
- 2022: Gradual dollar rise (should NOT trigger - too slow)

#### 4. Update Documentation (`docs/methodology.md`)

Add Signal #7 section after Signal #6.

---

## Signal #10: Retail Capitulation (NOT STARTED)

### Implementation Plan:

#### Data Source:
- **AAII Sentiment Survey**: https://www.aaii.com/sentimentsurvey/sent_results
- Weekly data, free download as CSV
- No API available - requires manual download or web scraper

#### Implementation Options:

**Option A (Manual - Recommended for MVP)**:
1. User downloads CSV from AAII website weekly
2. Save to `data/external/aaii_sentiment.csv`
3. Add helper function to read this file in `src/data/sentiment_data.py`
4. Document process in README

**Option B (Automated - Future Enhancement)**:
1. Build web scraper using BeautifulSoup/Selenium
2. Cache results locally
3. Update weekly via cron job
4. Risk: Scraper breaks if AAII changes website

#### Signal Logic:

```python
def _check_retail_capitulation(sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for extreme retail sentiment (contrarian indicator).

    Bulls < 20%: Extreme bearishness = potential bottom (CAPITULATION)
    Bulls > 60%: Extreme bullishness = potential top (EUPHORIA)
    """
    bulls_pct = sentiment_data.get('bulls_percent')

    if bulls_pct is None:
        return {'active': False}

    if bulls_pct < 20:
        return {
            'active': True,
            'level': 'HIGH',
            'signal_type': 'CAPITULATION',
            'message': f"RETAIL CAPITULATION: Extreme bearishness ({bulls_pct:.1f}% bulls). "
                      f"Historically marks bottoms when combined with oversold technicals. "
                      f"Contrarian buying opportunity when panic peaks."
        }
    elif bulls_pct > 60:
        return {
            'active': True,
            'level': 'HIGH',
            'signal_type': 'EUPHORIA',
            'message': f"RETAIL EUPHORIA: Extreme bullishness ({bulls_pct:.1f}% bulls). "
                      f"Historically precedes corrections when retail is all-in. "
                      f"Consider trimming positions as complacency peaks."
        }

    return {'active': False}
```

#### Test Periods:
- March 2009: Bulls <20% at market bottom
- January 2000: Bulls >60% at dot-com peak
- March 2020: Bulls <20% at COVID bottom
- Q4 2021: Bulls >60% before 2022 bear market

---

## Priority:

1. **Complete Signal #7** (high priority - automated, predictive)
2. **Implement Signal #10** (medium priority - requires manual data updates)

---

## Notes:

- Signal #7 data (DTWEXBGS) only goes back to 2006, so pre-2006 backtests will have limited data
- Signal #10 requires user to manually download AAII data weekly (or build scraper)
- Both signals are documented in research phase, ready for implementation

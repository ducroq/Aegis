# External Data Sources

This folder contains manually curated data from external sources that are not available via free APIs.

## Files

### `cboe_equity_putcall_historical.csv`
**Source:** CBOE (Chicago Board Options Exchange)
**URL:** https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv
**Description:** Daily equity put/call ratio - measures retail investor sentiment
**Date Range:** 2006-11-01 to 2019-10-04 (3,253 data points)
**Update Frequency:** Historical only (CBOE stopped updating in 2019)
**Status:** ⚠️ NOT USED - Missing 2020-2025 data (5-year gap)

**Columns:**
- `Date` - Trading date
- `PutCallRatio` - Put volume / Call volume ratio

**Interpretation:**
- **Low ratio (<0.6):** Extreme greed/bullish sentiment → Contrarian SELL signal (risk)
- **Normal (0.6-0.7):** Neutral sentiment
- **High ratio (>0.8):** Extreme fear/bearish sentiment → Contrarian BUY signal (opportunity)

**Why Not Used:**
- Data stops in 2019, missing COVID crash (2020), 2022 bear market, 2023-2025 recovery
- VIX (via FRED) already captures similar sentiment and is current
- Not worth the 5-year data gap for marginal improvement

---

### `aaii_sentiment.csv`
**Source:** AAII (American Association of Individual Investors)
**Description:** Weekly retail investor sentiment survey
**Date Range:** 2024-01-07 to 2024-03-10 (10 weeks only)
**Update Frequency:** Manual upload required
**Status:** ⚠️ NOT USED - Insufficient historical data

**Columns:**
- `Date` - Survey week
- `Bullish%` - % of respondents bullish
- `Neutral%` - % of respondents neutral
- `Bearish%` - % of respondents bearish

**Why Not Used:**
- Only 10 weeks of data (insufficient for backtesting)
- AAII full historical data requires paid membership (~$29/year)
- Consumer Sentiment (UMCSENT from FRED) provides similar insight for free

---

## Future Considerations

**If you want to add retail sentiment indicators:**

1. **Subscribe to AAII** (~$29/year) for complete historical survey data (1987-present)
2. **Web scraping** (check terms of service first)
3. **Alternative free sources:**
   - University of Michigan Consumer Sentiment (already using via FRED)
   - CNN Fear & Greed Index (daily, but limited history)

**Current sentiment coverage is adequate:**
- Institutional: CFTC positioning
- Market fear: VIX
- Consumer: UMCSENT

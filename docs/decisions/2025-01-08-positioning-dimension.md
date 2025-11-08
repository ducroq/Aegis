# Add CFTC Positioning as 5th Risk Dimension

**Date:** 2025-01-08
**Status:** Accepted

## Context

Initial Aegis design had 4 risk dimensions: Recession, Credit, Valuation, Liquidity. Should we add a 5th dimension tracking investor positioning and sentiment?

## Decision

**Yes - Add Positioning as 5th dimension with 10% weight**

**Data sources:**
- CFTC Commitments of Traders (S&P 500, Treasury futures)
- VIX futures positioning
- Put/call ratios (future enhancement)

## Rationale

### 1. Crowded Trades Amplify Moves

**When everyone is positioned the same way:**
- Forced unwinding creates cascades
- "No buyers left" at extremes
- Herding behavior amplifies volatility

**Historical examples:**
- **2008:** Massive long equity positioning before crash
- **2020:** Record short VIX positioning = complacency
- **2022:** Extreme long positioning into year-end 2021

### 2. Contrarian Signal

**Extreme bullish positioning = Risk:**
- When speculators are max long, who's left to buy?
- Any negative catalyst triggers selling cascade
- "Be fearful when others are greedy" (Buffett)

**Extreme bearish positioning = Opportunity:**
- Short squeezes can be violent
- Pessimism often overdone
- Provides support during selloffs

### 3. Complements Other Dimensions

**Positioning interacts with fundamentals:**
- High valuations + crowded longs = explosive downside
- Credit stress + forced deleveraging = systemic risk
- Recession + panic = overshoot

**But positioning is independent signal:**
- Can be extreme even when fundamentals normal
- Provides sentiment layer on top of quant

### 4. Data Availability

**CFTC data is:**
- Free and public
- Updated weekly (Fridays)
- Historical data back to 1990s
- Reliable and auditable

## Weight: 10% (Lowest)

**Why only 10%?**

1. **Noisier than fundamentals:**
   - Positioning can stay extreme for weeks/months
   - More false signals than recession/credit
   - Short-term traders vs long-term fundamentals

2. **Lagging indicator:**
   - CFTC data has 1-week lag
   - By time it's extreme, may be too late
   - Best as confirmation, not primary

3. **Less historical validation:**
   - CFTC data quality varies pre-2000
   - Fewer crashes to validate against
   - Newer indicator than yield curve, credit spreads

4. **Complements, doesn't lead:**
   - Works best with other dimensions elevated
   - Amplifier more than leading indicator
   - Incremental signal, not game-changer

## Implementation

### Positioning Scorer

```python
def calculate_score(self, indicators):
    score = 0.0

    # S&P 500 net positioning (percentile basis)
    sp_positioning_pct = indicators.get('cftc_sp500_net_long_percentile')

    if sp_positioning_pct > 90:  # 90th percentile = extreme bullish
        score += 4.0  # Very crowded long
    elif sp_positioning_pct > 75:  # 75th percentile
        score += 2.0  # Elevated bullishness
    elif sp_positioning_pct < 25:  # 25th percentile = extreme bearish
        score -= 2.0  # Extreme pessimism (subtract = lowers risk)

    # VIX futures positioning (complacency measure)
    vix_short_interest = indicators.get('vix_short_interest')
    if vix_short_interest > 80:  # 80th percentile
        score += 3.0  # Extreme complacency

    # Treasury positioning (crowded shorts = squeeze risk)
    treasury_net_short_pct = indicators.get('cftc_treasury_net_short_percentile')
    if treasury_net_short_pct > 80:
        score += 3.0  # Crowded treasury short

    return min(score, 10.0)
```

### Percentile Approach

Use historical percentiles instead of absolute levels:
- 90th percentile = extreme (occurs ~10% of time)
- 75th percentile = elevated
- 25th-75th = normal range
- 10th percentile = extreme opposite

**Why percentiles?**
- Context-aware (what's "extreme" changes over time)
- Normalizes across different instruments
- More stable than absolute thresholds

## Consequences

### Positive

✅ **Completes Picture:** Captures sentiment layer
✅ **Contrarian Value:** Identifies crowded trades
✅ **Amplification Signal:** Confirms other dimensions
✅ **Free Data:** CFTC reports are public

### Negative

⚠️ **Noisier:** More false signals than fundamentals
⚠️ **Complexity:** 5 dimensions harder to track than 4
⚠️ **Lag:** Weekly data with 1-week delay
⚠️ **Limited History:** Less validated than yield curve

### Neutral

ℹ️ **Low Weight (10%):** Mitigates noise issue
ℹ️ **Optional:** Could make this dimension toggle-able
ℹ️ **Room to Grow:** Can add more sentiment indicators

## Alternatives Considered

### Alternative 1: Merge with Liquidity ❌

**Why Rejected:**
- Positioning is conceptually different from liquidity
- Would dilute both signals
- Better as separate dimension

### Alternative 2: No 5th Dimension ❌

**Why Rejected:**
- Misses valuable sentiment signal
- Historical crashes showed positioning extremes
- Low weight (10%) makes it non-intrusive

### Alternative 3: Higher Weight (15-20%) ❌

**Why Rejected:**
- Too noisy for higher weight
- Not validated enough for larger role
- Can increase if backtest proves valuable

## Backtest Validation

**Will test:**
1. With vs without positioning dimension
2. 5% vs 10% vs 15% weight
3. Different positioning indicators (CFTC, put/call, etc.)
4. Percentile thresholds (80th vs 90th)

**Success Criteria:**
- Improves overall F1 score by >5%
- Catches at least 1 crash earlier
- Doesn't add >2 false positives per year

## Future Enhancements

**Additional positioning data:**
- [ ] Put/call ratios (CBOE)
- [ ] Individual investor sentiment surveys
- [ ] Options skew (risk reversal)
- [ ] Fund flow data (equity vs bond inflows)
- [ ] Margin debt levels

**Refinements:**
- [ ] Multi-factor positioning model
- [ ] Machine learning to find optimal percentiles
- [ ] Regime-specific thresholds

## References

- CFTC Commitments of Traders Reports
- "Crowded Trades and Tail Risk" (2018, BIS)
- "Sentiment Indicators and Market Crashes" (NBER 2016)

---

**Last Updated:** 2025-01-08
**Next Review:** After backtesting completion

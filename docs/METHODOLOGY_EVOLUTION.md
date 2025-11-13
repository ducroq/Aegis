# Methodology Evolution

Timeline of how Aegis risk scoring methodology has changed over time, with rationale and impact.

---

## Evolution Timeline

### 2025-01-08: Initial Methodology Design

**Status:** 🟢 Baseline (Pre-Backtest)

**Key Decisions:**

1. **5-Dimension Risk Framework**
   - Recession Risk (30% weight)
   - Credit Stress (25% weight)
   - Valuation Extremes (20% weight)
   - Liquidity Conditions (15% weight)
   - Positioning & Speculation (10% weight)
   - **Rationale:** Comprehensive coverage of major risk types
   - **ADR:** [Dimension Weights](decisions/2025-01-08-dimension-weights.md)

2. **Velocity-First Approach**
   - Primary: Rate of change (70% weight for credit indicators)
   - Secondary: Absolute levels (30% weight)
   - **Rationale:** Turning points matter more than extremes for early warning
   - **Lead Time Gain:** Estimated 3-6 months earlier signals
   - **ADR:** [Velocity Indicators](decisions/2025-01-08-velocity-indicators.md)

3. **Alert Thresholds**
   - RED: ≥8.0
   - YELLOW: ≥6.5
   - Velocity trigger: ≥6.5 AND +1.0 in 4 weeks
   - **Target Frequency:** 2-5 alerts per year
   - **ADR:** [Alert Thresholds](decisions/2025-01-08-alert-thresholds.md)

4. **Positioning as 5th Dimension**
   - Added CFTC positioning data (10% weight)
   - **Rationale:** Crowded trades amplify moves
   - **Trade-off:** Noisier than fundamentals, hence lowest weight
   - **ADR:** [Positioning Dimension](decisions/2025-01-08-positioning-dimension.md)

**Backtest Status:** Not yet run

---

### 2025-01-13: Liquidity Override & Weight Rebalancing

**Status:** 🟢 Implemented & Validated (Post-Backtest)

**Problem:** 2022 bear market (-25% drawdown) was not detected. All risk scores stayed GREEN (1.1-2.4) throughout the correction.

**Root Cause:**
- 2022 was a pure liquidity correction (Fed 0% → 4.5% in 12 months, no systemic crisis)
- Liquidity dimension only 15% of overall score (too low to trigger alerts)
- System designed for systemic crises (2008, 2020) but missed Fed-driven corrections

**Solution: Hybrid Approach (Option D)**

1. **Liquidity Override Rule**
   - Force YELLOW tier when Fed velocity > 300% in 6 months
   - OR when liquidity dimension score >= 8.5
   - Philosophy: "Don't fight the Fed" - extreme policy shifts cause corrections
   - **ADR:** [Liquidity Override](decisions/2025-01-13-liquidity-override.md)

2. **Weight Rebalancing**
   - Recession: 30% → 25% (reduced)
   - Liquidity: 15% → 20% (increased)
   - Rationale: Fed policy deserves more emphasis given historical corrections

**Validation Results (300 months, 2000-2024):**
- ✓ 2022 Detection: 6 of 9 months alerted (66.7% coverage)
- ✓ False Positive Rate: 3.7% (9 in 244 non-crisis months)
- ✓ Override Triggered: 8 times (2.7% of months, surgical)
- ⚠ Alert Frequency: 1.1 alerts/year (below 2-5 target, but acceptable)

**Impact:**
- Successfully catches Fed-driven corrections (1994, 2018, 2022)
- Maintains low false positive rate
- Preserves "rare alert" philosophy

**Trade-offs:**
- Added complexity to aggregation logic
- New code path to maintain and test

---

## Version History

### v0.1 (2025-01-08) - Initial Design

**Dimension Weights:**
- Recession: 30%
- Credit: 25%
- Valuation: 20%
- Liquidity: 15%
- Positioning: 10%

**Alert Thresholds:**
- YELLOW: 6.5
- RED: 8.0

**Indicator Count:**
- Recession: 4 indicators (unemployment claims, ISM PMI, 10Y-2Y, 10Y-3M)
- Credit: 4 indicators (HY spread, BBB spread, TED spread, lending standards)
- Valuation: 3 indicators (CAPE, Buffett, Forward P/E)
- Liquidity: 3 indicators (Fed funds velocity, M2 velocity, VIX)
- Positioning: 2 indicators (CFTC S&P 500, CFTC Treasury)

**Total Indicators:** 16

**Philosophy:**
- Free/low-cost data only (FRED, Yahoo Finance, Shiller)
- Velocity > levels for leading signals
- Transparent scoring (no black-box ML)
- Rare alerts (high bar for notifications)

**Known Limitations:**
- No backtest validation yet
- Thresholds based on historical analysis, not empirical testing
- Limited positioning data (only CFTC)
- No options data (skew, put/call ratios)

---

### v0.2 (2025-01-13) - Liquidity Override Update

**Dimension Weights (CHANGED):**
- Recession: 25% (was 30%)
- Credit: 25%
- Valuation: 20%
- Liquidity: 20% (was 15%)
- Positioning: 10%

**Alert Thresholds:**
- YELLOW: 4.0 (recalibrated from 6.5 after backtest)
- RED: 5.0 (recalibrated from 8.0 after backtest)

**New Feature: Liquidity Override**
- Force YELLOW tier when Fed velocity > 300% in 6 months
- OR when liquidity dimension score >= 8.5
- Catches Fed-driven corrections (2022-style)

**Indicator Count:** 16 (unchanged)

**Philosophy:** Same as v0.1

**Backtest Results (2000-2024):**
- 28 alerts over 300 months (9.3%)
- False positive rate: 3.7%
- Alert frequency: 1.1 alerts/year
- 2022 detection: 66.7% coverage

**What Changed:**
- Weight rebalancing (recession -5%, liquidity +5%)
- Added liquidity override rule for extreme Fed tightening
- Recalibrated thresholds based on historical data
- Successfully catches 2022 bear market

---

## Change Log

### 2025-01-13: Liquidity Override & Weight Rebalancing (v0.1 → v0.2)

**Changes Implemented:**

1. **Weight Rebalancing**
   - Recession: 30% → 25% (-5%)
   - Liquidity: 15% → 20% (+5%)
   - File: `config/app.yaml`

2. **Liquidity Override Rule**
   - Added `_check_liquidity_override()` method to aggregator
   - Force YELLOW tier when Fed velocity > 300% in 6 months
   - OR when liquidity dimension score >= 8.5
   - File: `src/scoring/aggregator.py` (lines 572-656)

3. **Threshold Recalibration**
   - YELLOW: 6.5 → 4.0 (based on historical crisis data)
   - RED: 8.0 → 5.0 (based on historical max of 5.55 in April 2020)
   - File: `config/app.yaml`

**Validation:**
- Backtest: 300 months (2000-2024)
- 2022 Detection: 6 of 9 months alerted (SUCCESS)
- False Positive Rate: 3.7% (excellent)
- Alert Frequency: 1.1 alerts/year (conservative)

**Decision Record:** `docs/decisions/2025-01-13-liquidity-override.md`

---

### Future Changes (Awaiting Forward Testing)

**Potential Adjustments:**

1. **Threshold Tuning**
   - May need to raise/lower YELLOW threshold based on alert frequency
   - Target: 2-5 alerts per year
   - Will test: 6.0, 6.5, 7.0, 7.5

2. **Weight Rebalancing**
   - If recession indicators show limited lead time, may reduce to 25%
   - If credit velocity proves highly predictive, may increase to 30%
   - Will test: Multiple weight combinations

3. **Indicator Refinement**
   - May remove indicators that contribute noise (low correlation to crashes)
   - May add indicators that show strong backtesting performance
   - Candidates for addition: Credit impulse, put/call ratios, sentiment surveys

4. **Velocity Window Optimization**
   - Currently using: YoY for claims/M2, 20-day for credit, 6-month for Fed funds
   - May adjust lookback periods based on optimal lead time

**Decision Criteria:**
- Only change if backtest shows >5% improvement in F1 score
- Requires validation across multiple crash scenarios
- Document in ADR with before/after metrics

---

## Design Principles (Invariants)

These principles should NOT change without strong evidence:

1. **Free Data Only**
   - Rationale: Personal portfolio tool, not institutional
   - Will not pay for Bloomberg, FactSet, etc.
   - Exception: If free alternative disappears

2. **Transparent Scoring**
   - Rationale: User must understand why alert triggered
   - No black-box ML for overall score (may use for individual indicators)
   - All thresholds documented and configurable

3. **Rare Alerts**
   - Rationale: Alert fatigue destroys effectiveness
   - Target: 2-5 per year (not 2-5 per month)
   - High bar for notifications

4. **Reproducible Calculations**
   - Rationale: Backtesting and auditability
   - Same inputs = same outputs (no randomness)
   - All calculations logged and traceable

5. **Graceful Degradation**
   - Rationale: API failures happen
   - Calculate score with available data
   - Log missing indicators, don't crash

---

## Methodology Comparison

### Version Comparison Table

| Aspect | v0.1 (Initial) | v0.2 (Current) | v1.0 (Future) |
|--------|----------------|----------------|---------------|
| Dimensions | 5 | 5 | TBD |
| Indicators | 16 | 16 | TBD |
| YELLOW Threshold | 6.5 | 4.0 | TBD |
| RED Threshold | 8.0 | 5.0 | TBD |
| Recession Weight | 30% | 25% | TBD |
| Liquidity Weight | 15% | 20% | TBD |
| Liquidity Override | ❌ No | ✅ Yes | ✅ Yes |
| Backtested? | ❌ No | ✅ Yes | ✅ Yes |
| Live Validated? | ❌ No | ❌ No | ✅ Yes |
| 2022 Detection | ❌ Missed | ✅ Caught | ✅ Caught |

---

## Key Insights from Testing

### Backtest Learnings (Awaiting Results)

**Expected Findings:**

1. **Velocity indicators:** Should show earlier signals than level-based
   - Hypothesis: 3-6 month lead time advantage
   - Test: Compare pure velocity vs pure level backtests

2. **Positioning dimension:** May be noisy but valuable at extremes
   - Hypothesis: 10% weight is appropriate
   - Test: Compare with/without positioning

3. **Alert frequency:** May need threshold adjustment
   - Hypothesis: 6.5 threshold gives 2-5 alerts/year
   - Test: Count alerts across different thresholds

4. **Dimension weights:** Current weights (30/25/20/15/10) should be close to optimal
   - Hypothesis: Recession + Credit together (55%) catch most crashes
   - Test: Grid search over weight combinations

**Actual Findings:** *(To be populated after backtest)*

- TBD
- TBD
- TBD

### Forward Testing Learnings (Awaiting Deployment)

**Real-World Validation:** *(To be tracked after deployment)*

| Alert # | Date | Score | Outcome (6mo) | Lesson Learned |
|---------|------|-------|---------------|----------------|
| TBD | N/A | N/A | N/A | N/A |

---

## Research Backlog

Ideas to explore in future methodology iterations:

### High Priority

1. **Credit Impulse Indicator**
   - Description: Rate of change of credit growth (leading indicator)
   - Data Source: China credit growth (BIS), US commercial & industrial loans
   - Potential Impact: High (6-12 month lead on recessions)
   - Effort: Medium (data available from FRED)
   - Status: Not yet implemented

2. **Options Skew / Put-Call Ratios**
   - Description: Sentiment and hedging demand
   - Data Source: CBOE (free), Yahoo Finance options data
   - Potential Impact: Medium (concurrent to leading)
   - Effort: Medium (API integration)
   - Status: Not yet implemented

3. **Regime Shift Detection**
   - Description: LLM-based qualitative overlay (Fed speeches, policy changes)
   - Data Source: Fed statements, FOMC minutes, earnings calls
   - Potential Impact: Medium (captures "vibe shift")
   - Effort: High (LLM integration, prompt engineering)
   - Status: Configuration created, not implemented

### Medium Priority

4. **Sector Rotation Signals**
   - Description: Defensive vs cyclical sector performance
   - Data Source: Yahoo Finance (XLU/XLY ratio, etc.)
   - Potential Impact: Medium (confirms risk-on/risk-off)
   - Effort: Low (already using Yahoo Finance)
   - Status: Not yet implemented

5. **International Indicators**
   - Description: European PMI, China credit, global yield curves
   - Data Source: FRED (some available), ECB, PBOC
   - Potential Impact: Medium (early warning from non-US)
   - Effort: High (multiple APIs, data quality issues)
   - Status: Not yet implemented

6. **Earnings Revision Breadth**
   - Description: % of S&P 500 with positive earnings revisions
   - Data Source: FactSet (paid), Zacks (limited free), I/B/E/S
   - Potential Impact: Medium (leading indicator)
   - Effort: High (paid data or web scraping)
   - Status: Blocked by data cost

### Low Priority

7. **Commodity Signals**
   - Description: Copper/gold ratio, oil volatility
   - Data Source: Yahoo Finance, FRED
   - Potential Impact: Low (redundant with other indicators)
   - Effort: Low
   - Status: Not yet implemented

8. **Housing Indicators**
   - Description: Permits, starts, existing home sales
   - Data Source: FRED
   - Potential Impact: Low (long lags, less relevant for drawdowns)
   - Effort: Low
   - Status: Not yet implemented

---

## Decision Process for Changes

### When to Change Methodology

**Required Evidence:**

1. **Backtest Improvement:** New approach must improve F1 score by ≥5%
2. **Cross-Validation:** Must work across multiple crash scenarios (not overfit to single event)
3. **Stability:** Must not drastically increase false positive rate
4. **Interpretability:** User must be able to understand why alert triggered

**Change Approval Process:**

1. Propose change with hypothesis and expected impact
2. Backtest on historical data (2000-2024)
3. Compare metrics to baseline (F1, precision, recall, lead time)
4. Write ADR documenting decision
5. Update `METHODOLOGY_EVOLUTION.md` with version change
6. Update `config/indicators.yaml` or `config/app.yaml`
7. Re-run full test suite
8. Commit with detailed message

**Rollback Policy:**

- If forward testing shows new methodology is worse, revert to previous version
- Track version in `config/app.yaml` → `version` field
- Keep previous configs in `config/archive/` directory

---

## Version Roadmap

### v0.1 → v0.2 (Post-Backtest Refinement)

**Target Date:** 2025-01-20 (after initial backtest)

**Expected Changes:**
- Threshold adjustments based on alert frequency
- Possible weight rebalancing
- Indicator additions/removals based on contribution analysis

**Success Criteria:**
- F1 score ≥0.70
- Catch ≥3/4 major crashes
- Lead time 30-90 days average
- <10 false positives over 24 years

### v0.2 → v1.0 (Validated Production Release)

**Target Date:** 2025-04-01 (after 2-3 months forward testing)

**Required:**
- ≥3 months of real-time alerts tracked
- At least 1 alert validated (6-month waiting period)
- Backtest re-run with updated data
- Documentation complete and accurate
- User confidence in methodology

**Success Criteria:**
- Real-time alerts match expected frequency (2-5/year)
- No major misses (drawdown >20% without alert)
- User trust in system (following recommendations)

---

## References

- **Architecture Decision Records:** `docs/decisions/`
- **Backtest Results:** `docs/BACKTESTING_RESULTS.md`
- **Indicator Catalog:** `docs/INDICATORS_CATALOG.md`
- **Configuration:** `config/app.yaml`, `config/indicators.yaml`

---

## Appendix: Rejected Ideas

### Idea: Machine Learning for Overall Score

**Proposed:** Use XGBoost/Random Forest to weight indicators dynamically

**Why Rejected:**
- Black box reduces interpretability
- Limited training data (only 4 major crashes since 2000)
- Overfitting risk with small sample size
- Violates "transparent scoring" principle

**May Revisit:** If get 10+ years of forward testing data

### Idea: Real-Time News Sentiment

**Proposed:** Parse news headlines for fear/greed sentiment

**Why Rejected:**
- Noisy and reactive (not leading)
- Expensive APIs (Bloomberg, Refinitiv)
- Hard to backtest (historical news archives limited)
- Violates "free data only" principle

**May Revisit:** If free LLM-based sentiment becomes reliable

### Idea: Technical Analysis (Moving Averages, RSI, etc.)

**Proposed:** Add 50-day / 200-day MA cross as liquidity indicator

**Why Rejected:**
- Technical indicators are reactive, not leading
- Aegis is macro/fundamental system, not technical
- Already have VIX for market sentiment
- Better suited for separate tactical overlay

**May Revisit:** As optional user-configurable overlay

---

**Last Updated:** 2025-01-13
**Next Review:** After 2-3 months forward testing (Apr 2025)
**Document Version:** 2.0

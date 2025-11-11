# Aegis Risk Scoring Methodology

**UPDATED 2025-11-09**: After 2000-2024 backtest, implemented hybrid leading + coincident system.

## Core Philosophy: Dual-Indicator Approach

**LEADING Signal (Valuation)**: Detects bubble conditions months before crashes
**COINCIDENT Signal (Macro)**: Confirms crises as they unfold
**OVERLAY Signal (Qualitative)**: Detects regime shifts via news scanning

### Why Hybrid?

**Discovery from Backtest:**
- Pure macro indicators are COINCIDENT (lag by 9-18 months after market peaks)
- Credit spreads widen DURING panic, unemployment rises AFTER layoffs
- Valuation extremes build BEFORE crashes (months of lead time)

**Solution:**
1. **Valuation warnings** (CAPE + Buffett) for early warning of bubble peaks
2. **Macro scoring** (credit/recession/liquidity) for crisis confirmation
3. **Combined alerts** for nuanced decision-making

See `docs/backtest_results.md` and `docs/valuation_warnings.md` for empirical validation.

---

## Core Philosophy: Data-First, News-Second

**Primary Signal**: Quantitative economic indicators with rate-of-change emphasis
**Secondary Signal**: Qualitative regime shifts detected via news scanning

## Quantitative Core Refinements

### 1. Rate of Change Over Absolute Values

The **velocity** of indicator changes often provides more predictive power than absolute levels.

#### Unemployment Claims

**Traditional Approach** (Lagging):
```python
unemployment_rate = get_fred('UNRATE')  # 3.5%
if unemployment_rate > 4.5:
    score += 2.0
```

**Enhanced Approach** (Leading):
```python
initial_claims = get_fred('ICSA')  # Weekly initial claims
claims_4wk_avg = initial_claims.rolling(4).mean()
claims_change_pct = (claims_4wk_avg[-1] / claims_4wk_avg[-52]) - 1  # YoY change

if claims_change_pct > 0.15:  # 15% jump YoY
    score += 4.0  # Strong leading signal of stress
elif claims_change_pct > 0.08:
    score += 2.0
```

**Rationale**: A sudden 15% spike in unemployment claims is an extremely leading indicator of recession, often preceding broader unemployment rate increases by 3-6 months.

---

#### Credit Spreads

**Traditional Approach**:
```python
hy_spread = get_fred('BAMLH0A0HYM2')  # 5.2%
if hy_spread > 6.0:
    score += 3.0
```

**Enhanced Approach**:
```python
hy_spread = get_fred('BAMLH0A0HYM2')
spread_level_score = score_by_level(hy_spread)

# Rate of change signal (4-week)
spread_change = hy_spread[-1] - hy_spread[-20]  # 20 trading days
spread_velocity = spread_change / 20  # Daily rate

# Weight velocity MORE than level
if spread_velocity > 0.1:  # Rapidly widening (10bps/day)
    velocity_score = 4.0  # Immediate liquidity/funding issue
elif spread_velocity > 0.05:
    velocity_score = 2.0
else:
    velocity_score = 0.0

# Combine (velocity weighted higher)
score = (velocity_score * 0.7) + (spread_level_score * 0.3)
```

**Rationale**: Spreads widening rapidly suggests an immediate liquidity or funding crisis (2008, March 2020), even if absolute levels aren't historically extreme yet.

---

### 2. Diffusion Index Signal: PMI Expansion/Contraction Cross

ISM PMI is a **diffusion index**: values above 50 = expansion, below 50 = contraction.

**Critical Signal**: The cross from expansion into contraction territory.

```python
ism_pmi = get_fred('NAPM')  # ISM Manufacturing PMI
previous_pmi = ism_pmi[-2:-1]  # Last month

# Detect expansion → contraction cross
if ism_pmi[-1] < 50 and previous_pmi >= 50:
    score += 3.0  # Major regime shift
elif ism_pmi[-1] < 50:
    # Already in contraction
    if ism_pmi[-1] < 45:
        score += 2.5  # Deep contraction
    else:
        score += 1.5
elif ism_pmi[-1] < 52 and previous_pmi >= 52:
    score += 1.0  # Warning: approaching contraction
```

**Rationale**: The transition from expansion to contraction is the most predictive moment, not just being below 50. This binary shift often precedes NBER recession declarations by 3-6 months.

---

### 3. Yield Curve: Near-Term Forward Spread

**Traditional**: 10Y-2Y spread (T10Y2Y)

**Enhanced**: Add 3M → 18M Forward Spread (highly scrutinized by NY Fed)

```python
# Traditional 10Y-2Y
spread_10y2y = get_fred('T10Y2Y')

# Near-term forward spread (3M → 18M)
# Calculate using Fed Funds Futures and short-term Treasuries
fed_funds_futures_18m = get_cme_futures('FF', months=18)
tbill_3m = get_fred('DTB3')

forward_spread = fed_funds_futures_18m - tbill_3m

# Scoring
def score_yield_curve(spread_10y2y, forward_spread):
    score = 0.0

    # 10Y-2Y inversion
    if spread_10y2y < -0.50:
        score += 3.0  # Deep inversion
    elif spread_10y2y < 0:
        score += 1.5

    # Near-term forward spread (often inverts FIRST)
    if forward_spread < -0.30:
        score += 2.0  # Highly predictive
    elif forward_spread < 0:
        score += 1.0

    # Both inverted = extreme signal
    if spread_10y2y < 0 and forward_spread < 0:
        score += 1.0  # Bonus for confirmation

    return min(score, 10.0)
```

**Rationale**: The NY Fed research shows the near-term forward spread often inverts before the traditional 10Y-2Y, providing earlier warning. When BOTH are inverted, recession probability is extremely high.

**Source**: [NY Fed: The Yield Curve as a Leading Indicator](https://www.newyorkfed.org/research/capital_markets/ycfaq.html)

---

### 4. Leverage & Speculation: CFTC Commitments of Traders

**Beyond VIX**: Net speculative positioning in S&P 500 and Treasury futures.

```python
# CFTC Commitment of Traders Report
# Net Speculative Position = (Long - Short) / Open Interest

sp500_net_spec = get_cftc_data('SP500', category='speculative')
treasury_net_spec = get_cftc_data('US10Y', category='speculative')

# Extreme positioning = contrarian signal
def score_positioning(sp500_net, treasury_net, historical_data):
    score = 0.0

    # S&P 500 positioning (percentile relative to 2-year history)
    sp500_percentile = calculate_percentile(sp500_net, historical_data)

    if sp500_percentile > 95:
        # Extreme net long = complacency, risk of reversal
        score += 2.0
    elif sp500_percentile < 5:
        # Extreme net short = potential capitulation/bottom
        score -= 1.0  # Contrarian opportunity signal

    # Treasury positioning (extreme shorts = risk of short squeeze)
    if treasury_net < percentile(historical_data, 5):
        score += 1.5  # Crowded short, funding risk

    return score
```

**Rationale**: Extreme net positioning (especially extreme longs in equities or shorts in bonds) often precedes violent reversals. This is a sentiment/positioning metric that complements price-based indicators.

**Data Source**: [CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)

---

## Qualitative Overlay: Regime Shift Detection

Instead of subjective ±1.0 point adjustments, use **fixed, rule-based scores** triggered by LLM-extracted events.

### Event Categories & Scoring

| Qualitative Signal | Definition | Adjustment Score | Auditability |
|-------------------|------------|------------------|--------------|
| **Financial Contagion** | Bank run, systemic stress, credit crunch, liquidity freeze, emergency lending facility | **+3.0 pts** | Major Shock |
| **Geopolitical Shock** | Invasion, war, embargo, sanctions, supply chain blockade, OPEC surprise | **+2.0 pts** | Structural Break |
| **Policy Reversal** | Emergency rate cut/hike, abandoned target, unprecedented fiscal spend, TARP, QE/QT reversal | **+1.5 pts** | Regime Shift |
| **Expert Capitulation** | High-signal expert (Grantham, Hussman, Gundlach, Buffett) declares bubble/bear market | **+1.0 pts** | Sentiment Check |

### Implementation

```python
# src/scoring/regime_shift.py

def detect_regime_shifts(articles, lookback_days=7):
    """
    Scan news articles for qualitative regime shifts

    Returns:
        float: Adjustment score (0-10)
        list: Detected events with evidence
    """

    prompt = f"""
    Analyze the following {len(articles)} articles from the past {lookback_days} days.

    Identify if ANY of these Qualitative Regime Shifts occurred:

    1. FINANCIAL CONTAGION
       Keywords: "bank run", "systemic stress", "credit crunch", "liquidity freeze",
                 "emergency lending facility", "FDIC seizure", "bailout"
       Examples: Lehman Brothers (2008), Silicon Valley Bank (2023)
       Score: +3.0 if detected

    2. GEOPOLITICAL SHOCK
       Keywords: "invasion", "war", "embargo", "sanctions", "supply chain blockade",
                 "OPEC surprise", "pandemic lockdown"
       Examples: Russia-Ukraine (2022), COVID-19 (2020), Gulf War (1990)
       Score: +2.0 if detected

    3. POLICY REVERSAL
       Keywords: "emergency rate cut/hike", "abandoned inflation target",
                 "unprecedented fiscal spending", "TARP", "quantitative easing reversal"
       Examples: March 2020 emergency cuts, 2008 TARP
       Score: +1.5 if detected

    4. EXPERT CAPITULATION
       Keywords: "Jeremy Grantham" OR "John Hussman" OR "Jeffrey Gundlach" OR "Warren Buffett"
                 AND ("bubble", "bear market", "untenable valuation", "top of market")
       Only count if expert explicitly declares bearish position
       Score: +1.0 if detected

    Return JSON:
    {{
      "financial_contagion": {{
        "detected": true/false,
        "score": 3.0 or 0.0,
        "evidence": "Quote from article",
        "source": "Article title/source"
      }},
      "geopolitical_shock": {{ ... }},
      "policy_reversal": {{ ... }},
      "expert_capitulation": {{ ... }},
      "total_adjustment": sum of all scores,
      "confidence": "HIGH/MEDIUM/LOW"
    }}

    Articles:
    {format_articles(articles)}
    """

    response = llm_client.generate_json(prompt)

    return response['total_adjustment'], response
```

### Auditability

Each adjustment is logged with:
- Event category
- Triggering article/source
- Specific quote/evidence
- Timestamp
- Confidence level

Example log entry:
```json
{
  "date": "2023-03-10",
  "event": "financial_contagion",
  "score_adjustment": 3.0,
  "evidence": "Silicon Valley Bank seized by FDIC after $42B deposit run",
  "source": "Federal Reserve Press Release",
  "confidence": "HIGH",
  "impact": "Raised overall risk from 6.2 to 9.2"
}
```

This makes the qualitative layer **backtestable**: you can audit historical events and validate whether the scoring was appropriate.

---

## Combined Scoring Architecture

### Weekly Risk Calculation

```python
def calculate_weekly_risk():
    # 1. QUANTITATIVE CORE (Primary Signal)
    recession_score = calculate_recession_risk_enhanced(
        claims_velocity=get_claims_velocity(),
        pmi_cross=detect_pmi_cross(),
        yield_curves=get_yield_curves()  # 10Y-2Y + 3M-18M forward
    )

    credit_score = calculate_credit_stress_enhanced(
        spread_velocity=get_spread_velocity(),
        spread_level=get_current_spreads()
    )

    valuation_score = calculate_valuation_risk(
        cape=get_shiller_cape(),
        buffett_indicator=get_market_cap_to_gdp()
    )

    liquidity_score = calculate_liquidity_risk(
        fed_policy=get_fed_stance(),
        m2_growth=get_m2_velocity()
    )

    positioning_score = calculate_positioning_risk(
        cftc_data=get_cftc_positioning()
    )

    # Weighted quantitative score
    quant_score = (
        recession_score * 0.30 +
        credit_score * 0.25 +
        valuation_score * 0.20 +
        liquidity_score * 0.15 +
        positioning_score * 0.10
    )

    # 2. QUALITATIVE OVERLAY (Secondary Signal)
    regime_adjustment, events = detect_regime_shifts(
        articles=get_weekly_articles(),
        lookback_days=7
    )

    # 3. COMBINED RISK SCORE
    final_score = min(quant_score + regime_adjustment, 10.0)

    return {
        'quantitative_score': quant_score,
        'regime_adjustment': regime_adjustment,
        'regime_events': events,
        'final_score': final_score,
        'dimensions': {
            'recession': recession_score,
            'credit': credit_score,
            'valuation': valuation_score,
            'liquidity': liquidity_score,
            'positioning': positioning_score
        }
    }
```

---

## Enhanced Indicator Reference

### Updated Indicator Configuration

```yaml
recession_indicators:
  unemployment_claims_velocity:
    source: "FRED"
    series_id: "ICSA"
    name: "Initial Unemployment Claims (4-week avg YoY change)"
    calculation: "4wk_avg_change_yoy"
    scoring:
      extreme_spike: 0.15  # 15% YoY increase
      moderate_spike: 0.08

  pmi_regime_shift:
    source: "FRED"
    series_id: "NAPM"
    name: "ISM Manufacturing PMI (Expansion/Contraction Cross)"
    scoring:
      cross_into_contraction: 50  # Trigger when crosses below 50
      deep_contraction: 45

  yield_curve_enhanced:
    traditional:
      series_id: "T10Y2Y"
      weight: 0.5
    near_term_forward:
      calculation: "FF_futures_18m - DTB3"
      weight: 0.5
    scoring:
      both_inverted_bonus: 1.0  # Extra weight if both inverted

credit_indicators:
  high_yield_velocity:
    source: "FRED"
    series_id: "BAMLH0A0HYM2"
    calculation: "20day_rate_of_change"
    scoring:
      rapid_widening: 0.1  # 10 bps/day
      moderate_widening: 0.05
    weight_ratio:
      velocity: 0.7
      level: 0.3

positioning_indicators:
  sp500_spec_net:
    source: "CFTC"
    contract: "SP500"
    calculation: "net_speculative_percentile_2y"
    scoring:
      extreme_long: 95  # 95th percentile = complacency
      extreme_short: 5   # 5th percentile = capitulation

  treasury_spec_net:
    source: "CFTC"
    contract: "US10Y"
    calculation: "net_speculative_percentile_2y"
    scoring:
      crowded_short: 5  # Extreme shorts = squeeze risk
```

---

## Backtesting Enhancements

With these refinements, backtest scenarios to validate:

### 2008 Financial Crisis
- **Financial Contagion**: Lehman failure (Sept 2008) → +3.0 regime adjustment
- **Credit Velocity**: HY spreads widening rapidly (July-Sept) → recession_score +4.0
- **Yield Curve**: Inverted 2007-2008 → early warning
- **Expected Alert**: YELLOW by Q2 2007, RED by Q3 2008

### 2020 COVID Crash
- **Geopolitical Shock**: Pandemic lockdowns (March 2020) → +2.0 regime adjustment
- **Unemployment Velocity**: Claims spike 1000% in 2 weeks → recession_score 10.0
- **Policy Reversal**: Emergency Fed cuts + QE restart → +1.5 regime adjustment
- **Expected Alert**: GREEN → RED in 1 week (very rapid, correctly captured by velocity indicators)

### 2022 Bear Market
- **Valuation**: CAPE >35 (2021) → early warning
- **Policy Reversal**: Fed pivots from QE to QT (2022) → +1.5 regime adjustment
- **Credit Velocity**: Spreads widen as rates rise → credit_score increases
- **Expected Alert**: YELLOW by Q1 2022, sustained through year

---

## Summary of Enhancements

### Quantitative Core
1. ✅ **Rate of Change** over absolute values (unemployment claims velocity, credit spread velocity)
2. ✅ **PMI Regime Cross** detection (expansion → contraction as major trigger)
3. ✅ **Enhanced Yield Curve** (add 3M-18M forward spread alongside 10Y-2Y)
4. ✅ **CFTC Positioning** data (extreme speculation/contrarian signals)

### Qualitative Overlay
1. ✅ **Fixed scoring rules** for regime shifts (+3.0, +2.0, +1.5, +1.0)
2. ✅ **Auditable event categories** (Financial Contagion, Geopolitical Shock, Policy Reversal, Expert Capitulation)
3. ✅ **Evidence logging** (specific quotes, sources, timestamps)
4. ✅ **Backtestable** (can validate historical adjustments)

### System Properties
- **Objective**: Clear formulas, reproducible calculations
- **Leading**: Velocity indicators catch regime changes earlier
- **Robust**: Combines quantitative precision with qualitative Black Swan detection
- **Auditable**: Every adjustment logged with evidence

---

**Result**: A more predictive quantitative core with a streamlined, rule-based qualitative overlay that maintains objectivity while capturing regime shifts.

---

## Implemented Special Signals (2025-11)

Beyond the core 5-dimension scoring, Aegis includes special warning signals that detect specific risk conditions:

### Signal #1: Double Inversion Warning

**Trigger Condition**: Yield curve inverted (-0.1% or worse) AND credit stress elevated (HY spreads ≥5.0%)

**Risk Level**: HIGH

**Message**: "DOUBLE INVERSION WARNING: Yield curve inverted AND credit stress elevated. Historical precedent: 2007-2008 Financial Crisis. Recession signal + funding stress = severe risk."

**Rationale**: When recession signals (inverted yield curve) combine with funding stress (elevated credit spreads), the probability of severe market stress is extremely high. This combination preceded the 2007-2008 financial crisis.

**Implementation**: `src/scoring/aggregator.py:_check_double_inversion()`

---

### Signal #2: Real Rate Warning

**Trigger Condition**: Real interest rate > 1.0% AND rising rapidly (>10% in 6 months)

**Risk Level**: HIGH

**Message**: "REAL RATE WARNING: Fed tightening aggressively. Real rate X.X% (Fed Y.Y% - Inflation Z.Z%) and rising rapidly (+W.W% in 6 months). Historical precedent: 2022 bear market (-25%), 1994 bond sell-off, 2018 Q4 (-20%). Fed headwind can cause selloff even without recession."

**Rationale**: Rapidly rising real interest rates (Fed funds minus inflation) create a headwind for asset valuations. Even without recession, aggressive Fed tightening can cause significant market corrections (2022 bear market, 1994 bond selloff, 2018 Q4).

**Key Insight**: This signal catches market stress from monetary policy tightening that occurs WITHOUT recession - a distinct risk scenario.

**Implementation**: `src/scoring/aggregator.py:_check_real_rate_warning()`

---

### Signal #3: Valuation Extreme Warning

**Trigger Condition**: CAPE ratio ≥35 OR Buffett Indicator ≥140%

**Risk Level**: HIGH

**Message**: "VALUATION WARNING: Market at extreme levels (CAPE=X.X, Buffett Indicator=Y%). Historical precedent: Dot-com (2000), COVID peak (2020). Consider building cash position incrementally."

**Rationale**: Extreme valuation levels have historically preceded major market corrections. While valuation alone doesn't predict timing, it indicates elevated risk of sharp declines when catalysts emerge.

**Historical Examples**:
- Dot-com bubble (2000): CAPE ~44, subsequent -49% decline
- COVID peak (2020): CAPE ~38, subsequent -34% decline
- Pre-GFC (2007): Buffett Indicator ~140%, subsequent -57% decline

**Implementation**: `src/scoring/aggregator.py:_check_valuation_warning()`

---

### Signal #4: Earnings Recession Warning

**Trigger Condition**: Trailing 12-month earnings declined >10% over past 12 months

**Risk Level**: HIGH

**Message**: "EARNINGS RECESSION WARNING: Trailing 12M earnings declining sharply. 12-month earnings change: X.X% (from $Y.YY to $Z.ZZ). Historical precedent: 2001-2002 tech crash, 2008-2009 financial crisis, 2015-2016 energy collapse. Profit pressure can cause market selloff even without GDP recession."

**Data Source**: Shiller CAPE dataset - Trailing 12-month real earnings

**IMPORTANT CAVEAT**: This signal uses **TRAILING earnings** (historical actual earnings, NOT forward estimates). This is a **LAGGING indicator** that detects earnings recessions DURING the decline, not predictively. Forward earnings estimates are not available historically for backtesting.

**Rationale**: Periods of significant earnings decline often cause market stress even without official GDP recessions. Corporate profit pressure reduces valuations and can trigger selloffs.

**Historical Examples**:
- 2001-2002: Post-tech bubble earnings collapse
- 2008-2009: Financial crisis earnings decline
- 2015-2016: Energy/industrial earnings recession (no GDP recession)

**Implementation**: `src/scoring/aggregator.py:_check_earnings_recession()`

**Code Location**: `src/data/shiller.py:get_trailing_earnings_as_of()` - Extracts trailing earnings from Shiller CAPE dataset

---

### Signal #5: Housing Bubble Warning

**Trigger Condition**: Median home prices rising >20% YoY AND mortgage rates <4% AND new home sales accelerating

**Risk Level**: HIGH

**Message**: "HOUSING BUBBLE WARNING: Home prices surging (+X.X% YoY), mortgage rates at Y.Y%, new home sales accelerating. Historical precedent: 2005-2007 housing bubble. Unsustainable price acceleration can reverse sharply when rates rise or lending tightens."

**Rationale**: Rapid home price appreciation combined with low rates and accelerating sales often indicates a housing bubble. When conditions reverse (rates rise or credit tightens), housing corrections can spillover to broader economy.

**Historical Example**: 2005-2007 housing bubble preceded the 2008 financial crisis

**Implementation**: `src/scoring/aggregator.py:_check_housing_bubble()`

---

### Signal Integration

All special signals are checked during risk aggregation and included in warning messages when active. Multiple signals can trigger simultaneously, indicating elevated multi-dimensional risk.

**Example Combined Warning** (March 2000):
- Signal #3: VALUATION WARNING (CAPE ~44)
- Signal #1: DOUBLE INVERSION WARNING (yield curve + credit stress)

**Example Combined Warning** (2022):
- Signal #2: REAL RATE WARNING (Fed tightening aggressively)
- Signal #3: VALUATION WARNING (CAPE ~35)

These signals provide specific, actionable context beyond the numerical risk score, helping users understand the TYPE of risk environment they're facing.

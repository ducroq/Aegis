# Aegis Risk Scoring Methodology

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

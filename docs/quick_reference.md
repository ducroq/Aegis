# Aegis Quick Reference Card

## Alert Interpretation & Action Guide

### Three-Tier Alert System

#### 🟡 VALUATION WARNING
**Trigger:** CAPE > 30 AND Buffett Indicator > 120%

**What it means:**
- Market is at bubble-level valuations
- Fragile conditions, vulnerable to shocks
- NOT an immediate crash signal

**What to do:**
- [ ] Start building cash position (target 20-40%)
- [ ] Reduce or eliminate margin
- [ ] Tighten stop losses
- [ ] Favor quality over speculation
- [ ] Monitor macro indicators for deterioration
- [ ] Timeline: Implement over 4-8 weeks (gradual)

**What NOT to do:**
- ❌ Panic sell everything
- ❌ Try to time the exact top
- ❌ Short the market (bubbles can inflate further)
- ❌ Ignore the warning ("this time is different")

**Historical precedent:**
- Dot-com (2000): Warned 83 days before peak
- COVID (2020): Warned 80 days before peak
- 2017-2018: Warned but no major crash (market up 20%, then -20% correction)

---

#### 🟠 YELLOW ALERT
**Trigger:** Overall risk score ≥ 4.0

**What it means:**
- Macro stress is building
- Economic deterioration underway
- Risk of significant market decline

**What to do:**
- [ ] Accelerate to 40-60% cash
- [ ] Move to defensive sectors (healthcare, utilities, staples)
- [ ] Reduce equity exposure
- [ ] Consider defensive hedges (if experienced)
- [ ] Review portfolio for high-beta/speculative positions

**Combined signals:**
- **Valuation WARNING + YELLOW**: Accelerate to 60% cash immediately
- **YELLOW only** (no valuation warning): Often late, but still reduce risk

---

#### 🔴 RED ALERT
**Trigger:** Overall risk score ≥ 5.0

**What it means:**
- Crisis is confirmed and underway
- Major damage likely occurring or imminent
- Economic/credit stress at severe levels

**What to do:**
- [ ] Move to 60-80% cash
- [ ] Hold defensive positions only
- [ ] Preserve capital mode
- [ ] Do NOT try to catch falling knives
- [ ] Wait for confirmation signals before re-entering

**Combined signals:**
- **Valuation WARNING + RED**: Maximum defense, 80% cash
- **RED only** (no valuation warning): Crisis underway, stay defensive

**When to re-enter:**
- Wait for RED to clear (score drops below 5.0)
- Look for stabilization signals (credit spreads narrowing, VIX declining)
- Re-enter gradually over weeks/months

---

## Decision Matrix

| Valuation | Macro | Cash Target | Action |
|-----------|-------|-------------|--------|
| GREEN | GREEN | 0-10% | Full risk-on |
| **WARNING** | GREEN | **20-40%** | **Start reducing** |
| **WARNING** | YELLOW | **40-60%** | **Accelerate defense** |
| **WARNING** | RED | **60-80%** | **Maximum defense** |
| GREEN | YELLOW | 30-50% | Tactical caution |
| GREEN | RED | 50-70% | Stay defensive |

---

## Example Scenarios

### Scenario 1: Dot-com Bubble (2000)

**Timeline:**
- Jan 2000: 🟡 VALUATION WARNING fires
  - Action: Reduce 100% → 70% equity over 8 weeks
- Mar 2000: Market peaks (you're at 70% equity)
- Dec 2000: 🟠 YELLOW alert (macro deteriorating)
  - Action: Reduce 70% → 40% equity
- Feb 2009: 🔴 RED alert (crisis confirmed)
  - Action: Reduce 40% → 30% equity, full defense
- Late 2002: RED clears, start re-entry

**Result:** Avoided most of -49% crash

---

### Scenario 2: Financial Crisis (2007-2009)

**Timeline:**
- Oct 2007: Market peaks (NO valuation warning - CAPE only 27)
- Aug 2008: 🟠 YELLOW alert (11 months after peak)
  - You're already down ~30%, but reduce to 50% equity
- Dec 2008: 🔴 RED alert
  - Move to 30% equity
- Mar 2009: Market bottoms, RED persists
- Mid 2009: RED clears, start re-entry

**Result:** Missed early warning (credit crisis, not valuation bubble), but confirmed crisis and avoided worst of damage

---

### Scenario 3: 2017-2018 False Positive

**Timeline:**
- Jul 2017: 🟡 VALUATION WARNING fires
  - Action: Reduce 100% → 70% equity
- Market continues up 20% over next year
- Dec 2018: Market corrects -20%
- Early 2019: Recovery begins

**Result:**
- "Missed" 20% upside by holding 30% cash
- Avoided -20% correction on that 30%
- Net: Slightly underperformed but preserved capital

**Lesson:** False positives are acceptable cost of avoiding crashes

---

## Monitoring Commands

### Check Current Status
```bash
python scripts/show_status.py
```

### Run Valuation Warning Test
```bash
python scripts/test_valuation_warnings.py
```

### Check Historical Performance
```bash
python scripts/backtest.py
```

### Daily Update
```bash
python scripts/daily_update.py
```

---

## Key Metrics to Watch

When ANY alert is active, monitor these:

### Market Indicators
- VIX > 30 = Fear/stress
- VIX < 15 = Complacency
- S&P 500 200-day MA (below = bear market)

### Credit Indicators
- HY spreads > 500bps = Stress
- HY spreads > 800bps = Crisis
- HY spreads < 300bps = Complacency

### Economic Indicators
- Unemployment claims rising = Layoffs
- ISM PMI < 50 = Contraction
- Yield curve inverted = Recession risk

---

## FAQs

**Q: Valuation warning has been active for 6 months. Should I sell more?**
A: No. Bubbles can last years. Maintain your 20-40% cash cushion. Only accelerate if macro YELLOW/RED fires.

**Q: I got YELLOW alert but no valuation warning. What does that mean?**
A: Macro stress building (credit crisis, recession) but not a valuation bubble. Still reduce risk to 40-60% cash.

**Q: RED alert fired. Should I go 100% cash?**
A: No. 60-80% cash is sufficient. Some equity exposure for eventual recovery. Don't try to time exact bottom.

**Q: When do I buy back in?**
A: When RED clears (score < 5.0) AND you see stabilization (credit spreads narrowing, VIX declining). Re-enter gradually.

**Q: What if I'm fully invested and YELLOW fires?**
A: Sell 40-60% of portfolio over 1-2 weeks. Prioritize:
1. Speculative/high-beta stocks first
2. Cyclical sectors
3. Keep defensive/quality names

**Q: False positive rate is 43%. Isn't that high?**
A: Acceptable because:
- Cost of missing crash (−50%) >> cost of false positive (−10% opportunity cost)
- Warnings call for gradual reduction, not panic selling
- Even "false" warnings often precede corrections (−20%)

---

## Technical Details

### Valuation Warning Thresholds
- CAPE > 30.0 (historical avg ~17, normal p90 ~31)
- Buffett Indicator > 120% (fair value = 100%)
- Both must be true simultaneously

### Macro Score Calculation
- Weighted average of 5 dimensions
- Recession: 30%
- Credit: 25%
- Valuation: 20%
- Liquidity: 15%
- Positioning: 10%

### Alert Thresholds (Calibrated from 2000-2024 Backtest)
- RED: ≥ 5.0 (was 8.0 originally)
- YELLOW: ≥ 4.0 (was 6.5 originally)

---

## Documents for Deep Dive

- `docs/methodology.md` - How scoring works
- `docs/backtest_results.md` - Historical performance (macro only)
- `docs/valuation_warnings.md` - Valuation system details
- `README.md` - System overview

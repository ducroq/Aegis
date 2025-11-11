# Catalyst Detection Enhancement Roadmap

**Goal**: Improve Aegis's ability to detect market catalysts that could trigger corrections despite low baseline risk scores.

**Current Gap**: Aegis detects baseline macro conditions well (valuations, credit, recession), but misses acute catalysts (geopolitical shocks, earnings deterioration, credit events, black swans).

---

## Priority 1: Geopolitical Shock Detection

### Approach A: News Sentiment Analysis (Automated)
**Data Source**: Financial news APIs
- Reuters/Bloomberg APIs (paid)
- NewsAPI.org (free tier available)
- Google News RSS feeds (free)

**Implementation**:
1. Daily news scraping for keywords:
   - "war", "conflict", "sanctions", "trade war"
   - "coup", "crisis", "emergency", "lockdown"
   - Country names + "default", "debt crisis"

2. Sentiment scoring using:
   - Simple keyword matching (MVP)
   - Or LLM-based sentiment (GPT-4, Claude API)
   - Track "fear score" over time

3. Alert threshold:
   - Spike in negative sentiment >2 std deviations
   - Cluster of crisis keywords in 24-hour window

**Pros**: Automated, real-time
**Cons**: Noisy, requires tuning, API costs

### Approach B: Manual Checklist (Simple MVP)
**Implementation**:
1. Weekly manual review of major headlines
2. Simple scoring rubric:
   - Major war/conflict: +3.0 to risk score
   - Trade sanctions/tariffs: +1.5 to risk score
   - Political crisis: +1.0 to risk score

3. Log adjustments in `data/manual_adjustments.csv`

**Pros**: Simple, no API costs, human judgment
**Cons**: Not scalable, requires weekly discipline

**Recommendation**: Start with Approach B (manual), upgrade to Approach A later.

---

## Priority 2: Earnings Recession Detection (Enhanced)

### Current Coverage:
- ✅ Signal #4: Earnings velocity (trailing 12-month earnings YoY change)

### Gaps:
- Forward earnings guidance (not just historical)
- Earnings call sentiment (management tone)
- Profit margin trends

### Enhancement Plan:

#### Phase 1: Add Forward P/E Velocity
**Data Source**: Yahoo Finance (free)
- Track S&P 500 forward P/E ratio
- Calculate 3-month velocity
- Alert if forward P/E falling >10% in 3 months

**Implementation**: Extend `src/data/market_data.py`

#### Phase 2: Earnings Surprise Tracking
**Data Source**: Earnings Whispers API or manual CSV
- Track % of S&P 500 companies missing earnings
- Alert if >40% missing in a quarter (deterioration)

**Implementation**: New module `src/data/earnings_data.py`

#### Phase 3: Earnings Call Sentiment (Advanced)
**Data Source**: AlphaVantage API (free tier)
- Scrape earnings call transcripts
- LLM sentiment analysis on management commentary
- Track "cautious language" frequency

**Pros**: Leading indicator of earnings trouble
**Cons**: Complex, API rate limits

**Recommendation**: Implement Phase 1 first (forward P/E velocity).

---

## Priority 3: Credit Event Detection (Enhanced)

### Current Coverage:
- ✅ Credit spread widening (HY, IG spreads)
- ✅ Bank lending standards

### Gaps:
- Individual company/bank failures (SVB 2023)
- Credit default swap (CDS) spreads spiking
- Corporate default rates

### Enhancement Plan:

#### Phase 1: CDS Spread Monitoring
**Data Source**:
- Markit iTraxx/CDX indices (paid: Bloomberg/Refinitiv)
- Or proxy: VIX, HYG ETF option-adjusted spreads (free)

**Implementation**:
- Track CDX High Yield index spread
- Alert if spread >500 bps or rising >100 bps/week

#### Phase 2: Bank Stock Volatility
**Data Source**: Yahoo Finance (free)
- Track KBW Bank Index (^BKX) volatility
- Alert if bank stock vol spikes >50% above 30-day average

**Rationale**: Bank stock crashes precede credit events (see SVB 2023)

#### Phase 3: Default Rate Tracking
**Data Source**: Moody's/S&P default rate reports (free monthly PDFs)
- Manual entry or web scraping
- Track trailing 12-month default rate
- Alert if >4% (historical recession levels)

**Recommendation**: Implement Phase 2 (bank stock vol) - easiest and free.

---

## Priority 4: Black Swan / Pandemic Detection

### Approach: Daily News Monitoring + WHO Alerts
**Data Sources**:
- WHO Disease Outbreak News RSS feed (free)
- CDC Emergency Preparedness RSS (free)
- Google News for "pandemic", "outbreak", "epidemic"

**Implementation**:
1. Daily RSS feed check
2. Keyword matching: "pandemic", "outbreak", "Level 5", "emergency"
3. Manual review flag (not automatic alert)

**Rationale**: Black swans are unpredictable, but early warning systems exist.

**Recommendation**: Low priority - focus on economic catalysts first.

---

## Priority 5: Liquidity Crisis Detection (Intra-Market)

### Current Coverage:
- ✅ Monthly liquidity indicators (M2, Fed policy)

### Gaps:
- Flash crashes, margin calls (intraday)
- Dealer inventory stress
- Funding market stress (repo rates)

### Enhancement Plan:

#### Phase 1: VIX Spike Detection
**Data Source**: Yahoo Finance (free, daily)
- Track VIX daily closes
- Alert if VIX >30 or +50% spike in 1 day

**Implementation**: Add to daily update script

#### Phase 2: MOVE Index (Bond Volatility)
**Data Source**: ICE BofA MOVE Index
- Track bond market volatility
- Alert if MOVE >150 (historical stress level)

#### Phase 3: Repo Rate Monitoring
**Data Source**: FRED (SOFR, repo rates)
- Track overnight repo rate spikes
- Alert if repo >2% above Fed Funds (funding stress)

**Recommendation**: Implement Phase 1 (VIX spikes) - simple and effective.

---

## Implementation Roadmap

### Phase 1 (MVP - Next 2 Weeks)
1. ✅ Document current market state (`MARKET_ANALYSIS_2024.md`)
2. 🔲 Manual geopolitical checklist (weekly review)
3. 🔲 VIX spike detection (daily update script)
4. 🔲 Bank stock volatility monitoring (^BKX tracking)

### Phase 2 (1 Month)
1. 🔲 Forward P/E velocity tracking
2. 🔲 News sentiment analysis (simple keyword-based)
3. 🔲 Earnings surprise tracking (quarterly)

### Phase 3 (3 Months)
1. 🔲 CDS spread monitoring
2. 🔲 Earnings call sentiment (LLM-based)
3. 🔲 Pandemic RSS monitoring

### Phase 4 (6 Months)
1. 🔲 Full NexusMind integration (news analysis platform)
2. 🔲 Real-time alert dashboard
3. 🔲 Multi-timeframe risk scoring (daily + weekly + monthly)

---

## Success Metrics

**Goal**: Catch catalysts 7-30 days before they cascade into market crashes.

**Measurement**:
- Lead time to detection vs. market drawdown
- False positive rate (target: <20% of alerts)
- Coverage: Detect 80%+ of major catalysts (>10% drawdowns)

**Backtesting**:
- 2020 COVID: Would VIX spike + WHO alert catch it? (Feb 2020)
- 2022 Ukraine: Would news sentiment catch it? (Feb 2022)
- 2023 SVB: Would bank stock vol catch it? (Mar 2023)

---

## Notes

- Start simple (manual + VIX) before building complex systems
- Prioritize high-signal, low-noise indicators
- Balance automation with human judgment
- Integrate with existing Aegis architecture (don't rebuild)
- Focus on **actionable** alerts (what can user do with this info?)

---

**Last Updated**: 2024-12-11

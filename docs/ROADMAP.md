# Aegis - Development Roadmap

## Now (Current Sprint - Next 1-2 Weeks)

### 🎯 Backtesting Infrastructure (Priority: P0, Risk: Medium, Effort: Large)
- [ ] Build `scripts/backtest.py` - Historical validation framework
- [ ] Load historical FRED data (2000-2024)
- [ ] Calculate what risk scores would have been
- [ ] Compare alerts to actual market drawdowns
- [ ] Generate backtest metrics report
- **Why:** Must validate methodology before trusting it with real money
- **Success Criteria:** System catches 3/4 major crashes with <10 false positives

### 📊 Threshold Calibration (Priority: P0, Risk: High, Effort: Medium)
- [ ] Analyze backtest results by threshold level
- [ ] Tune YELLOW/RED thresholds for 2-5 alerts/year target
- [ ] Document threshold rationale in ADR
- [ ] Update `config/app.yaml` with calibrated values
- **Why:** Current thresholds are educated guesses, need empirical validation
- **Blocker:** Depends on backtesting completion

## Next (Coming Soon - Next 2-4 Weeks)

### 🤖 Orchestration Scripts (Priority: P1, Risk: Low, Effort: Medium)
- [ ] `scripts/daily_update.py` - Fetch data, calculate risk, save history
- [ ] `scripts/weekly_report.py` - Generate report, send if alert triggered
- [ ] `scripts/show_status.py` - CLI to display current risk
- [ ] Test end-to-end with dummy data
- **Why:** Need automation before production deployment

### 📧 Email Alert Polish (Priority: P1, Risk: Low, Effort: Small)
- [ ] Design HTML email template
- [ ] Add charts/visualizations (risk trend, dimension breakdown)
- [ ] Include track record (historical alert accuracy)
- [ ] Test email deliverability
- **Why:** Alerts need to be actionable and professional

### 🔄 Production Deployment (Priority: P1, Risk: Medium, Effort: Medium)
- [ ] Set up cron job or scheduler (daily at 6 AM)
- [ ] Configure real API keys (FRED, SendGrid)
- [ ] Test full daily workflow
- [ ] Set up monitoring/error alerting
- **Why:** Make system operational for real-world use

## Later (Backlog - Next 1-3 Months)

### 📈 Dashboard (Optional) (Priority: P2, Risk: Low, Effort: Large)
- [ ] Flask app for visualization
- [ ] Charts: Risk history, dimension breakdown, indicator trends
- [ ] Deploy to Heroku or local server
- **Why:** Nice-to-have for monitoring, not critical for alerts

### 🌐 Additional Data Sources (Priority: P2, Risk: Medium, Effort: Medium)
- [ ] Shiller CAPE data scraper
- [ ] CFTC Commitments of Traders client
- [ ] International indicators (Europe, China)
- **Why:** Richer data for better signals

### 🧪 Regime Shift Detection (Priority: P2, Risk: High, Effort: Large)
- [ ] LLM-based qualitative overlay (NexusMind integration)
- [ ] Detect Black Swan events from news
- [ ] Boost risk score on significant regime changes
- **Why:** Complements quant signals, but adds complexity

### 📱 Mobile Notifications (Priority: P3, Risk: Low, Effort: Medium)
- [ ] Push notifications via Pushover/Twilio
- [ ] Mobile-friendly dashboard
- **Why:** Faster alerts than email, but not essential

### 🔬 Advanced Features (Priority: P3, Risk: High, Effort: Large)
- [ ] Options market signals (put/call ratios, skew)
- [ ] Sector rotation analysis (defensives vs cyclicals)
- [ ] Credit impulse from China
- [ ] Factor exposures (value, momentum, quality)
- **Why:** Potential signal improvement, but diminishing returns

## Completed ✅

### Core Implementation (Completed: 2025-01-08)
- [x] Configuration manager with YAML/secrets.ini
- [x] FRED API client with caching and velocity
- [x] Market data client (Yahoo Finance)
- [x] All 5 risk dimension scorers
- [x] Risk aggregator with weighted scoring
- [x] Alert logic with threshold checking
- [x] Email sender with formatting
- [x] History manager for CSV storage
- [x] Data manager orchestration

### Test Infrastructure (Completed: 2025-01-08)
- [x] Comprehensive test suite (104 tests)
- [x] pytest configuration with markers
- [x] GitHub Actions CI/CD pipeline
- [x] Multi-platform testing (Ubuntu, Windows, macOS)
- [x] Coverage reporting with Codecov integration
- [x] Test documentation

### Documentation (Completed: 2025-01-08)
- [x] README with project overview
- [x] Methodology documentation
- [x] Getting started guide
- [x] Testing strategy
- [x] CLAUDE.md for AI context
- [x] AI-Augmented Solo Dev Framework setup

---

## Prioritization Framework

Tasks are prioritized based on:

| Factor | Weight | Reasoning |
|--------|--------|-----------|
| **Business Value** | 40% | Does this make system more useful/reliable? |
| **Risk Reduction** | 30% | Does this reduce chance of false signals or missed crashes? |
| **User Experience** | 15% | Does this make system easier to use/trust? |
| **Learning/Innovation** | 10% | Does this teach us something valuable? |
| **Fun Factor** | 5% | Is this enjoyable to build? |

**Priority Levels:**
- **P0 (Critical):** Must have for production readiness
- **P1 (High):** Important for quality experience
- **P2 (Medium):** Nice-to-have enhancements
- **P3 (Low):** Future exploration

**Risk Assessment:**
- **High Risk:** Unproven approach, could fail or need iteration
- **Medium Risk:** Standard implementation with some unknowns
- **Low Risk:** Well-understood, straightforward implementation

**Effort Estimate:**
- **Small:** Hours (1-8 hours)
- **Medium:** Days (1-5 days)
- **Large:** Weeks (1-3 weeks)

---

## Decision Framework: What to Work On Next?

Consider these factors:

1. **Time Available:**
   - <2 hours? → Small, low-risk tasks (documentation, polish)
   - 2-8 hours? → Medium tasks (backtesting analysis, script writing)
   - 1+ days? → Large tasks (full backtesting framework, dashboard)

2. **Energy Level:**
   - High energy? → Complex tasks (backtesting logic, threshold tuning)
   - Medium energy? → Standard implementation (orchestration scripts)
   - Low energy? → Documentation, testing, bug fixes

3. **Context:**
   - Fresh start? → P0/P1 tasks (backtesting, production deployment)
   - Mid-project? → Continue current work package
   - Feeling exploratory? → P2/P3 nice-to-haves (dashboard, advanced features)

4. **Blockers:**
   - Always check if other tasks are blocked by current work
   - Prefer unblocking tasks over new features

---

## Milestones

### Milestone 1: Core Complete ✅ (2025-01-08)
All modules implemented, tested, and passing CI/CD

### Milestone 2: Validated System 🎯 (Target: 2025-01-20)
Backtesting complete, thresholds calibrated, methodology proven

### Milestone 3: Production Ready 🎯 (Target: 2025-02-01)
Daily automation running, alerts configured, monitoring in place

### Milestone 4: Enhanced Experience 🎯 (Target: 2025-03-01)
Dashboard operational, additional data sources integrated

### Milestone 5: Advanced Features 🎯 (Target: TBD)
Regime detection, mobile alerts, options signals

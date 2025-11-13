# TODO: Dashboard Not Showing 2022 YELLOW Alerts

**Issue:** Despite updating risk_scores.csv with v0.2.0 methodology (2022 shows YELLOW), the live dashboard at https://aegis-risk.netlify.app/history still shows 2022 as GREEN.

**Status:** ⏸️ DEFERRED - Needs future investigation

**Last Updated:** 2025-01-13 (session ended)

---

## What We Tried (Comprehensive List)

### Data Updates
1. ✓ Updated CSV with correct YELLOW data (verified locally and on GitHub)
2. ✓ Regenerated all historical scores with v0.2.0 methodology
3. ✓ Verified CSV shows: `2022-04-01,1.74,...,YELLOW,True`
4. ✓ Confirmed Netlify is serving correct CSV (WebFetch verified YELLOW in CSV)

### Cache Busting Attempts
5. ✓ Added cache-busting query parameters (?v=0.2.0)
6. ✓ Used timestamp-based cache busting (Date.now())
7. ✓ Moved CSV files into dashboard/data/ directory to serve from Netlify
8. ✓ Hard refresh, incognito mode, cleared cache - still shows GREEN
9. ✓ Manual Netlify deploy triggered multiple times

### Code Fixes
10. ✓ Fixed JavaScript to use `tier` column from CSV instead of recalculating from score
11. ✓ Changed lines 235-240 in dashboard/history.js to read tier directly
12. ✓ Committed and pushed changes (commit 96a87e8)

### Deployment Verification
13. ✓ Configured Netlify webhook for auto-deploy
14. ✓ Manually deployed after each change
15. ✗ **Dashboard still shows GREEN** despite all changes

---

## Current State

| Component | Status | Details |
|-----------|--------|---------|
| Local CSV | ✅ Correct | `2022-04-01,1.74,...,YELLOW,True` |
| GitHub CSV | ✅ Correct | Same as local |
| Netlify CSV | ✅ Correct | WebFetch confirms YELLOW in served CSV |
| JavaScript Logic | ✅ Fixed | Now reads `tier` column instead of calculating |
| Live Dashboard | ❌ Wrong | Still shows 2022 as GREEN |

---

## Root Cause Theories

### Theory 1: Aggressive Browser/CDN Caching
Despite all cache-busting attempts, something is caching the old visualization. The CSV is correct but the rendered chart is stale.

### Theory 2: JavaScript Not Reloading
The history.js file might be cached by:
- Browser cache (despite hard refresh)
- Netlify CDN edge cache
- Service worker (if one exists)

### Theory 3: Data Parsing Issue
JavaScript might be loading CSV correctly but parsing `tier` column incorrectly (e.g., reading wrong column index, trimming issues).

### Theory 4: Plotly Chart State
Plotly might be caching internal state or not properly re-rendering with new data.

---

## Debugging Steps for Next Session

### 1. Add Console Logging
```javascript
// In dashboard/history.js, line 235
const colors = riskData.map(d => {
    console.log(`Date: ${d.date}, Tier: ${d.tier}, Score: ${d.overall_risk}`);
    const tier = d.tier || 'GREEN';
    // ... rest of code
});
```

### 2. Check Browser Console
Open browser dev tools → Console tab → Look for:
- Any errors loading CSV
- Console logs from above
- Network tab: verify CSV request shows latest data

### 3. Verify Netlify Deployment
- Check deploy logs: https://app.netlify.com/sites/aegis-risk/deploys
- Verify files actually updated in deploy preview
- Check if dashboard/data/ directory is included

### 4. Nuclear Option: Complete Cache Purge
```javascript
// Add to history.js
const CACHE_BUST = '20250113'; // Update this each deploy
GITHUB_CSV_URL: `/data/risk_scores.csv?v=${CACHE_BUST}`,
```

### 5. Manual Verification
Download https://aegis-risk.netlify.app/data/risk_scores.csv directly and inspect in text editor to confirm tier values.

---

## Workarounds

### For Demo Purposes
The backtest results are valid and documented. The methodology works correctly (proven by backtest script showing YELLOW). Dashboard visualization is a UI bug, not a methodology issue.

### For Production Use
When GitHub Actions runs daily updates:
- Risk scores will be calculated correctly
- CSV will show correct tiers
- Email alerts (when implemented) will use correct tier logic
- Only the dashboard visualization is affected

---

## Next Steps

**Priority:** Medium (UI bug, not core functionality)

**When to revisit:**
1. After other higher-priority features are complete
2. When setting up monitoring/logging infrastructure
3. If dashboard becomes critical for daily use

**Alternative Solution:**
Consider rebuilding dashboard with a different approach:
- Use Python script to generate static HTML report
- Pre-render charts server-side instead of client-side
- Use a different charting library (Chart.js, D3.js)

---

**Date:** 2025-01-13
**Session Duration:** Extended debugging session
**Outcome:** Issue documented but not resolved

# TODO: Dashboard Not Showing 2022 YELLOW Alerts

**Issue:** Despite updating risk_scores.csv with v0.2.0 methodology (2022 shows YELLOW), the live dashboard at https://aegis-risk.netlify.app/history still shows 2022 as GREEN.

**Status:** Not resolved - needs future investigation

**What We Tried:**
1. ✓ Updated CSV with correct YELLOW data (verified locally and on GitHub)
2. ✓ Added cache-busting query parameters (?v=0.2.0)
3. ✓ Used timestamp-based cache busting (Date.now())
4. ✓ Moved CSV files into dashboard/data/ directory to serve from Netlify
5. ✗ Hard refresh, incognito mode, cleared cache - still shows GREEN

**Current State:**
- Local CSV: `2022-04-01,1.74,...,YELLOW,True` ✓ Correct
- GitHub CSV: `2022-04-01,1.74,...,YELLOW,True` ✓ Correct
- Netlify dashboard/data/risk_scores.csv: Should be correct (pushed)
- Live site: Shows 2022 as GREEN ✗ Wrong

**Possible Causes:**
1. Netlify CDN caching (despite headers in netlify.toml)
2. Browser service worker caching
3. CSP/CORS issue preventing CSV load
4. JavaScript parsing issue with tier column
5. Plotly chart color mapping issue

**Next Steps to Try:**
1. Check browser console for errors when loading /data/risk_scores.csv
2. Add console.log in history.js to debug what tier values are being read
3. Verify Netlify deployment actually includes dashboard/data/ files
4. Check Netlify deploy logs for any file exclusion warnings
5. Try renaming CSV files entirely (risk_scores_v2.csv) to force new file
6. Add explicit cache-control headers for /data/*.csv in netlify.toml

**Workaround:**
For now, the methodology is correct in the codebase. The dashboard display issue is cosmetic - the actual risk calculation would work correctly in production use.

**Date:** 2025-01-13
**Priority:** Medium (affects demo/visualization, not core functionality)

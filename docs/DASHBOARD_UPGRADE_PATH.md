# Dashboard Upgrade Path

**Current Architecture**: Option A+ (Static HTML + GitHub CSV fetch)
**Status**: Production-ready, deployed to Netlify
**Last Updated**: 2024-12-11

## When to Upgrade

Stay with **Option A+** (current approach) unless you encounter one of these triggers:

### ❌ Stay Simple (Current Approach Works)
- Monthly or weekly data updates
- CSV size < 1MB (~2,000 data points)
- Public data (no authentication needed)
- Simple visualizations (time series, radar, bars)
- Personal use or small audience (<10,000 views/month)

### ✅ Upgrade to Hugo (Option C)
**Trigger Conditions:**
- Need content management (blog posts, methodology explanations)
- Want SEO optimization for public sharing
- Multi-page dashboard (separate pages for each dimension)
- Static site generation with templates
- CSV still small (<1MB)

**Complexity:** Low (2-3 hours)
**Cost:** Still free (Netlify)

### ✅ Upgrade to React + Netlify Functions (Option B)
**Trigger Conditions:**
- Hourly or more frequent data updates
- CSV size > 1MB (slow client-side parsing)
- Need custom date range filtering
- Want advanced interactivity (drill-downs, multi-chart linking)
- User authentication required
- Real-time data integration (WebSockets, polling)

**Complexity:** Medium-High (8-16 hours)
**Cost:** Free tier initially, may incur function costs at scale

## Migration Paths

### Path 1: Option A+ → Hugo (Static Site Generator)

**Why Hugo?**
- Keeps simplicity of static hosting
- Adds templating, content management, SEO
- Can still fetch CSV from GitHub client-side
- Fast builds (<1 second for 100 pages)

**Migration Steps:**

1. **Install Hugo**
   ```bash
   # Windows (via Chocolatey)
   choco install hugo-extended

   # Mac
   brew install hugo

   # Verify
   hugo version
   ```

2. **Initialize Hugo Site**
   ```bash
   cd C:\local_dev\Aegis
   hugo new site dashboard-hugo
   cd dashboard-hugo

   # Choose a theme (example: PaperMod for dashboards)
   git submodule add https://github.com/adityatelange/hugo-PaperMod themes/PaperMod
   ```

3. **Migrate Existing Assets**
   ```bash
   # Copy current dashboard files
   cp ../dashboard/index.html layouts/_default/index.html
   cp ../dashboard/js/dashboard.js static/js/
   cp -r ../dashboard/css static/ (if any)
   ```

4. **Configure Hugo**
   ```toml
   # config.toml
   baseURL = 'https://aegis-risk.netlify.app/'
   languageCode = 'en-us'
   title = 'Aegis Portfolio Risk Dashboard'
   theme = 'PaperMod'

   [params]
     description = "Real-time macro risk monitoring"
     author = "Your Name"
   ```

5. **Update Netlify Config**
   ```toml
   # netlify.toml
   [build]
     publish = "dashboard-hugo/public"
     command = "cd dashboard-hugo && hugo --minify"

   [build.environment]
     HUGO_VERSION = "0.121.0"
   ```

6. **Test Locally**
   ```bash
   hugo server -D
   # Visit http://localhost:1313
   ```

7. **Deploy**
   ```bash
   git add .
   git commit -m "Migrate dashboard to Hugo"
   git push
   # Netlify auto-deploys with Hugo build command
   ```

**Reusable Components:**
- `dashboard/js/dashboard.js` → Works as-is in Hugo
- Charts (Plotly) → Same code, same CDN libraries
- CSV fetching logic → No changes needed

**What You Gain:**
- Content pages (methodology, about, changelog)
- SEO optimization (meta tags, sitemaps)
- Multi-page structure (dimensions on separate pages)
- Markdown content management
- Faster initial load (minified assets)

**What You Keep:**
- Client-side CSV fetching (no build step for data)
- Free Netlify hosting
- Simple deployment workflow

---

### Path 2: Option A+ → React + Netlify Functions

**Why React + Functions?**
- Full control over data pipeline
- Advanced interactivity (date pickers, filters)
- Server-side data processing (heavy CSV parsing)
- Real-time updates (polling, WebSockets)
- User authentication and personalization

**Migration Steps:**

1. **Create React App**
   ```bash
   cd C:\local_dev\Aegis
   npx create-react-app dashboard-react
   cd dashboard-react

   # Install dependencies
   npm install plotly.js-dist-min papaparse axios recharts
   ```

2. **Migrate Modular JavaScript to React Components**

   Our current `dashboard.js` is already modular, making migration easier:

   ```jsx
   // src/components/RiskTimeline.jsx (from ChartRenderer.createRiskTimeline)
   import React, { useEffect, useRef } from 'react';
   import Plotly from 'plotly.js-dist-min';

   export default function RiskTimeline({ data }) {
     const plotRef = useRef(null);

     useEffect(() => {
       if (!data || data.length === 0) return;

       const dates = data.map(d => d.date);
       const scores = data.map(d => d.overall_risk);

       const trace = {
         x: dates,
         y: scores,
         type: 'scatter',
         mode: 'lines+markers',
         name: 'Risk Score',
         line: { color: '#667eea', width: 3 }
       };

       const layout = {
         height: 400,
         xaxis: { title: 'Date' },
         yaxis: { title: 'Risk Score (0-10)', range: [0, 10] }
       };

       Plotly.newPlot(plotRef.current, [trace], layout, {responsive: true});
     }, [data]);

     return <div ref={plotRef} />;
   }
   ```

3. **Create Netlify Function for CSV Processing**

   ```javascript
   // netlify/functions/get-risk-data.js
   const axios = require('axios');
   const Papa = require('papaparse');

   exports.handler = async function(event, context) {
     try {
       const { startDate, endDate } = event.queryStringParameters || {};

       // Fetch CSV from GitHub
       const response = await axios.get(
         'https://raw.githubusercontent.com/ducroq/Aegis/master/data/history/risk_scores.csv'
       );

       // Parse CSV
       const parsed = Papa.parse(response.data, {
         header: true,
         dynamicTyping: true,
         skipEmptyLines: true
       });

       let data = parsed.data;

       // Server-side filtering (why we need Functions)
       if (startDate) {
         data = data.filter(d => d.date >= startDate);
       }
       if (endDate) {
         data = data.filter(d => d.date <= endDate);
       }

       return {
         statusCode: 200,
         headers: {
           'Content-Type': 'application/json',
           'Cache-Control': 'public, max-age=300' // 5 min cache
         },
         body: JSON.stringify(data)
       };
     } catch (error) {
       return {
         statusCode: 500,
         body: JSON.stringify({ error: error.message })
       };
     }
   };
   ```

4. **Update Netlify Config**

   ```toml
   # netlify.toml
   [build]
     publish = "dashboard-react/build"
     command = "cd dashboard-react && npm run build"
     functions = "netlify/functions"

   [build.environment]
     NODE_ENV = "production"

   [[redirects]]
     from = "/api/*"
     to = "/.netlify/functions/:splat"
     status = 200
   ```

5. **React Data Fetching Hook**

   ```jsx
   // src/hooks/useRiskData.js
   import { useState, useEffect } from 'react';
   import axios from 'axios';

   export default function useRiskData(startDate = null, endDate = null) {
     const [data, setData] = useState([]);
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);

     useEffect(() => {
       async function fetchData() {
         try {
           setLoading(true);
           const params = {};
           if (startDate) params.startDate = startDate;
           if (endDate) params.endDate = endDate;

           const response = await axios.get('/api/get-risk-data', { params });
           setData(response.data);
           setError(null);
         } catch (err) {
           setError(err.message);
         } finally {
           setLoading(false);
         }
       }

       fetchData();
     }, [startDate, endDate]);

     return { data, loading, error };
   }
   ```

6. **Main Dashboard Component**

   ```jsx
   // src/App.jsx
   import React, { useState } from 'react';
   import useRiskData from './hooks/useRiskData';
   import RiskTimeline from './components/RiskTimeline';
   import DimensionRadar from './components/DimensionRadar';

   export default function App() {
     const [dateRange, setDateRange] = useState({ start: null, end: null });
     const { data, loading, error } = useRiskData(dateRange.start, dateRange.end);

     if (loading) return <div>Loading...</div>;
     if (error) return <div>Error: {error}</div>;

     return (
       <div className="dashboard">
         <h1>Aegis Portfolio Risk Dashboard</h1>

         {/* Date range picker (new feature!) */}
         <DateRangePicker onChange={setDateRange} />

         {/* Existing charts, now as React components */}
         <RiskTimeline data={data} />
         <DimensionRadar data={data} />
       </div>
     );
   }
   ```

7. **Deploy**
   ```bash
   git add .
   git commit -m "Upgrade to React + Netlify Functions"
   git push
   ```

**Reusable Components:**
- Chart logic from `ChartRenderer` module → React components (90% reusable)
- Risk tier calculation from `RiskCalculator` → Utils folder
- Color schemes, thresholds from `CONFIG` → React Context or constants

**What You Gain:**
- Date range filtering (server-side)
- Advanced interactivity (drill-downs, tooltips)
- Code splitting (faster initial load)
- Type safety (with TypeScript migration)
- Testing infrastructure (Jest, React Testing Library)
- State management (Redux, Zustand)

**What You Lose:**
- Simplicity (more dependencies, build complexity)
- Zero-cost guarantee (Functions have invocation limits)

**Cost Estimate:**
- Free tier: 125,000 function invocations/month
- If 1,000 users/month × 10 page loads = 10,000 invocations (well within free)
- Only scales up cost with heavy traffic (>100K users/month)

---

## Comparison Table

| Feature | Option A+ (Current) | Hugo (Option C) | React + Functions (Option B) |
|---------|---------------------|-----------------|------------------------------|
| **Setup time** | 0 (done) | 2-3 hours | 8-16 hours |
| **Build time** | None | <1 second | 30-60 seconds |
| **Data updates** | Auto (GitHub) | Auto (GitHub) | Manual or automated pipeline |
| **Date filtering** | ❌ No | ❌ No | ✅ Yes |
| **SEO** | Basic | ✅ Excellent | Good |
| **Multi-page** | ❌ No | ✅ Yes | ✅ Yes |
| **Real-time data** | ❌ No | ❌ No | ✅ Yes |
| **Authentication** | ❌ No | ❌ No | ✅ Yes |
| **Cost** | Free | Free | Free (within limits) |
| **Maintenance** | Zero | Low | Medium |
| **Learning curve** | None | Low | Medium-High |

---

## Decision Framework

Use this flowchart to decide when to upgrade:

```
Start: Is current dashboard meeting your needs?
  ├─ YES → Stay with Option A+ (no upgrade needed)
  └─ NO → What's the primary limitation?

      ├─ "I need blog posts / SEO / multi-page structure"
      │   └─ Upgrade to Hugo (Option C)
      │       Time: 1 weekend
      │       Risk: Low

      ├─ "I need custom date filtering / advanced interactivity"
      │   └─ Upgrade to React + Functions (Option B)
      │       Time: 1-2 weeks
      │       Risk: Medium

      ├─ "CSV is too large (>1MB) / slow loading"
      │   └─ Upgrade to React + Functions (Option B)
      │       (Server-side parsing + caching)

      ├─ "I need real-time updates / user auth / database"
      │   └─ Upgrade to React + Functions + Database (Option D)
      │       Time: 3-4 weeks
      │       Risk: High
      │       (Consider Next.js + Supabase or similar)

      └─ "I want more frequent data updates (hourly/daily)"
           └─ Stay with Option A+, just update CSV more often
               (GitHub Actions workflow to auto-commit CSV)
```

---

## Gradual Migration Strategy

**Recommended**: Don't do a "big bang" rewrite. Migrate incrementally:

### Phase 1: Add Hugo for Content (Keep Dashboard Intact)
1. Hugo handles `/about`, `/methodology`, `/changelog`
2. Dashboard stays at `/dashboard` (existing static HTML)
3. Hugo layout links to dashboard
4. **Effort**: 3 hours, **Risk**: Very low

### Phase 2: Move Dashboard to Hugo Layout
1. Convert `index.html` to Hugo template (`layouts/index.html`)
2. JavaScript modules stay as static assets
3. **Effort**: 2 hours, **Risk**: Low

### Phase 3: Add React Components Gradually
1. Start with one chart (e.g., RiskTimeline)
2. Use Hugo shortcodes to embed React components
3. Test, iterate, expand to other charts
4. **Effort**: 1-2 hours per component, **Risk**: Low

### Phase 4: Full React Migration (If Needed)
1. Only if you need advanced features (filtering, auth)
2. By this point, you've validated React works for your use case
3. **Effort**: 8-16 hours, **Risk**: Medium

---

## Testing Before Migration

Before committing to an upgrade path, test locally:

### Test Hugo Locally (Option C)
```bash
hugo new site test-dashboard
cd test-dashboard
# Copy existing dashboard files
cp ../dashboard/index.html layouts/_default/index.html
cp ../dashboard/js/dashboard.js static/js/
hugo server -D
# Visit http://localhost:1313
# Does it work? Are charts rendering?
```

### Test React Locally (Option B)
```bash
npx create-react-app test-dashboard-react
cd test-dashboard-react
# Install dependencies
npm install plotly.js-dist-min papaparse
# Create one component (RiskTimeline.jsx) from existing code
npm start
# Visit http://localhost:3000
# Test chart rendering, data fetching
```

---

## Rollback Plan

If an upgrade goes wrong, rollback is simple:

1. **Git revert**:
   ```bash
   git log  # Find commit before migration
   git revert <commit-hash>
   git push
   ```

2. **Netlify rollback**:
   - Netlify dashboard → Deploys → Select previous successful deploy → "Publish deploy"

3. **Keep Option A+ branch**:
   ```bash
   # Before migration, create backup branch
   git checkout -b option-a-plus-backup
   git push -u origin option-a-plus-backup

   # If migration fails, restore:
   git checkout master
   git reset --hard origin/option-a-plus-backup
   git push --force
   ```

---

## Conclusion

**Current Status**: Option A+ is production-ready, deployed, and meeting requirements.

**Recommendation**: Stay with Option A+ until you hit a specific limitation (date filtering, SEO, large CSV). The modular JavaScript refactor (just completed) makes future migrations easier.

**Next Steps When Ready**:
1. Identify the trigger condition (see Decision Framework)
2. Test locally (Hugo or React test project)
3. Create git branch for migration (`git checkout -b upgrade-to-hugo`)
4. Implement incrementally (Phase 1 → 2 → 3)
5. Deploy to Netlify preview environment
6. Validate, then merge to master

**Timeline Estimate**:
- Hugo migration: 1 weekend (2-3 hours actual work)
- React migration: 1-2 weeks (8-16 hours actual work)
- Full-stack (React + DB): 3-4 weeks (requires backend architecture)

---

**Last Updated**: 2024-12-11
**Status**: Active, ready for future upgrades when needed

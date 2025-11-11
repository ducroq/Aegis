# Aegis Dashboard - Netlify Deployment Guide

Beautiful static dashboard for visualizing Aegis portfolio risk data, deployed to Netlify with automatic updates from GitHub.

## Features

- **Real-time risk monitoring**: Overall risk score with GREEN/YELLOW/RED tiers
- **Interactive charts**: Plotly.js visualizations with zoom, pan, and hover details
- **Historical analysis**: 300 months of risk data (2000-2024)
- **Dimension breakdown**: Radar and bar charts showing recession, credit, valuation, liquidity, positioning
- **Auto-updating**: Fetches latest CSV data directly from GitHub
- **Zero maintenance**: No build step, no server, no API limits

## Quick Start (Netlify Deployment)

### Option 1: Deploy via Netlify UI (Recommended)

1. **Push to GitHub** (if not already done):
   ```bash
   git add dashboard/ netlify.toml
   git commit -m "Add Netlify dashboard"
   git push
   ```

2. **Connect to Netlify**:
   - Go to [netlify.com](https://netlify.com) and sign in
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub and select the `Aegis` repository
   - Netlify will auto-detect `netlify.toml` configuration
   - Click "Deploy site"

3. **Done!**
   - Netlify assigns a URL like `https://aegis-risk-dashboard.netlify.app`
   - Every time you push to GitHub, Netlify auto-redeploys
   - Data updates automatically when CSV is pushed

### Option 2: Deploy via Netlify CLI

1. **Install Netlify CLI**:
   ```bash
   npm install -g netlify-cli
   ```

2. **Login and deploy**:
   ```bash
   netlify login
   netlify init
   netlify deploy --prod
   ```

3. **Configure**:
   - Build command: (leave empty)
   - Publish directory: `dashboard`

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                   User visits dashboard                 │
│              https://your-site.netlify.app              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │   index.html       │
            │   (from Netlify)   │
            └────────┬───────────┘
                     │
                     │ JavaScript fetches CSV
                     ▼
┌─────────────────────────────────────────────────────────┐
│   https://raw.githubusercontent.com/ducroq/Aegis/       │
│   master/data/history/risk_scores.csv                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │  Plotly.js renders │
            │  interactive charts│
            └────────────────────┘
```

**Key insight**: The dashboard HTML is static, but it fetches the latest CSV from GitHub on every page load. This means:
- ✅ No build step needed
- ✅ Data auto-updates when you push CSV to GitHub
- ✅ No API limits or server costs
- ✅ Fast CDN delivery via Netlify

## Updating Data

The dashboard automatically fetches the latest data from GitHub. To update:

1. **Run your data pipeline**:
   ```bash
   python scripts/daily_update.py
   # or
   python scripts/backfill_history.py --start-date 2000-01-01 --end-date 2024-12-31
   ```

2. **Commit and push CSV**:
   ```bash
   git add data/history/risk_scores.csv
   git commit -m "Update risk data - $(date +%Y-%m-%d)"
   git push
   ```

3. **Refresh dashboard**:
   - Dashboard fetches latest CSV from GitHub automatically
   - Users see updated data on next page load (no cache issues)

## Customization

### Change GitHub CSV URL

Edit `dashboard/index.html`, line ~200:

```javascript
const GITHUB_CSV_URL = 'https://raw.githubusercontent.com/YOUR-USERNAME/Aegis/master/data/history/risk_scores.csv';
```

### Adjust Risk Thresholds

Edit `dashboard/index.html`, `getRiskTier()` function:

```javascript
function getRiskTier(score) {
    if (score >= 8.0) return { tier: 'RED', color: '#ef4444' };
    if (score >= 6.5) return { tier: 'YELLOW', color: '#f59e0b' };
    return { tier: 'GREEN', color: '#10b981' };
}
```

### Custom Domain

In Netlify dashboard:
1. Go to "Domain settings"
2. Click "Add custom domain"
3. Follow instructions to configure DNS

Example: `risk.yourdomain.com`

## Local Testing

Just open `dashboard/index.html` in your browser!

```bash
# Windows
start dashboard/index.html

# Mac
open dashboard/index.html

# Linux
xdg-open dashboard/index.html
```

Or use a local server:

```bash
# Python 3
cd dashboard
python -m http.server 8000

# Then visit: http://localhost:8000
```

## Troubleshooting

### "Failed to fetch data" error

**Problem**: CORS error or GitHub URL not found

**Solution**:
1. Check that CSV file exists at GitHub URL
2. Verify repository is public (or use a GitHub token)
3. Check browser console for specific error

### Dashboard shows old data

**Problem**: Browser cache or GitHub cache

**Solution**:
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. GitHub raw files cache for ~5 minutes - wait and retry
3. Check that you pushed the latest CSV to GitHub

### Charts not rendering

**Problem**: Plotly.js or PapaParse not loading

**Solution**:
1. Check internet connection (CDN libraries)
2. Open browser console for JavaScript errors
3. Verify CSV format (header row with correct column names)

## CSV Format Requirements

The dashboard expects `risk_scores.csv` with these columns:

```csv
date,overall_risk,recession,credit,valuation,liquidity,positioning
2024-12-01,1.75,2.0,0.0,2.5,3.0,2.0
2024-11-01,1.82,2.1,0.1,2.6,3.1,2.1
...
```

**Required columns**:
- `date`: YYYY-MM-DD format
- `overall_risk`: Weighted risk score (0-10)
- `recession`, `credit`, `valuation`, `liquidity`, `positioning`: Dimension scores (0-10)

## Performance

- **Page load**: ~1-2 seconds (includes CSV fetch from GitHub)
- **Chart rendering**: ~500ms for 300 data points
- **Browser compatibility**: Chrome, Firefox, Safari, Edge (modern versions)
- **Mobile responsive**: Yes, charts adapt to screen size

## Cost

**FREE** - Netlify free tier includes:
- 100 GB bandwidth/month
- Unlimited sites
- Automatic HTTPS
- Continuous deployment

Perfect for personal dashboards with moderate traffic.

## Security

- No authentication required (dashboard is read-only)
- Data fetched from public GitHub repository
- No sensitive data exposed (all historical market data)
- HTTPS enabled by default on Netlify

If you want to make the dashboard private:
1. Set GitHub repository to private
2. Generate GitHub personal access token
3. Modify fetch URL to include token (not recommended for public sites)

## Future Enhancements

Potential additions (requires upgrading to Option B with React + Netlify Functions):

- Date range selector (filter historical data)
- Export charts as PNG/PDF
- Alert history log (show all triggered warnings)
- Custom indicator overlay (add S&P 500 price)
- Real-time FRED data integration
- Email alert subscription

## Support

- GitHub Issues: [github.com/ducroq/Aegis/issues](https://github.com/ducroq/Aegis/issues)
- Documentation: See main `README.md`

---

**Built with [Aegis](https://github.com/ducroq/Aegis)** - Open source macro risk monitoring

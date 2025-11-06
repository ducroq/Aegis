# Getting Started with Aegis

## Quick Start Guide

### 1. Prerequisites

- Python 3.9 or higher
- Git (for version control)
- A FRED API key (free)

### 2. Installation

```bash
# Navigate to project
cd C:\local_dev\Aegis

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get Your FRED API Key

1. Visit https://fred.stlouisfed.org/
2. Create a free account
3. Go to https://fred.stlouisfed.org/docs/api/api_key.html
4. Request an API key (instant approval)
5. Copy your key

### 4. Configure Secrets

```bash
# Copy the example secrets file
cp config/credentials/secrets.ini.example config/credentials/secrets.ini

# Edit the file and add your FRED API key
# Use any text editor:
notepad config/credentials/secrets.ini  # Windows
nano config/credentials/secrets.ini     # Mac/Linux
```

Add your key:
```ini
[api_keys]
fred_api_key = YOUR_ACTUAL_KEY_HERE
```

### 5. Test Your Setup

```bash
# Test that configuration loads correctly
python src/config/config_manager.py --test

# Expected output: "Configuration loaded successfully"
```

### 6. Run Your First Data Fetch

```bash
# Fetch latest economic data and calculate risk score
python scripts/daily_update.py

# Expected output:
# - Fetching data from FRED...
# - Calculating risk scores...
# - Overall risk: 5.2/10 (GREEN)
# - Saved to data/history/risk_scores.csv
```

### 7. View Current Risk Status

```bash
python scripts/show_status.py
```

Example output:
```
═══════════════════════════════════
AEGIS RISK ASSESSMENT
═══════════════════════════════════
Date: 2025-01-06
Overall Risk: 5.2/10 (GREEN)
Status: Normal conditions - stay the course

DIMENSION BREAKDOWN:
─────────────────────
• Recession Risk:     4.5/10 →
• Credit Stress:      5.0/10 ↑
• Valuation Extreme:  7.0/10 →
• Liquidity:          3.5/10 ↓
• Geopolitical:       4.0/10 →

No alerts triggered.
Next update: Tomorrow 6 PM
```

## Next Steps

### Set Up Email Alerts

1. **Option A: Gmail SMTP (Free)**
   - Enable 2FA in your Google Account
   - Generate an App Password: https://myaccount.google.com/apppasswords
   - Add to `config/credentials/secrets.ini`:
   ```ini
   [email_credentials]
   sender_email = your.email@gmail.com
   sender_password = your-app-password
   recipient_email = your.email@gmail.com
   ```

2. **Option B: SendGrid (Professional)**
   - Create free account: https://signup.sendgrid.com/
   - Get API key: https://app.sendgrid.com/settings/api_keys
   - Add to `config/credentials/secrets.ini`:
   ```ini
   [api_keys]
   sendgrid_api_key = SG.xxxxx
   ```

### Schedule Daily Updates

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6 PM
4. Action: Start a program
   - Program: `C:\local_dev\Aegis\venv\Scripts\python.exe`
   - Arguments: `C:\local_dev\Aegis\scripts\daily_update.py`

**Mac/Linux Cron:**
```bash
crontab -e

# Add line (runs daily at 6 PM):
0 18 * * * cd /path/to/Aegis && ./venv/bin/python scripts/daily_update.py
```

### Schedule Weekly Reports

Same process, but run `scripts/weekly_report.py` every Monday at 8 AM.

**Cron:**
```bash
0 8 * * 1 cd /path/to/Aegis && ./venv/bin/python scripts/weekly_report.py
```

## Understanding the Output

### Risk Score Interpretation

- **0-6.4 (GREEN)**: Normal market conditions, stay invested
- **6.5-7.9 (YELLOW)**: Elevated risk, consider building cash position
- **8.0-10.0 (RED)**: Severe risk, consider defensive positioning

### What to Do When You Get an Alert

**YELLOW Alert:**
1. Review your portfolio allocation
2. Consider building 10-20% cash position over next 4-8 weeks
3. Tilt toward defensive sectors (healthcare, utilities, consumer staples)
4. Don't panic sell everything

**RED Alert:**
1. Seriously consider 30-50% cash position
2. Review stop-loss levels
3. Reduce leverage/margin to zero
4. Wait for risk to drop before redeploying

**Remember:** Aegis can't predict exact timing. Alerts may come weeks or months before a crash (or there may be no crash at all - false alarm).

## Customization

### Adjust Your Risk Tolerance

Edit `config/app.yaml`:

```yaml
alerts:
  yellow_threshold: 6.5  # Lower = more sensitive (more alerts)
  red_threshold: 8.0     # Lower = more sensitive
```

### Adjust Dimension Weights

If you care more about credit stress than valuations:

```yaml
scoring:
  weights:
    recession: 0.30
    credit: 0.30        # Increased from 0.25
    valuation: 0.15     # Decreased from 0.20
    liquidity: 0.15
    geopolitical: 0.10
```

**Important:** Weights must sum to 1.0!

## Troubleshooting

### "FRED API key not found"
- Check `config/credentials/secrets.ini` exists (not `.example`)
- Verify key is under `[api_keys]` section
- Key format: `fred_api_key = abcdef1234567890`

### "No data returned from FRED"
- Check your internet connection
- Verify API key is valid (test at: https://fred.stlouisfed.org/docs/api/fred/)
- Some series may be discontinued or renamed

### "Import errors"
- Ensure you activated virtual environment: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Email alerts not sending
- Check credentials in `secrets.ini`
- For Gmail: ensure App Password is enabled (not regular password)
- Check spam folder
- Test with a simple script first

## What's Next?

- **Backtest**: Run historical validation to see how system would have performed
- **Calibrate**: Adjust thresholds based on your personal comfort level
- **Monitor**: Track alerts over next 6-12 months
- **Iterate**: Fine-tune weights/thresholds based on your experience

## Questions?

See the full documentation in `docs/` folder:
- `methodology.md` - Detailed scoring methodology
- `indicators.md` - Explanation of each indicator
- `backtest_results.md` - Historical performance analysis

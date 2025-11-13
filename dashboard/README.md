# Aegis Dashboard - Multi-Page Structure

## Overview

The Aegis dashboard has been restructured into a multi-page application for better UX and separation of concerns.

## Page Structure

### 1. **Overview** (`overview.html`)
**Purpose:** Quick snapshot of current risk status

**Content:**
- Current risk score and tier
- 4-week trend indicator
- Last updated timestamp
- Alert banner (if active)
- Current dimension breakdown (radar chart)
- Risk gauge
- Recent 30-day trend
- Active warning signals

**Use Case:** "What's the risk RIGHT NOW?" - Quick daily check

---

### 2. **History** (`history.html`)
**Purpose:** Deep dive into historical trends and backtest results

**Content:**
- Overall risk score timeline (full 300 months)
- Historical dimension trends
- Alert history and track record
- Statistical summary table
- Dimension correlation matrix
- Major market events overlay (2000, 2008, 2020, 2022)

**Features:**
- Time range selector (All Time, 5Y, 3Y, 1Y, YTD)

**Use Case:** "How has risk evolved over time?" - Research and validation

---

### 3. **Dimensions** (`dimensions.html`)
**Purpose:** Detailed breakdown of each risk component

**Dimensions:**
- Recession Risk (30%)
- Credit Stress (25%)
- Valuation Extremes (20%)
- Liquidity Conditions (15%)
- Positioning & Speculation (10%)

**Use Case:** "Why is recession risk elevated?" - Drill-down analysis

---

### 4. **Methodology** (`methodology.html`)
**Purpose:** Explain how the system works

**Use Case:** "How does this work?" - Education and transparency

---

## File Structure

```
dashboard/
├── index.html          # Redirects to overview.html
├── overview.html       # Current risk snapshot
├── history.html        # Historical trends
├── dimensions.html     # Dimension breakdown
├── methodology.html    # How it works
├── styles.css          # Shared CSS
└── README.md           # This file
```

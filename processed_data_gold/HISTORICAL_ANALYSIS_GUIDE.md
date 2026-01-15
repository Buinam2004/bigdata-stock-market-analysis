# Quick Start Guide: Historical Data Analysis

## Getting Started

### Step 1: Launch the Dashboard

```bash
cd processed_data_gold
streamlit run dashboard.py
```

### Step 2: Switch to Historical Mode

1. Look at the **left sidebar**
2. Under "Dashboard Settings", find **"View Mode"**
3. Select **"Historical Analysis"** (instead of "Real-Time")

### Step 3: Choose Your Time Period

Under "Historical Data Range" in the sidebar:

- See the available data range displayed
- Select a time period from the dropdown:
  - Quick options: Last Hour, Last 24 Hours, Last 7 Days, etc.
  - Or choose "Custom Range" for specific dates

### Step 4: Filter Your Data

- **Select Symbols**: Choose specific stocks to analyze (e.g., AAPL, MSFT)
- **Select Sectors**: Filter by sector (e.g., Technology, Healthcare)

### Step 5: Explore the Analysis

The main view will show:

#### 📊 Data Summary

- Number of symbols
- Buy/Sell signal counts
- Average signal score

#### 📈 Historical Trends

- Interactive chart comparing selected symbols
- Switch between metrics (Price, RSI, Volume, etc.)
- Zoom, pan, and hover for details

#### 📊 Trading Signal Distribution

- See how signals changed over time
- Color-coded by recommendation type
- Stacked bar chart by date

#### 📊 Performance Metrics by Symbol

- Tabs for each selected symbol
- Starting/ending prices with change %
- High/low prices
- Signal summary (buy/sell/hold counts)
- Golden/Death cross events
- Full historical charts with indicators

#### 💾 Export Data

- Scroll to the bottom
- Click "📥 Download CSV"
- Opens in Excel or import to Python/R

## Common Workflows

### 1️⃣ Review Yesterday's Trading

```
View Mode: Historical Analysis
Time Period: Last 24 Hours
Symbols: [Your watchlist]
```

### 2️⃣ Weekly Performance Check

```
View Mode: Historical Analysis
Time Period: Last 7 Days
Symbols: [Select 3-5 stocks]
Metric: Price (for trend chart)
```

### 3️⃣ Validate Signal Accuracy

```
View Mode: Historical Analysis
Time Period: Last 30 Days
Check: Signal Distribution Chart
Compare: Did prices follow signal recommendations?
```

### 4️⃣ Export for Analysis

```
View Mode: Historical Analysis
Time Period: [Your choice]
Symbols: [Filter as needed]
Action: Download CSV
Use: Excel, Python pandas, R, etc.
```

### 5️⃣ Switch Back to Real-Time

```
View Mode: Real-Time
Auto-refresh: ✓ Enabled
Watch: Live updates every 10 seconds
```

## Tips & Tricks

### 🎯 Best Practices

1. **Start with shorter time periods** - Last 24 Hours or Last 7 Days for faster loading
2. **Limit symbols to 3-5** - Charts become cluttered with too many symbols
3. **Use the metric selector** - Switch between Price, RSI, Volume to see different patterns
4. **Export for deep analysis** - CSV export allows custom calculations and visualizations
5. **Compare similar sectors** - Filter by sector for meaningful comparisons

### ⚡ Performance Tips

- Shorter date ranges = faster queries
- Fewer symbols = faster chart rendering
- Use predefined periods instead of "All Time"
- Disable auto-refresh in Historical mode (default)

### 🔍 Analysis Ideas

- **Trend Analysis**: Use Price metric to identify uptrends/downtrends
- **Momentum**: Check RSI metric for overbought/oversold patterns
- **Volume Patterns**: Volume spikes often precede price movements
- **Signal Validation**: Compare signal distribution to actual price changes
- **Cross-symbol Comparison**: See which stocks outperformed others

## Visual Reference

### Sidebar Layout (Historical Mode)

```
⚙️ Dashboard Settings
  ○ Real-Time
  ● Historical Analysis          ← Select this

  ☐ Auto-refresh                ← Usually unchecked

📊 Data Filters
  Select Symbols: [Dropdown]
  Select Sectors: [Dropdown]

📅 Historical Data Range
  Data available: 15,234 records
  From: 2026-01-10 08:00:00
  To:   2026-01-15 14:30:00

  Time Period: [Dropdown]        ← Choose here
    • Last Hour
    • Last 6 Hours
    • Last 24 Hours              ← Popular
    • Last 7 Days                ← Popular
    • Last 30 Days
    • All Time
    • Custom Range
```

### Main Dashboard Layout (Historical Mode)

```
📜 Historical Data Analysis
───────────────────────────────────────
Date Range: 2026-01-08 to 2026-01-15
Total Records: 1,245

[Symbols: 5] [🟢 Buy: 342] [🔴 Sell: 198] [Avg Score: 1.2]
───────────────────────────────────────

📈 Historical Trends
▸ Price & Indicator Comparison  [Metric: Price ▼]

[Interactive Line Chart]
───────────────────────────────────────

📊 Trading Signal Distribution

[Stacked Bar Chart showing signals by date]
───────────────────────────────────────

📊 Performance Metrics by Symbol
[AAPL] [MSFT] [GOOGL] [AMZN] [TSLA]

  Starting Price: $180.50
  Ending Price:   $185.75
  Price Change:   $5.25 ↑ 2.91%

  [Full technical analysis & charts]
───────────────────────────────────────

💾 Export Data
Download the historical data...  [📥 Download CSV]

▸ 📋 View Raw Historical Data (click to expand)
```

## Comparison: Real-Time vs Historical

| Feature      | Real-Time               | Historical            |
| ------------ | ----------------------- | --------------------- |
| Data Source  | Latest data only        | Date range filtered   |
| Auto-refresh | Yes (10-60 sec)         | No (manual refresh)   |
| Time Range   | Current moment          | Any historical period |
| Use Case     | Monitoring live markets | Analysis & research   |
| Charts       | Current indicators      | Trend comparisons     |
| Export       | Current snapshot        | Any date range        |

## Example Analysis Workflow

### Scenario: Evaluate a stock's performance

```
1. Open dashboard in Historical mode
2. Select Time Period: Last 30 Days
3. Choose Symbol: AAPL
4. Review the metrics tab:
   - Did price go up or down?
   - How many buy signals were generated?
   - What was the RSI trend?
5. Check the candlestick chart:
   - Identify support/resistance levels
   - Look for golden/death crosses
6. Export CSV for deeper analysis:
   - Calculate correlation with other stocks
   - Backtest a trading strategy
```

## Getting Help

### Data Not Showing?

- Make sure Gold layer processor is running
- Check if data exists in selected date range
- Try "All Time" to see what's available

### Charts Not Loading?

- Too many symbols selected (limit to 5)
- Date range too large (try shorter period)
- Browser compatibility (use Chrome/Firefox)

### Need More Analysis?

- Export CSV and use:
  - Python with pandas/matplotlib
  - Excel for pivot tables/charts
  - R for statistical analysis
  - Jupyter notebooks for exploration

## Next Steps

After using Historical Analysis:

1. **Identify patterns** in your selected stocks
2. **Validate signals** by comparing recommendations to actual price movements
3. **Export data** for custom backtesting
4. **Switch to Real-Time** to monitor current market
5. **Iterate** - Adjust filters and time periods to gain insights

---

**Happy Analyzing! 📊📈**

For more details, see [HISTORICAL_FEATURES.md](HISTORICAL_FEATURES.md)

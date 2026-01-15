# Historical Data Analysis Features

This document describes the new historical data viewing capabilities added to the dashboard.

## Overview

The dashboard now supports two viewing modes:

1. **Real-Time** - The original live streaming view
2. **Historical Analysis** - New feature for analyzing historical stock data

## New Features

### 1. View Mode Selector

- Toggle between "Real-Time" and "Historical Analysis" in the sidebar
- Auto-refresh is disabled by default in Historical mode for better performance

### 2. Date Range Selection

Choose from predefined time periods or select a custom date range:

- **Last Hour** - Most recent hour of data
- **Last 6 Hours** - Past 6 hours
- **Last 24 Hours** - Past day
- **Last 7 Days** - Past week
- **Last 30 Days** - Past month
- **All Time** - Complete historical data
- **Custom Range** - Select specific start and end dates

### 3. Historical Data Queries

Three new query functions:

- `load_historical_data()` - Loads data within a date range with filters
- `get_date_range_stats()` - Shows available data range and record count
- Supports filtering by symbols and sectors

### 4. Historical Visualizations

#### A. Historical Trend Comparison Chart

- Compare multiple symbols side-by-side over time
- Selectable metrics:
  - Price (close)
  - RSI (14-period)
  - Volume
  - Price Change %
  - Signal Score
- Interactive Plotly charts with zoom and pan

#### B. Trading Signal Distribution Chart

- Stacked bar chart showing signal distribution over time
- Color-coded by recommendation type:
  - 🟢 Strong Buy / Buy
  - 🟡 Hold
  - 🔴 Sell / Strong Sell
- Shows how signals change across dates

### 5. Historical Performance Metrics

For each selected symbol, the dashboard calculates and displays:

**Price Metrics:**

- Starting Price
- Ending Price
- Price Change (absolute and %)
- Highest Price in period
- Lowest Price in period

**Volume Metrics:**

- Average Volume

**Technical Indicators:**

- Average RSI over the period
- Average Volatility (20-period standard deviation)

**Trading Signals Summary:**

- Total Buy Signals
- Total Hold Signals
- Total Sell Signals
- Golden Cross events
- Death Cross events

**Data Summary:**

- Total records analyzed
- Date range covered

### 6. Historical Charts Per Symbol

Each symbol gets:

- Full candlestick chart with Bollinger Bands
- Moving Averages (SMA 5, 20, 50)
- Volume bars
- RSI indicator with overbought/oversold levels
- Historical context for all technical indicators

### 7. Data Export

**CSV Export Feature:**

- Download button for historical data
- File naming: `historical_data_[start_date]_[end_date].csv`
- Includes all columns from the gold table
- Can be opened in Excel, Python pandas, or any analytics tool

**Raw Data Viewer:**

- Expandable section to view the full dataset
- Scrollable table with all historical records
- Useful for detailed inspection

## How to Use

### Accessing Historical Analysis

1. Open the dashboard: `streamlit run dashboard.py`
2. In the sidebar, select **"Historical Analysis"** from View Mode
3. Choose your desired time period or custom date range
4. Select symbols and/or sectors to analyze
5. Explore the various charts and metrics

### Example Use Cases

#### 1. Analyze Past Week Performance

```
View Mode: Historical Analysis
Time Period: Last 7 Days
Symbols: AAPL, MSFT, GOOGL
```

This will show:

- Price trends for the past week
- How many buy/sell signals were generated
- Performance metrics for each stock

#### 2. Compare Monthly Trends

```
View Mode: Historical Analysis
Time Period: Last 30 Days
Symbols: Select your portfolio stocks
```

Useful for:

- Identifying long-term trends
- Comparing stock performance
- Evaluating signal accuracy

#### 3. Historical Signal Analysis

```
View Mode: Historical Analysis
Time Period: All Time
```

Shows:

- Complete trading signal history
- Distribution of signals over entire dataset
- Long-term performance patterns

#### 4. Export for Further Analysis

```
1. Select Historical Analysis mode
2. Choose date range and filters
3. Scroll to "Export Data" section
4. Click "📥 Download CSV"
5. Open in Excel or Python for custom analysis
```

## Technical Details

### Data Source

- Reads from the same `stock_gold_realtime` Iceberg table
- Uses Spark SQL for efficient querying
- Applies date range filters at the query level for performance

### Performance Considerations

- Historical queries can be slower for large date ranges
- Limit symbol selection to 5 for optimal chart rendering
- Use predefined time periods instead of "All Time" for faster loading
- Auto-refresh is disabled by default in Historical mode

### Filtering Logic

- **Date filters**: Applied using event_time field
- **Symbol filters**: Optional, shows all if none selected
- **Sector filters**: Optional, applies to all symbols in sector
- **Combines with real-time filters**: Uses same sidebar controls

## Data Availability

The historical data available depends on:

1. When the pipeline started running
2. How much data has been ingested
3. Iceberg table retention settings

Check the sidebar in Historical mode to see:

- Earliest available date
- Latest available date
- Total records in the database

## Integration with Real-Time View

Both views use the same:

- Spark session (cached for efficiency)
- Symbol and sector filters
- Chart rendering functions
- Technical indicator calculations

You can seamlessly switch between views without losing filter selections.

## Future Enhancements

Potential additions:

- Backtesting framework for trading signals
- Performance attribution analysis
- Comparative benchmarking
- Alert history and accuracy tracking
- Machine learning model predictions on historical data
- Portfolio simulation based on historical signals

## Troubleshooting

### No Historical Data Showing

- Ensure the Gold layer processor is running: `python silver_to_gold_streaming.py`
- Check that data exists in the time range selected
- Verify MinIO is running and accessible

### Slow Performance

- Reduce the date range
- Limit number of symbols selected
- Use predefined time periods instead of custom ranges
- Ensure sufficient memory allocation for Spark

### Export Issues

- Large datasets may take time to generate CSV
- Check browser download settings
- Try reducing date range if file is too large

## Code Changes Summary

Files modified:

- `dashboard.py` - Added all historical analysis features

New functions added:

- `load_historical_data()` - Query data with date filters
- `get_date_range_stats()` - Get available date range
- `create_historical_trend_chart()` - Multi-symbol trend comparison
- `create_signal_distribution_chart()` - Signal distribution over time
- `calculate_historical_metrics()` - Performance metrics per symbol

Lines of code added: ~350 lines

## Conclusion

These historical analysis features provide powerful capabilities to:

- Review past trading signals
- Analyze stock performance over time
- Export data for custom analysis
- Make informed decisions based on historical patterns
- Validate the effectiveness of technical indicators

The features integrate seamlessly with the existing real-time dashboard while maintaining the same user experience and data source.

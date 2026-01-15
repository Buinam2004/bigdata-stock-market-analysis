"""
Real-time Stock Market Analytics Dashboard
Powered by Streamlit and Apache Iceberg
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc

# Page configuration
st.set_page_config(
    page_title="Real-Time Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .buy-signal {
        color: #00C851;
        font-weight: bold;
    }
    .sell-signal {
        color: #ff4444;
        font-weight: bold;
    }
    .hold-signal {
        color: #ffbb33;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Initialize Spark Session (cached to avoid recreation)
@st.cache_resource
def get_spark_session():
    """Initialize and cache Spark session"""
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")

    spark = (
        SparkSession.builder.appName("Streamlit-Dashboard")
        .master("local[2]")
        .config(
            "spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.367",
        )
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", ICEBERG_WAREHOUSE)
        .config("spark.sql.defaultCatalog", "local")
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.driver.memory", "1g")
        .config("spark.ui.enabled", "false")
        # Avoid port conflicts with other Spark apps
        .config("spark.driver.port", "0")  # Use random available port
        .config("spark.driver.blockManager.port", "0")  # Random BlockManager port
        .config("spark.port.maxRetries", "100")  # Try many ports if needed
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    spark.sql("USE stock_db")
    return spark


def load_gold_data(limit=1000):
    """Load latest data from Gold Iceberg table"""
    spark = get_spark_session()
    try:
        # Refresh table metadata to get latest snapshot
        spark.sql("REFRESH TABLE stock_gold_realtime")

        df = (
            spark.read.format("iceberg")
            .table("stock_gold_realtime")
            .orderBy(desc("event_time"))
            .limit(limit)
        )
        return df.toPandas()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def load_historical_data(start_date=None, end_date=None, symbols=None, sectors=None):
    """Load historical data from Gold Iceberg table with date range filters"""
    spark = get_spark_session()
    try:
        # Refresh table metadata to get latest snapshot
        spark.sql("REFRESH TABLE stock_gold_realtime")

        # Build query with filters
        query = "SELECT * FROM stock_gold_realtime WHERE 1=1"

        if start_date:
            query += f" AND event_time >= '{start_date}'"
        if end_date:
            query += f" AND event_time <= '{end_date}'"
        if symbols:
            symbol_list = "','".join(symbols)
            query += f" AND symbol IN ('{symbol_list}')"
        if sectors:
            sector_list = "','".join(sectors)
            query += f" AND sector IN ('{sector_list}')"

        query += " ORDER BY event_time DESC"

        df = spark.sql(query)
        return df.toPandas()
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        return pd.DataFrame()


def get_date_range_stats():
    """Get the date range of available data"""
    spark = get_spark_session()
    try:
        spark.sql("REFRESH TABLE stock_gold_realtime")
        query = """
        SELECT 
            MIN(event_time) as min_date,
            MAX(event_time) as max_date,
            COUNT(*) as total_records
        FROM stock_gold_realtime
        """
        result = spark.sql(query).toPandas()
        if not result.empty:
            return result.iloc[0].to_dict()
        return {"min_date": None, "max_date": None, "total_records": 0}
    except Exception as e:
        st.error(f"Error getting date range: {e}")
        return {"min_date": None, "max_date": None, "total_records": 0}


def load_latest_by_symbol(symbols=None):
    """Load the most recent record for each symbol"""
    spark = get_spark_session()
    try:
        # Refresh table metadata to get latest snapshot
        spark.sql("REFRESH TABLE stock_gold_realtime")

        query = """
        SELECT *
        FROM (
            SELECT *, 
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
            FROM stock_gold_realtime
        ) 
        WHERE rn = 1
        """
        if symbols:
            symbol_list = "','".join(symbols)
            query += f" AND symbol IN ('{symbol_list}')"

        df = spark.sql(query).drop("rn")
        return df.toPandas()
    except Exception as e:
        st.error(f"Error loading latest data: {e}")
        return pd.DataFrame()


def create_candlestick_chart(df, symbol):
    """Create candlestick chart with Bollinger Bands and moving averages"""
    df_symbol = df[df["symbol"] == symbol].sort_values("event_time")

    if df_symbol.empty:
        return None

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f"{symbol} - Price & Indicators", "Volume", "RSI"),
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df_symbol["event_time"],
            open=df_symbol["open"],
            high=df_symbol["high"],
            low=df_symbol["low"],
            close=df_symbol["close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # Bollinger Bands
    if "bb_upper" in df_symbol.columns:
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["bb_upper"],
                name="BB Upper",
                line=dict(color="gray", dash="dash", width=1),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["bb_lower"],
                name="BB Lower",
                line=dict(color="gray", dash="dash", width=1),
                fill="tonexty",
                fillcolor="rgba(128,128,128,0.1)",
            ),
            row=1,
            col=1,
        )

    # Moving Averages
    if "sma_5" in df_symbol.columns:
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["sma_5"],
                name="SMA 5",
                line=dict(color="blue", width=1),
            ),
            row=1,
            col=1,
        )

    if "sma_20" in df_symbol.columns:
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["sma_20"],
                name="SMA 20",
                line=dict(color="orange", width=1),
            ),
            row=1,
            col=1,
        )

    if "sma_50" in df_symbol.columns:
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["sma_50"],
                name="SMA 50",
                line=dict(color="red", width=1),
            ),
            row=1,
            col=1,
        )

    # Volume
    colors = [
        "red" if row["close"] < row["open"] else "green"
        for _, row in df_symbol.iterrows()
    ]
    fig.add_trace(
        go.Bar(
            x=df_symbol["event_time"],
            y=df_symbol["volume"],
            name="Volume",
            marker_color=colors,
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # RSI
    if "rsi_14" in df_symbol.columns:
        fig.add_trace(
            go.Scatter(
                x=df_symbol["event_time"],
                y=df_symbol["rsi_14"],
                name="RSI",
                line=dict(color="purple", width=2),
            ),
            row=3,
            col=1,
        )

        # RSI levels
        fig.add_hline(
            y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1
        )
        fig.add_hline(
            y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1
        )

    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        template="plotly_white",
    )

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)

    return fig


def create_macd_chart(df, symbol):
    """Create MACD chart"""
    df_symbol = df[df["symbol"] == symbol].sort_values("event_time")

    if df_symbol.empty or "macd" not in df_symbol.columns:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_symbol["event_time"],
            y=df_symbol["macd"],
            name="MACD",
            line=dict(color="blue", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_symbol["event_time"],
            y=df_symbol["macd_signal"],
            name="Signal",
            line=dict(color="red", width=2),
        )
    )

    colors = ["green" if val > 0 else "red" for val in df_symbol["macd_histogram"]]
    fig.add_trace(
        go.Bar(
            x=df_symbol["event_time"],
            y=df_symbol["macd_histogram"],
            name="Histogram",
            marker_color=colors,
        )
    )

    fig.update_layout(
        title=f"{symbol} - MACD",
        height=300,
        xaxis_title="Time",
        yaxis_title="MACD",
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def create_historical_trend_chart(df, symbols, metric="close"):
    """Create historical trend comparison chart for multiple symbols"""
    fig = go.Figure()

    for symbol in symbols:
        df_symbol = df[df["symbol"] == symbol].sort_values("event_time")
        if not df_symbol.empty and metric in df_symbol.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_symbol["event_time"],
                    y=df_symbol[metric],
                    name=symbol,
                    mode="lines",
                    line=dict(width=2),
                )
            )

    metric_names = {
        "close": "Price",
        "rsi_14": "RSI",
        "volume": "Volume",
        "price_change_pct": "Price Change %",
        "signal_score": "Signal Score",
    }

    fig.update_layout(
        title=f"Historical {metric_names.get(metric, metric)} Comparison",
        xaxis_title="Time",
        yaxis_title=metric_names.get(metric, metric),
        hovermode="x unified",
        template="plotly_white",
        height=500,
    )

    return fig


def create_signal_distribution_chart(df):
    """Create chart showing distribution of trading signals over time"""
    # Group by date and recommendation
    df["date"] = pd.to_datetime(df["event_time"]).dt.date
    signal_counts = (
        df.groupby(["date", "recommendation"]).size().reset_index(name="count")
    )

    fig = go.Figure()

    for rec in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]:
        data = signal_counts[signal_counts["recommendation"] == rec]
        if not data.empty:
            color = {
                "STRONG BUY": "#00C851",
                "BUY": "#7FD47F",
                "HOLD": "#ffbb33",
                "SELL": "#FF9999",
                "STRONG SELL": "#ff4444",
            }.get(rec, "gray")

            fig.add_trace(
                go.Bar(
                    x=data["date"],
                    y=data["count"],
                    name=rec,
                    marker_color=color,
                )
            )

    fig.update_layout(
        title="Historical Trading Signal Distribution",
        xaxis_title="Date",
        yaxis_title="Number of Signals",
        barmode="stack",
        template="plotly_white",
        height=400,
    )

    return fig


def calculate_historical_metrics(df, symbol):
    """Calculate historical performance metrics for a symbol"""
    df_symbol = df[df["symbol"] == symbol].sort_values("event_time")

    if df_symbol.empty:
        return {}

    metrics = {
        "total_records": len(df_symbol),
        "date_range": f"{df_symbol['event_time'].min()} to {df_symbol['event_time'].max()}",
        "price_start": df_symbol.iloc[0]["close"],
        "price_end": df_symbol.iloc[-1]["close"],
        "price_change": df_symbol.iloc[-1]["close"] - df_symbol.iloc[0]["close"],
        "price_change_pct": (
            (df_symbol.iloc[-1]["close"] - df_symbol.iloc[0]["close"])
            / df_symbol.iloc[0]["close"]
            * 100
        ),
        "price_high": df_symbol["high"].max(),
        "price_low": df_symbol["low"].min(),
        "avg_volume": df_symbol["volume"].mean(),
        "avg_rsi": df_symbol["rsi_14"].mean(),
        "buy_signals": len(
            df_symbol[df_symbol["recommendation"].isin(["BUY", "STRONG BUY"])]
        ),
        "sell_signals": len(
            df_symbol[df_symbol["recommendation"].isin(["SELL", "STRONG SELL"])]
        ),
        "hold_signals": len(df_symbol[df_symbol["recommendation"] == "HOLD"]),
        "golden_crosses": df_symbol["golden_cross"].sum(),
        "death_crosses": df_symbol["death_cross"].sum(),
        "volatility_avg": (
            df_symbol["volatility_20"].mean()
            if "volatility_20" in df_symbol.columns
            else 0
        ),
    }

    return metrics


# ========================================
# Main Dashboard
# ========================================

st.markdown(
    '<h1 class="main-header">📈 Real-Time Stock Market Analytics</h1>',
    unsafe_allow_html=True,
)
st.markdown("### Live Technical Analysis & Trading Signals")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Dashboard Settings")

    # View mode selection
    view_mode = st.radio(
        "View Mode", options=["Real-Time", "Historical Analysis"], index=0
    )

    auto_refresh = st.checkbox("🔄 Auto-refresh", value=(view_mode == "Real-Time"))
    if auto_refresh:
        refresh_interval = st.slider("Refresh interval (seconds)", 10, 60, 10)
    else:
        refresh_interval = 10

    st.markdown("---")
    st.header("📊 Data Filters")

    # Load available symbols
    latest_data = load_latest_by_symbol()
    if not latest_data.empty:
        all_symbols = sorted(latest_data["symbol"].unique())
        selected_symbols = st.multiselect(
            "Select Symbols",
            options=all_symbols,
            default=all_symbols[:5] if len(all_symbols) >= 5 else all_symbols,
        )

        all_sectors = sorted(latest_data["sector"].unique())
        selected_sectors = st.multiselect(
            "Select Sectors", options=all_sectors, default=all_sectors
        )
    else:
        st.warning("No data available yet")
        selected_symbols = []
        selected_sectors = []

    # Historical data filters
    if view_mode == "Historical Analysis":
        st.markdown("---")
        st.header("📅 Historical Data Range")

        # Get available date range
        date_stats = get_date_range_stats()

        if date_stats["min_date"] and date_stats["max_date"]:
            st.caption(f"Data available: {date_stats['total_records']:,} records")
            st.caption(f"From: {date_stats['min_date']}")
            st.caption(f"To: {date_stats['max_date']}")

            # Date range selector with minute-level granularity
            date_range_option = st.selectbox(
                "Time Period",
                options=[
                    "Last 5 Minutes",
                    "Last 10 Minutes",
                    "Last 15 Minutes",
                    "Last 30 Minutes",
                    "Last Hour",
                    "Last 2 Hours",
                    "Last 6 Hours",
                    "Last 24 Hours",
                    "Last 7 Days",
                    "Last 30 Days",
                    "All Time",
                    "Custom Range",
                ],
                index=4,  # Default to "Last Hour"
            )

            if date_range_option == "Custom Range":
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        value=pd.to_datetime(date_stats["min_date"]).date(),
                    )
                with col2:
                    end_date = st.date_input(
                        "End Date", value=pd.to_datetime(date_stats["max_date"]).date()
                    )
            else:
                end_date = datetime.now()
                if date_range_option == "Last 5 Minutes":
                    start_date = end_date - timedelta(minutes=5)
                elif date_range_option == "Last 10 Minutes":
                    start_date = end_date - timedelta(minutes=10)
                elif date_range_option == "Last 15 Minutes":
                    start_date = end_date - timedelta(minutes=15)
                elif date_range_option == "Last 30 Minutes":
                    start_date = end_date - timedelta(minutes=30)
                elif date_range_option == "Last Hour":
                    start_date = end_date - timedelta(hours=1)
                elif date_range_option == "Last 2 Hours":
                    start_date = end_date - timedelta(hours=2)
                elif date_range_option == "Last 6 Hours":
                    start_date = end_date - timedelta(hours=6)
                elif date_range_option == "Last 24 Hours":
                    start_date = end_date - timedelta(days=1)
                elif date_range_option == "Last 7 Days":
                    start_date = end_date - timedelta(days=7)
                elif date_range_option == "Last 30 Days":
                    start_date = end_date - timedelta(days=30)
                else:  # All Time
                    start_date = pd.to_datetime(date_stats["min_date"])
                    end_date = pd.to_datetime(date_stats["max_date"])
        else:
            st.warning("No historical data available")
            start_date = None
            end_date = None
            date_range_option = "All Time"

    st.markdown("---")
    st.info("💡 **Tip**: Switch between Real-Time and Historical views")

# Create placeholder for auto-refresh
placeholder = st.empty()

# Main loop
while True:
    with placeholder.container():

        # ========================================
        # HISTORICAL ANALYSIS VIEW
        # ========================================
        if view_mode == "Historical Analysis":
            st.subheader("📜 Historical Data Analysis")

            # Load historical data
            if start_date and end_date:
                with st.spinner("Loading historical data..."):
                    df_historical = load_historical_data(
                        start_date=start_date,
                        end_date=end_date,
                        symbols=selected_symbols if selected_symbols else None,
                        sectors=selected_sectors if selected_sectors else None,
                    )

                if df_historical.empty:
                    st.warning(
                        "No data available for the selected filters and date range."
                    )
                    if not auto_refresh:
                        break
                    time.sleep(refresh_interval)
                    continue

                # Display data summary
                st.markdown(f"**Date Range:** {start_date} to {end_date}")
                st.markdown(f"**Total Records:** {len(df_historical):,}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    unique_symbols = df_historical["symbol"].nunique()
                    st.metric("Symbols", unique_symbols)
                with col2:
                    total_buy = len(
                        df_historical[
                            df_historical["recommendation"].isin(["BUY", "STRONG BUY"])
                        ]
                    )
                    st.metric("🟢 Buy Signals", total_buy)
                with col3:
                    total_sell = len(
                        df_historical[
                            df_historical["recommendation"].isin(
                                ["SELL", "STRONG SELL"]
                            )
                        ]
                    )
                    st.metric("🔴 Sell Signals", total_sell)
                with col4:
                    avg_signal_score = df_historical["signal_score"].mean()
                    st.metric("Avg Signal Score", f"{avg_signal_score:.2f}")

                st.markdown("---")

                # ========================================
                # Historical Trend Charts
                # ========================================
                st.subheader("📈 Historical Trends")

                # Metric selector for comparison
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("#### Price & Indicator Comparison")
                with col2:
                    metric_choice = st.selectbox(
                        "Metric",
                        options=[
                            "close",
                            "rsi_14",
                            "volume",
                            "price_change_pct",
                            "signal_score",
                        ],
                        format_func=lambda x: {
                            "close": "Price",
                            "rsi_14": "RSI",
                            "volume": "Volume",
                            "price_change_pct": "Price Change %",
                            "signal_score": "Signal Score",
                        }.get(x, x),
                    )

                if selected_symbols:
                    trend_chart = create_historical_trend_chart(
                        df_historical, selected_symbols[:5], metric_choice
                    )
                    st.plotly_chart(trend_chart, use_container_width=True)
                else:
                    st.info("Select symbols from the sidebar to view trend comparisons")

                st.markdown("---")

                # ========================================
                # Signal Distribution Over Time
                # ========================================
                st.subheader("📊 Trading Signal Distribution")

                signal_dist_chart = create_signal_distribution_chart(df_historical)
                st.plotly_chart(signal_dist_chart, use_container_width=True)

                st.markdown("---")

                # ========================================
                # Historical Performance Metrics
                # ========================================
                st.subheader("📊 Performance Metrics by Symbol")

                if selected_symbols:
                    tabs = st.tabs(selected_symbols[:5])

                    for i, symbol in enumerate(selected_symbols[:5]):
                        with tabs[i]:
                            metrics = calculate_historical_metrics(
                                df_historical, symbol
                            )

                            if metrics:
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric(
                                        "Starting Price",
                                        f"${metrics['price_start']:.2f}",
                                    )
                                    st.metric(
                                        "Ending Price", f"${metrics['price_end']:.2f}"
                                    )
                                    st.metric(
                                        "Price Change",
                                        f"${metrics['price_change']:.2f}",
                                        delta=f"{metrics['price_change_pct']:.2f}%",
                                    )

                                with col2:
                                    st.metric(
                                        "Highest Price", f"${metrics['price_high']:.2f}"
                                    )
                                    st.metric(
                                        "Lowest Price", f"${metrics['price_low']:.2f}"
                                    )
                                    st.metric(
                                        "Avg Volume", f"{metrics['avg_volume']:,.0f}"
                                    )

                                with col3:
                                    st.metric("Avg RSI", f"{metrics['avg_rsi']:.1f}")
                                    st.metric(
                                        "Volatility (Avg)",
                                        f"{metrics['volatility_avg']:.2f}",
                                    )
                                    st.metric(
                                        "Total Records", f"{metrics['total_records']:,}"
                                    )

                                st.markdown("#### Trading Signals Summary")
                                col1, col2, col3, col4, col5 = st.columns(5)
                                with col1:
                                    st.metric("🟢 Buy", metrics["buy_signals"])
                                with col2:
                                    st.metric("🟡 Hold", metrics["hold_signals"])
                                with col3:
                                    st.metric("🔴 Sell", metrics["sell_signals"])
                                with col4:
                                    st.metric(
                                        "✅ Golden Cross", metrics["golden_crosses"]
                                    )
                                with col5:
                                    st.metric(
                                        "❌ Death Cross", metrics["death_crosses"]
                                    )

                                # Historical chart for this symbol
                                st.markdown("#### Price History with Indicators")
                                symbol_data = df_historical[
                                    df_historical["symbol"] == symbol
                                ]
                                if not symbol_data.empty:
                                    hist_chart = create_candlestick_chart(
                                        symbol_data, symbol
                                    )
                                    if hist_chart:
                                        st.plotly_chart(
                                            hist_chart, use_container_width=True
                                        )
                            else:
                                st.info(f"No historical data available for {symbol}")
                else:
                    st.info("Select symbols from the sidebar to view detailed metrics")

                st.markdown("---")

                # ========================================
                # Export Historical Data
                # ========================================
                st.subheader("💾 Export Data")

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("Download the historical data for further analysis")
                with col2:
                    csv_data = df_historical.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"historical_data_{start_date}_{end_date}.csv",
                        mime="text/csv",
                    )

                # Raw data table
                with st.expander("📋 View Raw Historical Data"):
                    st.dataframe(df_historical, use_container_width=True, height=400)

            else:
                st.warning("Please select a valid date range")

        # ========================================
        # REAL-TIME VIEW (Original functionality)
        # ========================================
        else:
            # Load fresh data
            df_all = load_gold_data(limit=5000)
            df_latest = load_latest_by_symbol(
                selected_symbols if selected_symbols else None
            )

            if df_latest.empty:
                st.warning(
                    "⏳ Waiting for data... Make sure the Gold layer processor is running."
                )
                time.sleep(5)
                continue

            # Filter by sector
            if selected_sectors:
                df_latest = df_latest[df_latest["sector"].isin(selected_sectors)]

            # ========================================
            # Key Metrics Row
            # ========================================
            st.subheader("📊 Market Overview")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                total_stocks = len(df_latest)
                st.metric("Total Stocks", total_stocks)

            with col2:
                buy_count = len(
                    df_latest[df_latest["recommendation"].isin(["BUY", "STRONG BUY"])]
                )
                st.metric("🟢 Buy Signals", buy_count)

            with col3:
                sell_count = len(
                    df_latest[df_latest["recommendation"].isin(["SELL", "STRONG SELL"])]
                )
                st.metric("🔴 Sell Signals", sell_count)

            with col4:
                hold_count = len(df_latest[df_latest["recommendation"] == "HOLD"])
                st.metric("🟡 Hold Signals", hold_count)

            with col5:
                avg_rsi = df_latest["rsi_14"].mean()
                st.metric("Avg RSI", f"{avg_rsi:.1f}")

            st.markdown("---")

            # ========================================
            # Trading Signals Table
            # ========================================
            st.subheader("🎯 Active Trading Signals")

            # Create signals table
            signals_df = df_latest[
                [
                    "symbol",
                    "sector",
                    "close",
                    "price_change_pct",
                    "rsi_14",
                    "signal_score",
                    "recommendation",
                    "event_time",
                ]
            ].copy()

            signals_df["price_change_pct"] = signals_df["price_change_pct"].round(2)
            signals_df["rsi_14"] = signals_df["rsi_14"].round(1)
            signals_df["close"] = signals_df["close"].round(2)

            # Color code recommendations
            def highlight_recommendation(val):
                if val in ["STRONG BUY", "BUY"]:
                    return "background-color: #d4edda; color: #155724"
                elif val in ["STRONG SELL", "SELL"]:
                    return "background-color: #f8d7da; color: #721c24"
                else:
                    return "background-color: #fff3cd; color: #856404"

            styled_df = signals_df.style.applymap(
                highlight_recommendation, subset=["recommendation"]
            )

            st.dataframe(styled_df, use_container_width=True, height=300)

            st.markdown("---")

            # ========================================
            # Detailed Analysis per Symbol
            # ========================================
            st.subheader("📈 Technical Analysis")

            if selected_symbols:
                # Create tabs for each symbol
                tabs = st.tabs(selected_symbols[:5])  # Limit to 5 tabs

                for i, symbol in enumerate(selected_symbols[:5]):
                    with tabs[i]:
                        # Symbol info
                        symbol_data = df_latest[df_latest["symbol"] == symbol].iloc[0]

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric(
                                "Current Price",
                                f"${symbol_data['close']:.2f}",
                                f"{symbol_data['price_change_pct']:.2f}%",
                            )
                        with col2:
                            st.metric("RSI (14)", f"{symbol_data['rsi_14']:.1f}")
                        with col3:
                            st.metric("Signal Score", symbol_data["signal_score"])
                        with col4:
                            rec_color = (
                                "🟢"
                                if symbol_data["recommendation"]
                                in ["BUY", "STRONG BUY"]
                                else (
                                    "🔴"
                                    if symbol_data["recommendation"]
                                    in ["SELL", "STRONG SELL"]
                                    else "🟡"
                                )
                            )
                            st.metric(
                                "Recommendation",
                                f"{rec_color} {symbol_data['recommendation']}",
                            )

                        # Technical indicators
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Moving Averages**")
                            st.write(f"• SMA 5:  ${symbol_data['sma_5']:.2f}")
                            st.write(f"• SMA 20: ${symbol_data['sma_20']:.2f}")
                            st.write(f"• SMA 50: ${symbol_data['sma_50']:.2f}")

                        with col2:
                            st.write("**Signals**")
                            st.write(
                                f"• Golden Cross: {'✅' if symbol_data['golden_cross'] else '❌'}"
                            )
                            st.write(
                                f"• Death Cross: {'✅' if symbol_data['death_cross'] else '❌'}"
                            )
                            st.write(
                                f"• RSI Oversold: {'✅' if symbol_data['rsi_oversold'] else '❌'}"
                            )
                            st.write(
                                f"• RSI Overbought: {'✅' if symbol_data['rsi_overbought'] else '❌'}"
                            )

                        # Charts
                        st.markdown("#### Price Chart with Indicators")
                        chart = create_candlestick_chart(df_all, symbol)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)

                        st.markdown("#### MACD Indicator")
                        macd_chart = create_macd_chart(df_all, symbol)
                        if macd_chart:
                            st.plotly_chart(macd_chart, use_container_width=True)
            else:
                st.info("👈 Select symbols from the sidebar to view detailed analysis")

            # ========================================
            # Sector Performance
            # ========================================
            st.markdown("---")
            st.subheader("🏢 Sector Performance")

            sector_perf = (
                df_latest.groupby("sector")
                .agg(
                    {
                        "close": "mean",
                        "price_change_pct": "mean",
                        "volume": "sum",
                        "rsi_14": "mean",
                        "symbol": "count",
                    }
                )
                .round(2)
            )
            sector_perf.columns = [
                "Avg Price",
                "Avg Change %",
                "Total Volume",
                "Avg RSI",
                "Stock Count",
            ]

            st.dataframe(sector_perf, use_container_width=True)

            # Sector chart
            fig_sector = go.Figure(
                data=[
                    go.Bar(
                        x=sector_perf.index,
                        y=sector_perf["Avg Change %"],
                        marker_color=[
                            "green" if x > 0 else "red"
                            for x in sector_perf["Avg Change %"]
                        ],
                        text=sector_perf["Avg Change %"],
                        textposition="outside",
                    )
                ]
            )
            fig_sector.update_layout(
                title="Sector Performance (%)",
                xaxis_title="Sector",
                yaxis_title="Average Change %",
                height=400,
                template="plotly_white",
            )
            st.plotly_chart(fig_sector, use_container_width=True)

        # Footer
        st.markdown("---")
        st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(
            "⚡ Data source: Apache Iceberg (Gold Layer) | 🔄 Real-time streaming from Silver layer"
        )

    # Auto-refresh logic
    if not auto_refresh:
        break

    time.sleep(refresh_interval)

    # For manual refresh, use this to break out:
    if not auto_refresh:
        break

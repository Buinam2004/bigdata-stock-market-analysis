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

    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 10, 60, 10)

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

    st.markdown("---")
    st.info("💡 **Tip**: Select specific symbols for detailed analysis")

# Create placeholder for auto-refresh
placeholder = st.empty()

# Main loop
while True:
    with placeholder.container():
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
                            if symbol_data["recommendation"] in ["BUY", "STRONG BUY"]
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
                        "green" if x > 0 else "red" for x in sector_perf["Avg Change %"]
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

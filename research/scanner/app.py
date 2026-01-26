"""
Small-Cap Scanner Pro - Real-Time Dashboard

Professional-grade UI with:
- Auto-refresh (configurable 5-60 sec)
- Multi-channel alerts (desktop, browser, sound)
- Candidate tracking (first seen timestamps)
- Clean, modern dark theme
"""

import streamlit as st
import pandas as pd
import importlib
import time
from datetime import datetime
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
import gap_hunter
importlib.reload(gap_hunter)
from gap_hunter import fetch_market_gainers
from news_bot import analyze_news

# Page Config
st.set_page_config(
    page_title="Small-Cap Scanner Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
    <style>
    /* Main Container */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1E2530 0%, #262D3D 100%);
        border: 1px solid #00D4AA20;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    div[data-testid="metric-container"]:hover {
        border-color: #00D4AA40;
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    /* Headers */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #00D4AA, #00FFC6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }
    
    h2, h3 {
        color: #00D4AA !important;
        font-weight: 600 !important;
    }
    
    /* Status Bar */
    .status-bar {
        background: #1E2530;
        border: 1px solid #00D4AA30;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        margin: 1rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .status-running {
        color: #4ADE80;
        font-weight: 600;
    }
    
    .status-stopped {
        color: #9CA3AF;
        font-weight: 600;
    }
    
    /* Tables */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0E1117;
        border-right: 1px solid #00D4AA20;
    }
    
    /* Dividers */
    hr {
        border-color: #00D4AA20 !important;
        margin: 1.5rem 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scanner' not in st.session_state:
    st.session_state.scanner = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'last_results' not in st.session_state:
    st.session_state.last_results = None
if 'last_news' not in st.session_state:
    st.session_state.last_news = None
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'new_candidates' not in st.session_state:
    st.session_state.new_candidates = set()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ SCANNER CONTROL")
    
    # Start/Stop Buttons
    col1, col2 = st.columns(2)
    with col1:
        start = st.button("▶️ START", type="primary", use_container_width=True)
    with col2:
        stop = st.button("⏹️ STOP", use_container_width=True)
    
    if start:
        st.session_state.running = True
        st.success("Scanner started!")
        
    if stop:
        st.session_state.running = False
        st.warning("Scanner stopped")
    
    st.divider()
    
    # Scan Settings
    with st.expander("🔄 SCAN SETTINGS", expanded=True):
        auto_refresh = st.checkbox("Auto-Refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (sec)", 5, 60, 15, 5)
    
    st.divider()
    
    # Filter Settings
    with st.expander("🎯 FILTERS", expanded=True):
        min_price = st.number_input("Min Price ($)", value=1.0, step=0.5, format="%.1f")
        max_price = st.number_input("Max Price ($)", value=20.0, step=1.0, format="%.1f")
        min_gap = st.slider("Min Day Change (%)", 1, 50, 2)
        max_float = st.number_input("Max Float (M)", value=80.0, step=10.0, format="%.1f")
        min_rvol = st.slider("Min RVOL", 0.5, 10.0, 2.0, 0.5)
    
    st.divider()
    
    # Alert Settings
    with st.expander("🔔 ALERTS", expanded=False):
        desktop_alerts = st.checkbox("Desktop Notifications", value=True)
        browser_alerts = st.checkbox("Browser Toasts", value=True)
        sound_alerts = st.checkbox("Sound Alerts", value=False)
    
    st.divider()
    
    # Info
    st.caption(f"**Status**: {'🟢 RUNNING' if st.session_state.running else '🔴 STOPPED'}")
    st.caption(f"**Refresh**: Every {refresh_interval}s")
    if st.session_state.last_scan_time:
        st.caption(f"**Last Scan**: {st.session_state.last_scan_time.strftime('%I:%M:%S %p')}")

# Main Area
st.title("🚀 SMALL-CAP SCANNER PRO")
st.markdown("### Real-Time Momentum Scanner with News Catalyst Filter")

# Status Bar
if st.session_state.running:
    status_html = f"""
    <div class="status-bar">
        <span class="status-running">● SCANNING</span>
        <span style="color: #9CA3AF;">Every {refresh_interval}s</span>
        <span style="color: #9CA3AF;">{datetime.now().strftime('%I:%M:%S %p')}</span>
    </div>
    """
else:
    status_html = """
    <div class="status-bar">
        <span class="status-stopped">○ STOPPED</span>
        <span style="color: #9CA3AF;">Click START to begin</span>
    </div>
    """
st.markdown(status_html, unsafe_allow_html=True)

# Scan execution
if st.session_state.running or start:
    with st.spinner("🔍 Scanning market..."):
        try:
            # Force reload
            importlib.reload(gap_hunter)
            from gap_hunter import fetch_market_gainers
            
            df = fetch_market_gainers(
                min_price=min_price,
                max_price=max_price,
                min_gap_percent=min_gap,
                max_float_million=max_float,
                min_rvol=min_rvol
            )
            
            st.session_state.last_results = df
            st.session_state.last_scan_time = datetime.now()
            
            # Check for new candidates
            if not df.empty:
                current_symbols = set(df['Ticker'].tolist())
                if st.session_state.new_candidates:
                    new_symbols = current_symbols - st.session_state.new_candidates
                    if new_symbols and browser_alerts:
                        for symbol in new_symbols:
                            st.toast(f"🚀 NEW: {symbol}", icon="🎯")
                st.session_state.new_candidates = current_symbols
                
                # Trigger news analysis
                news_results = []
                for ticker in df['Ticker'].tolist()[:10]:  # Top 10 only
                    analysis = analyze_news(ticker)
                    news_results.append({
                        "Ticker": ticker,
                        "Verdict": analysis['verdict'],
                        "Headline": analysis['headline'],
                        "URL": analysis['url'],
                        "publisher": analysis.get('publisher', 'Unknown')
                    })
                
                # Sort by priority
                def get_priority(verdict):
                    if "💀" in verdict or "🔥" in verdict: return 0
                    if "☁️" in verdict: return 1
                    return 2
                
                news_df = pd.DataFrame(news_results)
                if not news_df.empty:
                    news_df['Priority'] = news_df['Verdict'].apply(get_priority)
                    news_df = news_df.sort_values(by='Priority').drop(columns=['Priority'])
                
                st.session_state.last_news = news_df
                
        except Exception as e:
            st.error(f"❌ Scan error: {e}")

# Display results
if st.session_state.last_results is not None:
    results = st.session_state.last_results
    
    if results.empty:
        st.warning("⚠️ No candidates found matching criteria")
    else:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("**Candidates**", len(results), help="Total symbols found")
        
        with col2:
            top = results.iloc[0]
            st.metric("**Top Gainer**", f"{top['Ticker']}", f"+{top['Gap%']:.1f}%")
        
        with col3:
            st.metric("**Highest Score**", f"{results['Score'].max():.1f}", help="Algo-Shadow score")
        
        with col4:
            # Count new candidates in last scan
            new_count = len(st.session_state.new_candidates) if hasattr(st.session_state, 'new_candidates') else 0
            st.metric("**Tracked**", new_count, help="Active candidates")
        
        st.divider()
        
        # Candidates Table
        st.subheader("📊 CANDIDATES")
        
        # Format display
        display_df = results.copy()
        
        # Add FirstSeen if it exists
        if 'FirstSeen' in display_df.columns:
            display_df['FirstSeen'] = pd.to_datetime(display_df['FirstSeen']).dt.strftime('%H:%M:%S')
            cols_to_show = ['Ticker', 'Price', 'Gap%', 'Volume', 'RVOL', 'Float (M)', 'Score', 'FirstSeen']
        else:
            cols_to_show = ['Ticker', 'Price', 'Gap%', 'Volume', 'RVOL', 'Float (M)', 'Score']
        
        # Filter to existing columns
        cols_to_show = [c for c in cols_to_show if c in display_df.columns]
        
        st.dataframe(
            display_df[cols_to_show],
            column_config={
                "Ticker": "Ticker",
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Gap%": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                "RVOL": st.column_config.NumberColumn("RVOL", format="%.2fx"),
                "Float (M)": st.column_config.NumberColumn("Float (M)", format="%.2f M"),
                "Score": st.column_config.NumberColumn("Score", format="%.2f"),
                "FirstSeen": "First Seen",
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        
        # News Section
        st.subheader("📰 CATALYST ANALYSIS")
        st.caption("News drives momentum - All candidates have recent news (24h filter)")
        
        if st.session_state.last_news is not None and not st.session_state.last_news.empty:
            news_df = st.session_state.last_news.copy()
            
            # Display as Streamlit dataframe
            st.dataframe(
                news_df[['Ticker', 'Verdict', 'Headline', 'URL']],
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "Verdict": st.column_config.TextColumn("Verdict", width="medium"),
                    "Headline": st.column_config.TextColumn("Headline", width="large"),
                    "URL": st.column_config.LinkColumn("Link", width="small"),
                },
                use_container_width=True,
                hide_index=True
            )


else:
    st.info("👈 Configure settings and click **START** to begin scanning")

# Auto-refresh
if st.session_state.running and auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.divider()
st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

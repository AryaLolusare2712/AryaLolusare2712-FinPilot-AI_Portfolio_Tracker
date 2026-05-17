"""
FinPilot — AI Portfolio Tracker
NSE/BSE Stocks + Crypto | Powered by Gemini AI
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Secrets (Streamlit Cloud) ──────────────────────────────────
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

from core.portfolio import (add_holding, remove_holding,
                             load_portfolio, get_transaction_history)
from core.analyzer import get_full_portfolio_data, get_allocation_data
from agents.llm_agent import LLMAgent
from agents.stock_agent import StockAgent
from agents.crypto_agent import CryptoAgent
from agents.news_agent import NewsAgent

# ── Page config (must be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="FinPilot — AI Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #080c10; }
[data-testid="stSidebar"] { background-color: #0d1218; border-right: 1px solid #1a2535; }
[data-testid="stHeader"] { background-color: #080c10; }

[data-testid="metric-container"] {
    background: #0d1218;
    border: 1px solid #1a2535;
    border-radius: 14px;
    padding: 16px 20px;
}

.stButton > button[kind="primary"] {
    background: rgba(0,229,160,.12);
    border: 1px solid rgba(0,229,160,.3);
    color: #00e5a0;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(0,229,160,.2);
    border-color: #00e5a0;
    box-shadow: 0 0 16px rgba(0,229,160,.25);
}

.stTabs [data-baseweb="tab-list"] { background: #0d1218; border-bottom: 1px solid #1a2535; gap: 4px; }
.stTabs [data-baseweb="tab"] { color: #4a6278; background: transparent; font-size: 13px; }
.stTabs [aria-selected="true"] { color: #00e5a0 !important; border-bottom: 2px solid #00e5a0 !important; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #080c10 !important;
    border: 1px solid #1a2535 !important;
    color: #dde6f0 !important;
    border-radius: 8px !important;
}

.chat-msg-user {
    background: #111922; border: 1px solid #243347;
    border-radius: 10px; padding: 12px 16px;
    margin: 6px 0; margin-left: 20%;
    color: #dde6f0; font-size: 14px; line-height: 1.6;
}
.chat-msg-bot {
    background: rgba(0,229,160,.05);
    border: 1px solid rgba(0,229,160,.12);
    border-left: 2px solid #00e5a0;
    border-radius: 10px; padding: 12px 16px;
    margin: 6px 0; margin-right: 20%;
    color: #dde6f0; font-size: 14px; line-height: 1.6;
}

.news-card {
    background: #0d1218; border: 1px solid #1a2535;
    border-radius: 14px; padding: 18px;
    margin-bottom: 10px;
}
.news-title { color: #dde6f0; font-size: 15px; font-weight: 600;
    text-decoration: none; line-height: 1.45; }
.news-meta { color: #4a6278; font-size: 11px; margin: 5px 0 8px; font-family: monospace; }
.news-badge { background: rgba(79,158,255,.1); border: 1px solid rgba(79,158,255,.2);
    color: #4f9eff; font-size: 9px; padding: 2px 8px;
    border-radius: 4px; margin-right: 6px; font-family: monospace; }
.news-desc { color: #8ba3bf; font-size: 13px; line-height: 1.6; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Initialize agents (cached) ─────────────────────────────────
@st.cache_resource
def init_agents():
    return {
        "llm":    LLMAgent(model="gemini-2.5-flash"),
        "stock":  StockAgent(),
        "crypto": CryptoAgent(),
        "news":   NewsAgent(),
    }

agents       = init_agents()
llm          = agents["llm"]
stock_agent  = agents["stock"]
crypto_agent = agents["crypto"]
news_agent   = agents["news"]
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY", "")

# ── Session state ──────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Helpers ────────────────────────────────────────────────────
def fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}"

@st.cache_data(ttl=60)
def fetch_portfolio():
    return get_full_portfolio_data()

@st.cache_data(ttl=300)
def fetch_news():
    if NEWS_API_KEY:
        return news_agent.get_market_news(api_key=NEWS_API_KEY)[:10]
    articles = news_agent.get_crypto_news()
    if not articles:
        articles = news_agent.get_market_news()
    return articles[:10]

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:6px 0 18px">
      <div style="width:32px;height:32px;border-radius:8px;
        background:linear-gradient(135deg,#00e5a0,#00b87a);
        display:flex;align-items:center;justify-content:center;
        font-size:15px;font-weight:900;color:#060e09;
        box-shadow:0 0 16px rgba(0,229,160,.3);">P</div>
      <div>
        <div style="font-size:15px;font-weight:800;color:#dde6f0;font-family:sans-serif">FinPilot</div>
        <div style="font-size:9px;color:#00e5a0;font-family:monospace;letter-spacing:.06em;margin-bottom:2px">AI Portfolio Tracker</div>
        <div style="font-size:10px;color:#4a6278;font-family:monospace">{datetime.now().strftime("%d %b %Y")}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    ai_ok = llm.available
    st.markdown(f"""
    <div style="font-size:10px;font-family:monospace;color:#4a6278;margin-bottom:4px">
      <span style="color:{'#00e5a0' if ai_ok else '#ffb830'}">●</span>
      Gemini AI · {'Ready' if ai_ok else 'Offline — add GEMINI_API_KEY'}
    </div>
    <div style="font-size:10px;font-family:monospace;color:#4a6278;margin-bottom:4px">
      <span style="color:#00e5a0">●</span> NSE/BSE · yfinance
    </div>
    <div style="font-size:10px;font-family:monospace;color:#4a6278;margin-bottom:16px">
      <span style="color:#4f9eff">●</span> Crypto · CoinGecko
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                'color:#4a6278;font-family:monospace;margin-bottom:8px">HOLDINGS</div>',
                unsafe_allow_html=True)

    portfolio_raw = load_portfolio()
    stocks_held   = portfolio_raw.get("stocks", {})
    crypto_held   = portfolio_raw.get("crypto", {})

    if not stocks_held and not crypto_held:
        st.markdown('<div style="color:#4a6278;font-size:12px">No holdings yet</div>',
                    unsafe_allow_html=True)
    else:
        for sym, h in stocks_held.items():
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:6px 0">
              <div style="width:28px;height:28px;border-radius:7px;flex-shrink:0;
                background:rgba(79,158,255,.15);border:1px solid rgba(79,158,255,.2);
                display:flex;align-items:center;justify-content:center;
                font-size:8px;font-family:monospace;color:#4f9eff;font-weight:700">{sym[:3]}</div>
              <div>
                <div style="font-family:monospace;font-size:12px;font-weight:600;color:#dde6f0">{sym}</div>
                <div style="font-size:10px;color:#4a6278">{h['quantity']} shares</div>
              </div>
            </div>""", unsafe_allow_html=True)

        for sym, h in crypto_held.items():
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:6px 0">
              <div style="width:28px;height:28px;border-radius:7px;flex-shrink:0;
                background:rgba(0,229,160,.12);border:1px solid rgba(0,229,160,.2);
                display:flex;align-items:center;justify-content:center;
                font-size:8px;font-family:monospace;color:#00e5a0;font-weight:700">{sym[:3]}</div>
              <div>
                <div style="font-family:monospace;font-size:12px;font-weight:600;color:#dde6f0">{sym}</div>
                <div style="font-size:10px;color:#4a6278">{h['quantity']} coins</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    txn_count = len(portfolio_raw.get("transactions", []))
    st.markdown(f'<div style="font-size:10px;font-family:monospace;color:#4a6278">'
                f'Transactions: <span style="color:#dde6f0">{txn_count}</span></div>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab_overview, tab_add, tab_prices, tab_ai, tab_chat, tab_news, tab_txn = st.tabs([
    "📊 Overview",
    "➕ Add / Remove",
    "📈 Live Prices",
    "🤖 AI Analysis",
    "💬 AI Chat",
    "📰 News",
    "📋 Transactions",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════
with tab_overview:
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            fetch_portfolio.clear()
            st.rerun()

    with st.spinner("Fetching live prices…"):
        data = fetch_portfolio()

    summary = data.get("summary", {})
    stocks  = data.get("stocks", [])
    crypto  = data.get("crypto", [])

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("💰 Total Invested", fmt_inr(summary.get("total_invested", 0)))
    with k2:
        st.metric("📈 Current Value", fmt_inr(summary.get("total_current_value", 0)))
    with k3:
        pnl     = summary.get("total_pnl", 0)
        pnl_pct = summary.get("total_pnl_pct", 0)
        st.metric("⚡ Total P&L", fmt_inr(pnl), delta=f"{pnl_pct:+.2f}%")
    with k4:
        all_assets = stocks + crypto
        best = max(all_assets, key=lambda x: x.get("pnl_pct", 0)) if all_assets else None
        st.metric("🏆 Best Performer",
                  best["symbol"] if best else "—",
                  delta=f"{best['pnl_pct']:+.2f}%" if best else None)

    st.markdown("---")

    # Charts
    alloc = get_allocation_data(data)
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:8px">● ALLOCATION BY VALUE</div>',
                    unsafe_allow_html=True)
        if alloc["values"]:
            fig = go.Figure(go.Pie(
                labels=alloc["labels"],
                values=alloc["values"],
                marker=dict(colors=alloc["colors"],
                            line=dict(color="#080c10", width=2)),
                hole=0.45,
                textinfo="label+percent",
                textfont=dict(size=11, color="#dde6f0"),
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8ba3bf"),
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="color:#4a6278;text-align:center;padding:60px 0;font-size:13px">'
                        'Add holdings to see allocation</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:8px">● P&L PER ASSET</div>',
                    unsafe_allow_html=True)
        if all_assets:
            syms   = [a["symbol"] for a in all_assets]
            pnls   = [a.get("pnl", 0) for a in all_assets]
            colors = ["#00e5a0" if p >= 0 else "#ff4d6d" for p in pnls]
            fig2 = go.Figure(go.Bar(
                x=syms, y=pnls,
                marker_color=colors,
                text=[fmt_inr(p) for p in pnls],
                textposition="outside",
                textfont=dict(size=10, color="#8ba3bf"),
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8ba3bf"),
                xaxis=dict(color="#4a6278", gridcolor="#1a2535"),
                yaxis=dict(color="#4a6278", gridcolor="#1a2535"),
                margin=dict(t=30, b=10, l=10, r=10),
                height=260,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown('<div style="color:#4a6278;text-align:center;padding:60px 0;font-size:13px">'
                        'No holdings to chart</div>', unsafe_allow_html=True)

    # Stock table
    if stocks:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin:16px 0 8px">● STOCKS</div>',
                    unsafe_allow_html=True)
        rows = []
        for s in stocks:
            rows.append({
                "Symbol":        s["symbol"],
                "Name":          s.get("name", s["symbol"]),
                "Qty":           s["quantity"],
                "Buy Price":     fmt_inr(s["buy_price"]),
                "Current Price": fmt_inr(s["current_price"]),
                "Invested":      fmt_inr(s.get("invested", 0)),
                "Value":         fmt_inr(s.get("current_value", 0)),
                "P&L":           fmt_inr(s.get("pnl", 0)),
                "P&L %":         f"{s.get('pnl_pct', 0):+.2f}%",
                "Day Chg %":     f"{s.get('change_pct', 0):+.2f}%",
                "Exchange":      s.get("exchange", "NSE"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Crypto table
    if crypto:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin:16px 0 8px">● CRYPTO</div>',
                    unsafe_allow_html=True)
        rows = []
        for c in crypto:
            rows.append({
                "Symbol":        c["symbol"],
                "Qty":           c["quantity"],
                "Buy Price":     fmt_inr(c["buy_price"]),
                "Current Price": fmt_inr(c["current_price"]),
                "Invested":      fmt_inr(c.get("invested", 0)),
                "Value":         fmt_inr(c.get("current_value", 0)),
                "P&L":           fmt_inr(c.get("pnl", 0)),
                "P&L %":         f"{c.get('pnl_pct', 0):+.2f}%",
                "24h Chg %":     f"{c.get('change_pct', 0):+.2f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if not stocks and not crypto:
        st.info("📭 Portfolio is empty. Go to **Add / Remove** to add your first holding.")

    errors = data.get("errors", [])
    if errors:
        with st.expander(f"⚠️ {len(errors)} data error(s)", expanded=False):
            for e in errors:
                st.caption(e)

# ══════════════════════════════════════════════════════════════
# TAB 2 — ADD / REMOVE
# ══════════════════════════════════════════════════════════════
with tab_add:
    col_left, col_right = st.columns(2)

    # Add Stock
    with col_left:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● ADD STOCK (NSE)</div>',
                    unsafe_allow_html=True)

        nse_chips = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO",
                     "SBIN", "TATAMOTORS", "ITC", "BAJFINANCE", "ICICIBANK"]
        selected_stock = st.selectbox("Quick select NSE symbol",
                                      ["— type below —"] + nse_chips, key="stock_chip")

        stock_sym = st.text_input(
            "NSE Symbol",
            value=selected_stock if selected_stock != "— type below —" else "",
            placeholder="e.g. RELIANCE", key="stock_sym_input"
        ).upper().strip()
        stock_qty   = st.number_input("Quantity (shares)", min_value=0.0001,
                                      step=1.0, format="%.4f", key="stock_qty")
        stock_price = st.number_input("Buy Price (₹)", min_value=0.01,
                                      step=10.0, format="%.2f", key="stock_price")

        if st.button("➕ Add Stock", type="primary", use_container_width=True):
            if not stock_sym:
                st.error("NSE symbol is required")
            elif stock_qty <= 0:
                st.error("Quantity must be positive")
            elif stock_price <= 0:
                st.error("Price must be positive")
            else:
                try:
                    add_holding("stocks", stock_sym, stock_qty, stock_price)
                    fetch_portfolio.clear()
                    st.success(f"✅ {stock_sym} added — {stock_qty} shares @ {fmt_inr(stock_price)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # Add Crypto
    with col_right:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● ADD CRYPTO</div>',
                    unsafe_allow_html=True)

        crypto_chips = ["BTC", "ETH", "SOL", "BNB", "XRP",
                        "ADA", "DOGE", "MATIC", "DOT", "AVAX"]
        selected_crypto = st.selectbox("Quick select crypto",
                                       ["— type below —"] + crypto_chips, key="crypto_chip")

        crypto_sym = st.text_input(
            "Crypto Symbol",
            value=selected_crypto if selected_crypto != "— type below —" else "",
            placeholder="e.g. BTC", key="crypto_sym_input"
        ).upper().strip()
        crypto_qty   = st.number_input("Quantity (coins)", min_value=0.000001,
                                       step=0.01, format="%.6f", key="crypto_qty")
        crypto_price = st.number_input("Buy Price (₹)", min_value=0.01,
                                       step=100.0, format="%.2f", key="crypto_price")

        if st.button("➕ Add Crypto", type="primary", use_container_width=True):
            if not crypto_sym:
                st.error("Crypto symbol is required")
            elif crypto_qty <= 0:
                st.error("Quantity must be positive")
            elif crypto_price <= 0:
                st.error("Price must be positive")
            else:
                try:
                    add_holding("crypto", crypto_sym, crypto_qty, crypto_price)
                    fetch_portfolio.clear()
                    st.success(f"✅ {crypto_sym} added — {crypto_qty} coins @ {fmt_inr(crypto_price)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")

    # Remove Holdings
    st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                'color:#ff4d6d;font-family:monospace;margin-bottom:12px">● REMOVE HOLDING</div>',
                unsafe_allow_html=True)

    portfolio_raw2 = load_portfolio()
    all_symbols = (
        [("stocks", s) for s in portfolio_raw2.get("stocks", {})] +
        [("crypto", s) for s in portfolio_raw2.get("crypto", {})]
    )

    if not all_symbols:
        st.info("No holdings to remove.")
    else:
        r1, r2 = st.columns([3, 1])
        with r1:
            remove_choice = st.selectbox(
                "Select holding to remove",
                options=[f"{s} ({t})" for t, s in all_symbols],
                key="remove_select"
            )
        with r2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Remove", type="primary", use_container_width=True):
                labels = [f"{s} ({t})" for t, s in all_symbols]
                idx = labels.index(remove_choice)
                asset_type, symbol = all_symbols[idx]
                try:
                    remove_holding(asset_type, symbol)
                    fetch_portfolio.clear()
                    st.success(f"✅ {symbol} removed from portfolio")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# TAB 3 — LIVE PRICES
# ══════════════════════════════════════════════════════════════
with tab_prices:
    p1, p2 = st.columns(2)

    with p1:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● NSE STOCK PRICE</div>',
                    unsafe_allow_html=True)
        stock_lookup = st.text_input("NSE Symbol", placeholder="e.g. INFY",
                                     key="price_stock_sym").upper().strip()
        if st.button("Get Stock Price", use_container_width=True, key="btn_stock_price"):
            if stock_lookup:
                with st.spinner(f"Fetching {stock_lookup}…"):
                    d = stock_agent.get_price(stock_lookup)
                if d.get("error") or not d.get("price"):
                    st.error(f"❌ {d.get('error', 'Symbol not found')}")
                else:
                    c = d.get("change_pct", 0)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Price", fmt_inr(d["price"]))
                    m2.metric("24h Change", f"{c:+.2f}%")
                    m3.metric("Exchange", d.get("exchange", "NSE"))
                    with st.expander("More details"):
                        st.json({
                            "Day High":   fmt_inr(d.get("day_high", 0)),
                            "Day Low":    fmt_inr(d.get("day_low", 0)),
                            "52W High":   fmt_inr(d.get("52w_high", 0)),
                            "52W Low":    fmt_inr(d.get("52w_low", 0)),
                            "Volume":     d.get("volume", 0),
                            "Prev Close": fmt_inr(d.get("prev_close", 0)),
                        })

    with p2:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● CRYPTO PRICE</div>',
                    unsafe_allow_html=True)
        crypto_lookup = st.text_input("Crypto Symbol", placeholder="e.g. SOL",
                                      key="price_crypto_sym").upper().strip()
        if st.button("Get Crypto Price", use_container_width=True, key="btn_crypto_price"):
            if crypto_lookup:
                with st.spinner(f"Fetching {crypto_lookup}…"):
                    d = crypto_agent.get_price(crypto_lookup, "inr")
                if d.get("error") or not d.get("price"):
                    st.error(f"❌ {d.get('error', 'Coin not found')}")
                else:
                    c = d.get("change_pct", 0)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Price", fmt_inr(d["price"]))
                    m2.metric("24h Change", f"{c:+.2f}%")
                    m3.metric("Currency", "INR")
                    with st.expander("More details"):
                        st.json({
                            "24h Volume": fmt_inr(d.get("volume_24h", 0)),
                            "Market Cap": fmt_inr(d.get("market_cap", 0)),
                        })

# ══════════════════════════════════════════════════════════════
# TAB 4 — AI ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab_ai:
    if not llm.available:
        st.warning("⚠️ Gemini AI is offline. Add `GEMINI_API_KEY` to your Streamlit secrets. "
                   "Get a free key at https://aistudio.google.com")

    a1, a2, a3 = st.columns(3)

    with a1:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● PORTFOLIO ANALYSIS</div>',
                    unsafe_allow_html=True)
        if st.button("🔍 Analyze Portfolio", use_container_width=True,
                     type="primary", disabled=not llm.available):
            data_ai = fetch_portfolio()
            if not data_ai["stocks"] and not data_ai["crypto"]:
                st.error("Portfolio is empty! Add holdings first.")
            else:
                with st.spinner("Analyzing with Gemini AI…"):
                    result = llm.analyze_portfolio(data_ai)
                st.markdown("**Analysis Result:**")
                st.markdown(result)

    with a2:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● WEEKLY REPORT</div>',
                    unsafe_allow_html=True)
        if st.button("📄 Generate Report", use_container_width=True,
                     type="primary", disabled=not llm.available):
            data_ai = fetch_portfolio()
            if not data_ai["stocks"] and not data_ai["crypto"]:
                st.error("Portfolio is empty!")
            else:
                with st.spinner("Generating weekly report…"):
                    result = llm.generate_report(data_ai)
                st.markdown("**Weekly Report:**")
                st.markdown(result)

    with a3:
        st.markdown('<div style="font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
                    'color:#00e5a0;font-family:monospace;margin-bottom:12px">● INVESTMENT ADVICE</div>',
                    unsafe_allow_html=True)
        inv_amount = st.number_input("Amount to invest (₹)", min_value=1000.0,
                                     step=5000.0, value=50000.0, format="%.0f")
        risk_level = st.selectbox("Risk Level", ["low", "medium", "high"],
                                  index=1, key="risk_select")
        if st.button("💡 Get Advice", use_container_width=True,
                     type="primary", disabled=not llm.available):
            with st.spinner("Getting investment advice…"):
                result = llm.get_investment_advice(inv_amount, risk_level)
            st.markdown("**Advice:**")
            st.markdown(result)

# ══════════════════════════════════════════════════════════════
# TAB 5 — AI CHAT
# ══════════════════════════════════════════════════════════════
with tab_chat:
    if not llm.available:
        st.warning("⚠️ Gemini AI offline. Add `GEMINI_API_KEY` to your Streamlit secrets to use chat.")

    # Render chat history
    if not st.session_state.chat_history:
        st.markdown('<div style="color:#4a6278;text-align:center;padding:30px 0;font-size:13px">'
                    'Ask anything about your portfolio…</div>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-bot">🤖 {msg["content"]}</div>',
                        unsafe_allow_html=True)

    # Quick suggestions
    st.markdown("**Quick questions:**")
    sug_cols = st.columns(4)
    suggestions = [
        "How is my portfolio doing?",
        "Which is my best asset?",
        "Should I rebalance?",
        "What's my total P&L?",
    ]
    for i, sug in enumerate(suggestions):
        with sug_cols[i]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state._pending_chat = sug
                st.rerun()

    chat_input = st.chat_input("Ask about your portfolio…", disabled=not llm.available)

    message = chat_input
    if "_pending_chat" in st.session_state:
        message = st.session_state.pop("_pending_chat")

    if message and message.strip():
        st.session_state.chat_history.append({"role": "user", "content": message})
        history_tuples = []
        msgs = st.session_state.chat_history
        for i in range(0, len(msgs) - 1, 2):
            if msgs[i]["role"] == "user" and i + 1 < len(msgs) and msgs[i+1]["role"] == "assistant":
                history_tuples.append((msgs[i]["content"], msgs[i+1]["content"]))
        with st.spinner("Thinking…"):
            portfolio_ctx = fetch_portfolio()
            reply = llm.chat(message, portfolio_ctx, history_tuples[-4:])
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# ══════════════════════════════════════════════════════════════
# TAB 6 — NEWS
# ══════════════════════════════════════════════════════════════
with tab_news:
    n1, _ = st.columns([1, 9])
    with n1:
        if st.button("🔄 Refresh News", key="news_refresh"):
            fetch_news.clear()
            st.rerun()

    with st.spinner("Fetching news…"):
        articles = fetch_news()

    if not articles:
        st.info("No news available. Add `NEWS_API_KEY` to your Streamlit secrets for live market news.")
    else:
        for article in articles:
            title  = article.get("title", "")
            url    = article.get("url", "#")
            source = article.get("source", "")
            pub    = article.get("published", "")
            desc   = article.get("description", "")
            try:
                pub_fmt = datetime.fromisoformat(
                    pub.replace("Z", "+00:00")).strftime("%d %b %Y, %I:%M %p")
            except Exception:
                pub_fmt = pub[:19].replace("T", " ") if pub else ""

            st.markdown(f"""
            <div class="news-card">
              <a class="news-title" href="{url}" target="_blank" rel="noopener">{title}</a>
              <div class="news-meta">
                <span class="news-badge">{source}</span>{pub_fmt}
              </div>
              {f'<div class="news-desc">{str(desc)[:200]}…</div>' if desc else ''}
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 7 — TRANSACTIONS
# ══════════════════════════════════════════════════════════════
with tab_txn:
    txns = get_transaction_history()[:50]

    if not txns:
        st.info("No transactions yet.")
    else:
        rows = []
        for t in txns:
            rows.append({
                "Type":   t.get("type", ""),
                "Asset":  t.get("asset_type", ""),
                "Symbol": t.get("symbol", ""),
                "Qty":    t.get("quantity", 0),
                "Price":  fmt_inr(t.get("price", 0)),
                "Total":  fmt_inr(t.get("total", 0)),
                "Date":   t.get("date", "")[:19].replace("T", " "),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(txns)} most recent transactions")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="font-size:9px;font-family:monospace;color:#4a6278;text-align:center;'
    'letter-spacing:.04em">FinPilot · AI Portfolio Tracker · NSE/BSE via yfinance · Crypto via CoinGecko · '
    'AI via Gemini · Not financial advice</div>',
    unsafe_allow_html=True
)

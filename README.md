# FinPilot — AI Portfolio Tracker

> Track your NSE/BSE stocks and crypto portfolio with live prices, AI-powered analysis, and an interactive chat assistant — all in one dark-themed dashboard.

---

## Features

- **Portfolio Overview** — Live P&L, current value, allocation pie chart, and per-asset bar chart
- **NSE/BSE Stock Tracking** — Real-time Indian stock prices via `yfinance`
- **Crypto Tracking** — Live cryptocurrency prices via CoinGecko API (INR)
- **AI Portfolio Analysis** — Powered by Gemini 2.5 Flash; get a full breakdown, weekly report, or tailored investment advice
- **AI Chat Assistant** — Conversational interface to ask anything about your portfolio
- **Live Market News** — Financial news feed via NewsAPI or CoinGecko fallback
- **Transaction History** — Log of all add/remove actions with timestamps
- **Add / Remove Holdings** — Quick-select chips for popular NSE stocks and crypto symbols

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Charts | Plotly |
| Stock Data | yfinance (NSE/BSE) |
| Crypto Data | CoinGecko (via requests) |
| AI | Google Gemini 2.5 Flash (`google-generativeai`) |
| Data | Pandas, Pydantic |
| Secrets | Streamlit Secrets (`st.secrets`) |
| Deployment | Heroku (Procfile) / Streamlit Cloud |

---

## Project Structure

```
├── app.py                  # Main Streamlit application
├── core/
│   ├── portfolio.py        # Add/remove holdings, load portfolio, transaction history
│   └── analyzer.py         # Portfolio data aggregation and allocation calculations
├── agents/
│   ├── llm_agent.py        # Gemini AI agent (analysis, report, advice, chat)
│   ├── stock_agent.py      # NSE/BSE price fetcher via yfinance
│   ├── crypto_agent.py     # Crypto price fetcher via CoinGecko
│   └── news_agent.py       # Market news fetcher
├── portfolio.json          # Persistent portfolio data store
├── requirements.txt
└── Procfile                # Heroku deployment config
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/AryaLolusare2712/AryaLolusare2712-FinPilot-AI_Portfolio_Tracker.git
cd AryaLolusare2712-FinPilot-AI_Portfolio_Tracker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Streamlit secrets

Create a `.streamlit/secrets.toml` file in the project root:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
NEWS_API_KEY = "your_newsapi_key_here"   # optional
```

- Get a free Gemini API key at [https://aistudio.google.com](https://aistudio.google.com)
- Get a free NewsAPI key at [https://newsapi.org](https://newsapi.org) (optional — falls back to CoinGecko news)

When deploying to Streamlit Cloud, add these under **App settings > Secrets** instead of using a local file.

### 4. Run the app

```bash
streamlit run app.py
```

---

## Secrets

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (for AI features) | Google Gemini API key |
| `NEWS_API_KEY` | No | NewsAPI key for live market news |

Set these in `.streamlit/secrets.toml` locally, or under **App settings > Secrets** on Streamlit Cloud.

---

## App Tabs

| Tab | Description |
|---|---|
| Overview | Portfolio summary, KPIs, allocation chart, holdings tables |
| Add / Remove | Add stocks (NSE) or crypto, remove existing holdings |
| Live Prices | Look up any NSE stock or crypto price on demand |
| AI Analysis | Gemini-powered portfolio analysis, weekly report, investment advice |
| AI Chat | Ask questions about your portfolio in natural language |
| News | Latest market and crypto news |
| Transactions | Full history of all add/remove actions |

---

## Deploying to Heroku

The repo includes a `Procfile` for Heroku deployment:

```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

Set your environment variables in Heroku's Config Vars under **Settings**.

---

## Disclaimer

FinPilot is a personal portfolio tracking tool. Nothing in this application constitutes financial advice. Always do your own research before making investment decisions.

---

## Author

**Arya Lolusare** — [GitHub](https://github.com/AryaLolusare2712)

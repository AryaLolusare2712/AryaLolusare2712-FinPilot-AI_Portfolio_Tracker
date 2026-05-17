# 🤖 AI Investment Portfolio Tracker (FastAPI Edition)

NSE/BSE Stocks + Crypto tracker with **Gemini AI** analysis — now powered by **FastAPI** for fast, production-ready deployment.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 📈 NSE/BSE Stocks | Live prices via yfinance (FREE) |
| 🪙 Crypto | Live prices via CoinGecko (FREE) |
| 🤖 AI Analysis | Gemini 1.5 Flash (FREE tier) |
| 💬 AI Chat | Portfolio Q&A with context |
| 📊 Charts | Allocation pie + P&L bar (Chart.js) |
| 📰 News | CryptoPanic + GNews live feed |
| 🧾 Transactions | Full buy/sell/remove history |
| ⚡ FastAPI | REST API + Single-page HTML UI |

---

## 🚀 Quick Start

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set up environment
```bash
cp .env.example .env
# Add your GEMINI_API_KEY and optionally NEWS_API_KEY
```

### Step 3: Run the app
```bash
python app.py
# OR
uvicorn app:app --reload --port 7860
```

### Step 4: Open in browser
```
http://localhost:7860
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Gemini AI for analysis/chat. Get free at [aistudio.google.com](https://aistudio.google.com) |
| `NEWS_API_KEY` | Optional | NewsAPI for market news. Free at [newsapi.org](https://newsapi.org) |
| `PORT` | Optional | Server port (default: 7860) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Main UI |
| GET | `/api/portfolio` | Full portfolio with live P&L |
| POST | `/api/portfolio/add/stock` | Add stock holding |
| POST | `/api/portfolio/add/crypto` | Add crypto holding |
| POST | `/api/portfolio/remove` | Remove holding |
| GET | `/api/price/stock/{symbol}` | Live NSE stock price |
| GET | `/api/price/crypto/{symbol}` | Live crypto price (INR) |
| GET | `/api/news` | Latest market/crypto news |
| GET | `/api/transactions` | Transaction history |
| POST | `/api/ai/analyze` | Full AI portfolio analysis |
| POST | `/api/ai/report` | Weekly AI report |
| POST | `/api/ai/advice` | Investment advice for amount+risk |
| POST | `/api/ai/chat` | Chat with portfolio context |

---

## 📁 Project Structure

```
portfolio-tracker/
│
├── agents/
│   ├── stock_agent.py      # NSE/BSE live prices (yfinance)
│   ├── crypto_agent.py     # Crypto live prices (CoinGecko)
│   ├── news_agent.py       # Market news (CryptoPanic/GNews)
│   └── llm_agent.py        # Gemini AI analysis & chat
│
├── core/
│   ├── portfolio.py        # Holdings CRUD (JSON)
│   └── analyzer.py         # Live P&L calculation
│
├── app.py                  # FastAPI app + HTML UI
├── portfolio.json          # Auto-created holdings store
├── .env                    # API keys
├── requirements.txt        # Python dependencies
├── Procfile                # Railway/Heroku deployment
└── README.md               # This file
```

---

## 🚀 Deploy to Railway

1. Push this folder to GitHub
2. Create new Railway project → Deploy from GitHub
3. Add environment variables:
   - `GEMINI_API_KEY` = your key
   - `NEWS_API_KEY`   = your key (optional)
4. Railway auto-detects Procfile and deploys!

---

## ⚠️ Disclaimer

Educational tool only. Consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

"""
LLM Agent - Gemini API (google-generativeai SDK)
Fixed: uses correct google.generativeai import (not google.genai)
"""

import json
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_OFFLINE_MSG = """
⚠️ Gemini API key missing.

Add this in your .env file or Railway Variables:
GEMINI_API_KEY=your_api_key

Get a free key at: https://aistudio.google.com
"""


class LLMAgent:

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model_name = model
        self.available = bool(GEMINI_API_KEY)
        self._model = None

        if self.available:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self._model = genai.GenerativeModel(model)
            except Exception as e:
                print(f"[LLMAgent] Init error: {e}")
                self.available = False

    def _call(self, prompt: str) -> str:
        if not self.available or self._model is None:
            return _OFFLINE_MSG
        try:
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini Error: {str(e)}"

    def analyze_portfolio(self, portfolio_data: dict) -> str:
        summary = portfolio_data.get("summary", {})
        stocks  = portfolio_data.get("stocks", [])
        crypto  = portfolio_data.get("crypto", [])

        prompt = f"""You are an expert Indian financial advisor.

PORTFOLIO SUMMARY:
Total Invested: ₹{summary.get('total_invested', 0):,.2f}
Current Value:  ₹{summary.get('total_current_value', 0):,.2f}
Total P&L:      ₹{summary.get('total_pnl', 0):,.2f}

Stocks: {json.dumps(stocks, indent=2)}
Crypto: {json.dumps(crypto, indent=2)}

Give analysis covering:
1. Portfolio health overview
2. Best & worst performing asset
3. Risk analysis
4. Diversification assessment
5. Top 3 actionable recommendations

Keep under 350 words. Use simple language."""
        return self._call(prompt)

    def chat(self, user_message: str, portfolio_context: dict, chat_history: list = None) -> str:
        summary  = portfolio_context.get("summary", {})
        stocks   = portfolio_context.get("stocks", [])
        crypto   = portfolio_context.get("crypto", [])

        holdings_str = ""
        for s in stocks:
            holdings_str += f"  - {s['symbol']}: {s['quantity']} shares @ ₹{s['buy_price']}, P&L: {s.get('pnl_pct', 0):.1f}%\n"
        for c in crypto:
            holdings_str += f"  - {c['symbol']}: {c['quantity']} coins @ ₹{c['buy_price']}, P&L: {c.get('pnl_pct', 0):.1f}%\n"

        history_str = ""
        if chat_history:
            for u, b in (chat_history or [])[-4:]:
                history_str += f"User: {u}\nAdvisor: {b}\n"

        prompt = f"""You are a friendly AI investment advisor for an Indian investor.

Portfolio:
- Invested: ₹{summary.get('total_invested', 0):,.2f}
- Value:    ₹{summary.get('total_current_value', 0):,.2f}
- P&L:      ₹{summary.get('total_pnl', 0):,.2f} ({summary.get('total_pnl_pct', 0):.1f}%)

Holdings:
{holdings_str or "No holdings yet."}
{f"Recent chat:{chr(10)}{history_str}" if history_str else ""}

User: {user_message}

Respond helpfully and concisely (max 200 words)."""
        return self._call(prompt)

    def generate_report(self, portfolio_data: dict) -> str:
        summary = portfolio_data.get("summary", {})
        prompt = f"""Generate a professional weekly investment report for an Indian investor.

Data: {json.dumps(summary, indent=2)}
Stocks: {json.dumps(portfolio_data.get('stocks', []), indent=2)}
Crypto: {json.dumps(portfolio_data.get('crypto', []), indent=2)}

Include: Executive Summary, Performance Highlights, Risk Assessment, Action Items.
Keep under 400 words."""
        return self._call(prompt)

    def get_investment_advice(self, amount: float, risk_level: str = "medium") -> str:
        risk_map = {"low": "conservative", "medium": "balanced", "high": "aggressive"}
        risk = risk_map.get(risk_level, "balanced")
        prompt = f"""An Indian {risk} investor wants to invest ₹{amount:,.2f}.

Provide:
1. Specific allocation (%) across NSE stocks, crypto, gold, fixed income
2. 2-3 specific stock/crypto suggestions
3. Why this suits their risk profile
4. Key risks
5. SIP vs lump sum recommendation

Be specific with amounts. Max 350 words."""
        return self._call(prompt)

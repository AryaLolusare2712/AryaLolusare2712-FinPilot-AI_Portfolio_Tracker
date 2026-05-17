"""
Analyzer - Portfolio ka live data fetch karke full analysis karo
"""
from agents.stock_agent import StockAgent
from agents.crypto_agent import CryptoAgent
from core.portfolio import load_portfolio, calculate_pnl

stock_agent = StockAgent()
crypto_agent = CryptoAgent()


def get_full_portfolio_data() -> dict:
    """
    Saare holdings ka live price fetch karo aur P&L calculate karo.
    Returns complete portfolio dict with summary.
    """
    portfolio = load_portfolio()
    result = {
        "stocks": [],
        "crypto": [],
        "summary": {},
        "errors": []
    }

    total_invested = 0.0
    total_current = 0.0

    # ── Stocks ────────────────────────────────────────────────
    stock_symbols = list(portfolio.get("stocks", {}).keys())
    for symbol in stock_symbols:
        holding = portfolio["stocks"][symbol]
        live = stock_agent.get_price(symbol)

        if live.get("error") or live.get("price", 0) == 0:
            result["errors"].append(
                f"Stock {symbol}: {live.get('error', 'Price unavailable')}"
            )
            # FIX: do NOT add pnl amounts to totals when data is errored
            pnl = calculate_pnl(symbol, holding["quantity"],
                                 holding["buy_price"], holding["buy_price"])
            result["stocks"].append({
                "symbol": symbol,
                "name": symbol,
                "quantity": holding["quantity"],
                "buy_price": holding["buy_price"],
                "current_price": holding["buy_price"],
                "change": 0,
                "change_pct": 0,
                "day_high": 0,
                "day_low": 0,
                "sector": "Unknown",
                "exchange": "NSE",
                "data_error": True,
                **pnl
            })
            # FIX: skip adding errored holding to totals (was double-counting)
            continue

        pnl = calculate_pnl(symbol, holding["quantity"],
                             holding["buy_price"], live["price"])
        result["stocks"].append({
            "symbol": symbol,
            "name": live.get("name", symbol),
            "quantity": holding["quantity"],
            "buy_price": holding["buy_price"],
            "current_price": live["price"],
            "change": live.get("change", 0),
            "change_pct": live.get("change_pct", 0),
            "day_high": live.get("day_high", 0),
            "day_low": live.get("day_low", 0),
            "volume": live.get("volume", 0),
            "pe_ratio": live.get("pe_ratio", "N/A"),
            "52w_high": live.get("52w_high", 0),
            "52w_low": live.get("52w_low", 0),
            "sector": live.get("sector", "Unknown"),
            "exchange": live.get("exchange", "NSE"),
            "data_error": False,
            **pnl
        })
        total_invested += pnl["invested"]
        total_current += pnl["current_value"]

    # ── Crypto ────────────────────────────────────────────────
    crypto_symbols = list(portfolio.get("crypto", {}).keys())
    if crypto_symbols:
        live_prices = crypto_agent.get_multiple_prices(crypto_symbols, "inr")
        live_map = {p["symbol"]: p for p in live_prices}

        for symbol in crypto_symbols:
            holding = portfolio["crypto"][symbol]
            live = live_map.get(symbol.upper(), {})

            if live.get("error") or not live.get("price"):
                result["errors"].append(
                    f"Crypto {symbol}: {live.get('error', 'Price unavailable')}"
                )
                # FIX: skip errored holding from totals
                pnl = calculate_pnl(symbol, holding["quantity"],
                                     holding["buy_price"], holding["buy_price"])
                result["crypto"].append({
                    "symbol": symbol,
                    "quantity": holding["quantity"],
                    "buy_price": holding["buy_price"],
                    "current_price": holding["buy_price"],
                    "change_pct": 0,
                    "data_error": True,
                    **pnl
                })
                continue

            pnl = calculate_pnl(symbol, holding["quantity"],
                                 holding["buy_price"], live["price"])
            result["crypto"].append({
                "symbol": symbol,
                "quantity": holding["quantity"],
                "buy_price": holding["buy_price"],
                "current_price": live["price"],
                "change_pct": live.get("change_pct", 0),
                "volume_24h": live.get("volume_24h", 0),
                "market_cap": live.get("market_cap", 0),
                "currency": "INR",
                "data_error": False,
                **pnl
            })
            total_invested += pnl["invested"]
            total_current += pnl["current_value"]

    # ── Summary ───────────────────────────────────────────────
    total_pnl = total_current - total_invested
    result["summary"] = {
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(
            (total_pnl / total_invested * 100) if total_invested > 0 else 0, 2
        ),
        "total_stocks": len(result["stocks"]),
        "total_crypto": len(result["crypto"]),
        "is_profit": total_pnl >= 0
    }

    return result


def get_top_performers(data: dict, n: int = 3) -> dict:
    """Top gainers aur losers return karo"""
    all_assets = data.get("stocks", []) + data.get("crypto", [])
    sorted_by_pnl = sorted(all_assets,
                            key=lambda x: x.get("pnl_pct", 0),
                            reverse=True)
    return {
        "top_gainers": sorted_by_pnl[:n],
        "top_losers":  sorted_by_pnl[-n:][::-1]
    }


def get_allocation_data(data: dict) -> dict:
    """Pie chart ke liye allocation data - FIX: use buy_price*qty as fallback"""
    labels = []
    values = []
    colors = []

    stock_colors  = ["#2196F3", "#03A9F4", "#00BCD4", "#009688",
                     "#4CAF50", "#8BC34A", "#CDDC39", "#FFC107"]
    crypto_colors = ["#FF9800", "#FF5722", "#E91E63", "#9C27B0",
                     "#673AB7", "#3F51B5", "#F44336", "#795548"]

    for i, s in enumerate(data.get("stocks", [])):
        # FIX: fall back to invested value so errored holdings still show in chart
        value = s.get("current_value") or s.get("invested", 0)
        if value > 0:
            labels.append(f"{s['symbol']} (Stock)")
            values.append(value)
            colors.append(stock_colors[i % len(stock_colors)])

    for i, c in enumerate(data.get("crypto", [])):
        value = c.get("current_value") or c.get("invested", 0)
        if value > 0:
            labels.append(f"{c['symbol']} (Crypto)")
            values.append(value)
            colors.append(crypto_colors[i % len(crypto_colors)])

    return {"labels": labels, "values": values, "colors": colors}

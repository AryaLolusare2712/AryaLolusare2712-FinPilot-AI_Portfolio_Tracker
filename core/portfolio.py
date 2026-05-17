"""
Portfolio Core - Holdings store aur manage karo (JSON based)
"""
import json
import os
from datetime import datetime
from typing import Optional

# Use absolute path relative to this file so it always writes to project root
_HERE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(os.getcwd(), "portfolio.json")


def _default_portfolio() -> dict:
    return {
        "stocks": {},
        "crypto": {},
        "transactions": [],
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }


def load_portfolio() -> dict:
    """Portfolio JSON se load karo"""
    path = os.path.normpath(PORTFOLIO_FILE)
    if not os.path.exists(path):
        save_portfolio(_default_portfolio())
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for key in ["stocks", "crypto", "transactions"]:
                    if key not in data:
                        data[key] = {} if key != "transactions" else []
                return data
        except (json.JSONDecodeError, IOError):
            return _default_portfolio()
    return _default_portfolio()


def save_portfolio(portfolio: dict):
    """Portfolio JSON mein save karo"""
    path = os.path.normpath(PORTFOLIO_FILE)
    portfolio["last_updated"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(portfolio, f, indent=2)


def add_holding(asset_type: str, symbol: str,
                quantity: float, buy_price: float,
                notes: str = "") -> dict:
    """
    Portfolio mein asset add karo.
    asset_type: 'stocks' ya 'crypto'
    """
    portfolio = load_portfolio()
    symbol = symbol.upper().strip()

    if symbol in portfolio[asset_type]:
        existing = portfolio[asset_type][symbol]
        old_qty = existing["quantity"]
        old_price = existing["buy_price"]
        new_qty = old_qty + quantity
        avg_price = ((old_qty * old_price) + (quantity * buy_price)) / new_qty
        portfolio[asset_type][symbol] = {
            **existing,
            "quantity": round(new_qty, 8),
            "buy_price": round(avg_price, 4),
            "invested": round(new_qty * avg_price, 2),
            "last_updated": datetime.now().isoformat()
        }
    else:
        portfolio[asset_type][symbol] = {
            "quantity": quantity,
            "buy_price": buy_price,
            "invested": round(quantity * buy_price, 2),
            "added_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "notes": notes
        }

    # Transaction log
    total_val = round(quantity * buy_price, 2)
    portfolio["transactions"].append({
        "type": "BUY",
        "asset_type": asset_type,
        "symbol": symbol,
        "quantity": quantity,
        "price": buy_price,
        "total": total_val,
        "date": datetime.now().isoformat()
    })

    save_portfolio(portfolio)
    return portfolio


def remove_holding(asset_type: str, symbol: str) -> dict:
    """Portfolio se asset remove karo"""
    portfolio = load_portfolio()
    symbol = symbol.upper().strip()

    if symbol in portfolio[asset_type]:
        holding = portfolio[asset_type][symbol]
        qty = holding["quantity"]
        price = holding["buy_price"]
        total_val = round(qty * price, 2)   # FIX: was missing "total" key

        portfolio["transactions"].append({
            "type": "REMOVE",
            "asset_type": asset_type,
            "symbol": symbol,
            "quantity": qty,
            "price": price,
            "total": total_val,             # FIX: added total so Transactions tab shows correct value
            "date": datetime.now().isoformat()
        })
        del portfolio[asset_type][symbol]
        save_portfolio(portfolio)
    return portfolio


def update_holding(asset_type: str, symbol: str,
                   quantity: Optional[float] = None,
                   buy_price: Optional[float] = None) -> dict:
    """Existing holding update karo"""
    portfolio = load_portfolio()
    symbol = symbol.upper().strip()

    if symbol in portfolio[asset_type]:
        if quantity is not None:
            portfolio[asset_type][symbol]["quantity"] = quantity
        if buy_price is not None:
            portfolio[asset_type][symbol]["buy_price"] = buy_price

        holding = portfolio[asset_type][symbol]
        portfolio[asset_type][symbol]["invested"] = round(
            holding["quantity"] * holding["buy_price"], 2
        )
        portfolio[asset_type][symbol]["last_updated"] = datetime.now().isoformat()
        save_portfolio(portfolio)

    return portfolio


def calculate_pnl(symbol: str, quantity: float,
                  buy_price: float, current_price: float) -> dict:
    """P&L calculate karo"""
    invested = round(quantity * buy_price, 2)
    current_value = round(quantity * current_price, 2)
    pnl = round(current_value - invested, 2)
    pnl_pct = round((pnl / invested * 100) if invested > 0 else 0, 2)

    return {
        "invested": invested,
        "current_value": current_value,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "is_profit": pnl >= 0
    }


def get_transaction_history() -> list:
    """Transaction history return karo"""
    portfolio = load_portfolio()
    return sorted(
        portfolio.get("transactions", []),
        key=lambda x: x.get("date", ""),
        reverse=True
    )


def clear_portfolio() -> dict:
    """Portfolio reset karo (caution!)"""
    portfolio = _default_portfolio()
    save_portfolio(portfolio)
    return portfolio

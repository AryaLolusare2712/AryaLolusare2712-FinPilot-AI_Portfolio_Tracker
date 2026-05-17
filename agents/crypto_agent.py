"""
Crypto Agent - CoinGecko API (FREE, no API key needed)
Supports BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, and more
"""
import requests
from datetime import datetime


class CryptoAgent:
    BASE_URL = "https://api.coingecko.com/api/v3"

    # Common symbol → CoinGecko ID mapping
    COIN_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "MATIC": "matic-network",
        "DOT": "polkadot",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "LTC": "litecoin",
        "ATOM": "cosmos",
        "NEAR": "near",
        "FTM": "fantom",
        "ALGO": "algorand",
        "VET": "vechain",
        "SAND": "the-sandbox",
        "MANA": "decentraland",
        "SHIB": "shiba-inu",
        "TRX": "tron",
    }

    def get_coin_id(self, symbol: str) -> str:
        return self.COIN_IDS.get(symbol.upper(), symbol.lower())

    def get_price(self, symbol: str, currency: str = "inr") -> dict:
        """CoinGecko se live crypto price - bilkul free"""
        try:
            coin_id = self.get_coin_id(symbol)
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": currency,
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true",
                "include_last_updated_at": "true"
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get(coin_id, {})

            if not data:
                return {"symbol": symbol.upper(), "error": "Coin not found", "price": 0}

            return {
                "symbol": symbol.upper(),
                "coin_id": coin_id,
                "price": data.get(currency, 0),
                "change_pct": round(data.get(f"{currency}_24h_change", 0), 2),
                "volume_24h": data.get(f"{currency}_24h_vol", 0),
                "market_cap": data.get(f"{currency}_market_cap", 0),
                "currency": currency.upper(),
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
        except requests.exceptions.ConnectionError:
            return {"symbol": symbol.upper(), "error": "Network error", "price": 0}
        except Exception as e:
            return {"symbol": symbol.upper(), "error": str(e), "price": 0}

    def get_multiple_prices(self, symbols: list, currency: str = "inr") -> list:
        """Multiple coins ek saath fetch karo - efficient"""
        try:
            coin_ids = [self.get_coin_id(s) for s in symbols]
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": currency,
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true"
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            raw = resp.json()

            results = []
            for symbol, coin_id in zip(symbols, coin_ids):
                data = raw.get(coin_id, {})
                results.append({
                    "symbol": symbol.upper(),
                    "coin_id": coin_id,
                    "price": data.get(currency, 0),
                    "change_pct": round(data.get(f"{currency}_24h_change", 0), 2),
                    "volume_24h": data.get(f"{currency}_24h_vol", 0),
                    "market_cap": data.get(f"{currency}_market_cap", 0),
                    "currency": currency.upper(),
                    "error": None
                })
            return results
        except Exception as e:
            return [self.get_price(s, currency) for s in symbols]

    def get_top_coins(self, currency: str = "inr", limit: int = 10) -> list:
        """Market cap ke hisaab se top coins"""
        try:
            url = f"{self.BASE_URL}/coins/markets"
            params = {
                "vs_currency": currency,
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "price_change_percentage": "24h"
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return []

    def get_history(self, symbol: str, days: int = 30,
                    currency: str = "inr") -> list:
        """Historical price data for charts"""
        try:
            coin_id = self.get_coin_id(symbol)
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {"vs_currency": currency, "days": days, "interval": "daily"}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            prices = resp.json().get("prices", [])
            return [{"timestamp": p[0], "price": p[1]} for p in prices]
        except Exception:
            return []

"""
Stock Agent - NSE/BSE live data
Fix: Uses a manual requests session with cookies+crumb to bypass
yfinance's 'Expecting value: line 1 column 1' crumb bug.
Falls back to yfinance download() if direct fetch fails.
"""
import time
import requests
import pandas as pd
from datetime import datetime


class StockAgent:

    POPULAR_NSE = {
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "INFY": "Infosys",
        "HDFCBANK": "HDFC Bank",
        "WIPRO": "Wipro",
        "TATAMOTORS": "Tata Motors",
        "ITC": "ITC Limited",
        "SBIN": "State Bank of India",
        "ADANIENT": "Adani Enterprises",
        "BAJFINANCE": "Bajaj Finance",
        "HINDUNILVR": "Hindustan Unilever",
        "ICICIBANK": "ICICI Bank",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "AXISBANK": "Axis Bank",
        "LT": "Larsen & Toubro",
        "SUNPHARMA": "Sun Pharmaceutical",
        "TITAN": "Titan Company",
        "ULTRACEMCO": "UltraTech Cement",
        "ASIANPAINT": "Asian Paints",
        "MARUTI": "Maruti Suzuki",
    }

    _cache: dict = {}
    CACHE_TTL = 60  # seconds

    # Shared session + crumb (class-level, refreshed once per hour)
    _session: requests.Session = None
    _crumb: str = None
    _session_ts: float = 0
    SESSION_TTL = 3600

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        return (time.time() - self._cache[key]["ts"]) < self.CACHE_TTL

    def _set_cache(self, key: str, data: dict):
        self._cache[key] = {"data": data, "ts": time.time()}

    # ── Session / Crumb ────────────────────────────────────────
    def _init_session(self) -> bool:
        """Get Yahoo Finance session cookies + crumb (once per hour)."""
        if (StockAgent._session is not None
                and StockAgent._crumb
                and (time.time() - StockAgent._session_ts) < self.SESSION_TTL):
            return True
        try:
            s = requests.Session()
            s.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            })
            s.get("https://finance.yahoo.com", timeout=10)
            crumb_resp = s.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb",
                timeout=10
            )
            if crumb_resp.status_code == 200 and crumb_resp.text.strip():
                StockAgent._session = s
                StockAgent._crumb = crumb_resp.text.strip()
                StockAgent._session_ts = time.time()
                return True
        except Exception:
            pass
        return False

    # ── Primary: direct Yahoo chart API ───────────────────────
    def _fetch_yahoo_direct(self, symbol: str, exchange: str) -> dict:
        """Call Yahoo Finance chart API directly with session + crumb."""
        if not self._init_session():
            return {}
        ticker_symbol = f"{symbol.upper()}.{exchange}"
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}"
            params = {
                "range": "2d", "interval": "1d",
                "crumb": StockAgent._crumb,
                "includePrePost": "false",
            }
            resp = StockAgent._session.get(url, params=params, timeout=10)

            # crumb expired — reset and retry once
            if resp.status_code == 401:
                StockAgent._crumb = None
                StockAgent._session = None
                if not self._init_session():
                    return {}
                params["crumb"] = StockAgent._crumb
                resp = StockAgent._session.get(url, params=params, timeout=10)

            if not resp.ok:
                return {}

            j = resp.json()
            result0 = j["chart"]["result"][0]
            meta    = result0["meta"]
            quote   = result0["indicators"]["quote"][0]

            closes  = [c for c in quote.get("close",  []) if c is not None]
            highs   = [h for h in quote.get("high",   []) if h is not None]
            lows    = [l for l in quote.get("low",    []) if l is not None]
            volumes = [v for v in quote.get("volume", []) if v is not None]

            if not closes:
                return {}

            current    = round(closes[-1], 2)
            prev_close = round(closes[-2], 2) if len(closes) >= 2 else current
            change     = round(current - prev_close, 2)
            change_pct = round((change / prev_close * 100) if prev_close else 0, 2)

            return {
                "symbol":     symbol.upper(),
                "ticker":     ticker_symbol,
                "name":       self.POPULAR_NSE.get(symbol.upper(), symbol.upper()),
                "price":      current,
                "prev_close": prev_close,
                "change":     change,
                "change_pct": change_pct,
                "day_high":   round(highs[-1],   2) if highs   else 0,
                "day_low":    round(lows[-1],    2) if lows    else 0,
                "volume":     int(volumes[-1])       if volumes else 0,
                "market_cap": meta.get("marketCap", 0),
                "pe_ratio":   "N/A",
                "52w_high":   round(meta.get("fiftyTwoWeekHigh", 0), 2),
                "52w_low":    round(meta.get("fiftyTwoWeekLow",  0), 2),
                "sector":     "N/A",
                "currency":   "INR",
                "exchange":   "NSE" if exchange == "NS" else "BSE",
                "timestamp":  datetime.now().isoformat(),
                "error":      None,
            }
        except Exception as e:
            return {"error": str(e)}

    # ── Fallback: yfinance download() ─────────────────────────
    def _fetch_yf_history(self, symbol: str, exchange: str) -> dict:
        """Fallback using yfinance download (avoids Ticker.info crumb issue)."""
        try:
            import yfinance as yf
            ticker_symbol = f"{symbol.upper()}.{exchange}"
            df = yf.download(
                ticker_symbol, period="5d", interval="1d",
                progress=False, auto_adjust=True
            )
            if df.empty:
                return {
                    "symbol": symbol.upper(), "price": 0, "change_pct": 0,
                    "error": "No data — check NSE symbol (e.g. RELIANCE, TCS, INFY)",
                    "timestamp": datetime.now().isoformat(),
                }

            current    = round(float(df["Close"].iloc[-1]), 2)
            prev_close = round(float(df["Close"].iloc[-2]), 2) if len(df) >= 2 else current
            change     = round(current - prev_close, 2)
            change_pct = round((change / prev_close * 100) if prev_close else 0, 2)

            return {
                "symbol":     symbol.upper(),
                "ticker":     ticker_symbol,
                "name":       self.POPULAR_NSE.get(symbol.upper(), symbol.upper()),
                "price":      current,
                "prev_close": prev_close,
                "change":     change,
                "change_pct": change_pct,
                "day_high":   round(float(df["High"].iloc[-1]),   2),
                "day_low":    round(float(df["Low"].iloc[-1]),    2),
                "volume":     int(df["Volume"].iloc[-1]),
                "market_cap": 0, "pe_ratio": "N/A",
                "52w_high": 0, "52w_low": 0, "sector": "N/A",
                "currency":  "INR",
                "exchange":  "NSE" if exchange == "NS" else "BSE",
                "timestamp": datetime.now().isoformat(),
                "error":     None,
            }
        except Exception as e:
            return {
                "symbol": symbol.upper(), "price": 0, "change_pct": 0,
                "error": str(e), "timestamp": datetime.now().isoformat(),
            }

    # ── Public API ────────────────────────────────────────────
    def get_price(self, symbol: str, exchange: str = "NS") -> dict:
        cache_key = f"{symbol}.{exchange}"
        if self._is_cached(cache_key):
            return self._cache[cache_key]["data"]

        result = self._fetch_yahoo_direct(symbol, exchange)
        if not result or result.get("price", 0) == 0 or result.get("error"):
            result = self._fetch_yf_history(symbol, exchange)

        self._set_cache(cache_key, result)
        return result

    def get_history(self, symbol: str, period: str = "1mo",
                    exchange: str = "NS") -> pd.DataFrame:
        try:
            import yfinance as yf
            return yf.Ticker(f"{symbol.upper()}.{exchange}").history(period=period)
        except Exception:
            return pd.DataFrame()

    def search_symbol(self, query: str) -> list:
        q = query.upper()
        return [
            {"symbol": s, "name": n}
            for s, n in self.POPULAR_NSE.items()
            if q in s or query.lower() in n.lower()
        ]

    def get_multiple_prices(self, symbols: list, exchange: str = "NS") -> list:
        return [self.get_price(s, exchange) for s in symbols]

"""
News Agent - Financial news fetch karo
Free sources use karta hai, NewsAPI optional hai
"""
import requests
from datetime import datetime


class NewsAgent:

    def get_market_news(self, query: str = "Indian stock market NSE BSE",
                        api_key: str = None) -> list:
        """
        Market news fetch karo.
        NewsAPI key optional hai - bina key ke bhi kuch news milti hai.
        Free key lene ke liye: https://newsapi.org (500 requests/day free)
        """
        if api_key:
            return self._fetch_newsapi(query, api_key)
        return self._fetch_free_news(query)

    def _fetch_newsapi(self, query: str, api_key: str) -> list:
        """NewsAPI se news (key chahiye)"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": api_key
            }
            resp = requests.get(url, params=params, timeout=10)
            articles = resp.json().get("articles", [])
            return [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "url": a.get("url", ""),
                    "published": a.get("publishedAt", ""),
                    "description": a.get("description", "")
                }
                for a in articles if a.get("title")
            ]
        except Exception as e:
            return [{"title": f"News fetch error: {e}", "source": "", "url": ""}]

    def _fetch_free_news(self, query: str) -> list:
        """
        Bina API key ke crypto/finance news.
        FIX: CoinGecko /v3/news endpoint deprecated hai — use GNews public RSS instead.
        """
        # Try CryptoPanic public feed (no key needed for public posts)
        articles = self._fetch_cryptopanic()
        if articles:
            return articles

        # Fallback: GNews RSS for crypto/finance
        articles = self._fetch_gnews_rss()
        if articles:
            return articles

        # Last resort placeholder
        return [
            {
                "title": "Live market news ke liye NewsAPI key add karo .env mein",
                "source": "System",
                "url": "https://newsapi.org",
                "published": datetime.now().isoformat(),
                "description": (
                    "Free tier: 500 requests/day. "
                    "Sign up at newsapi.org and set NEWS_API_KEY in your .env file."
                )
            }
        ]

    def _fetch_cryptopanic(self) -> list:
        """CryptoPanic public news feed — free, no API key"""
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "public": "true",
                "kind": "news",
                "filter": "hot"
            }
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                results = resp.json().get("results", [])[:10]
                articles = []
                for r in results:
                    title = r.get("title", "")
                    if not title:
                        continue
                    source = r.get("source", {}).get("title", "CryptoPanic")
                    url_link = r.get("url", "")
                    published = r.get("published_at", "")
                    articles.append({
                        "title": title,
                        "source": source,
                        "url": url_link,
                        "published": published,
                        "description": ""
                    })
                return articles
        except Exception:
            pass
        return []

    def _fetch_gnews_rss(self) -> list:
        """GNews RSS feed for crypto/finance news — free"""
        try:
            import xml.etree.ElementTree as ET
            url = "https://news.google.com/rss/search?q=crypto+OR+bitcoin+OR+NSE+stock&hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")[:10]
                articles = []
                for item in items:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub = item.findtext("pubDate", "")
                    source_el = item.find("source")
                    source = source_el.text if source_el is not None else "Google News"
                    desc_raw = item.findtext("description", "")
                    if title:
                        articles.append({
                            "title": title,
                            "source": source,
                            "url": link,
                            "published": pub,
                            "description": desc_raw[:200] if desc_raw else ""
                        })
                return articles
        except Exception:
            pass
        return []

    def get_crypto_news(self) -> list:
        """
        Crypto-specific news.
        FIX: CoinGecko /api/v3/news was deprecated — now using CryptoPanic + GNews fallback.
        """
        articles = self._fetch_cryptopanic()
        if articles:
            return articles
        return self._fetch_gnews_rss()

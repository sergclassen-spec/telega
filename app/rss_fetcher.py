# app/rss_fetcher.py
import feedparser, logging
from .config import CHANNELS

FEEDS = [
    "https://www.reuters.com/rssFeed/businessNews",
    "https://www.investing.com/rss/news.rss",
]


def fetch_rss(limit_per_feed: int = 5):
    items = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            entries = getattr(feed, "entries", [])[:limit_per_feed]
            if not entries:
                logging.warning("No entries for feed %s", url)
                continue
            for e in entries:
                items.append({
                    "title": e.get("title", "")[:300],
                    "summary": e.get("summary", "")[:2000],
                    "link": e.get("link", ""),
                    "channel_id": None,
                    "category": None,
                })
        except Exception as e:
            logging.error("Failed to parse RSS %s: %s", url, e)
    return items

# app/rss_fetcher.py
"""
Simple RSS fetcher. Returns list of items dicts:
{ 'title':..., 'summary':..., 'link':..., 'channel_id': None, 'category': None }
"""

import feedparser
from .config import CHANNELS

# configure feeds to your niches
FEEDS = [
    "https://www.reuters.com/rssFeed/businessNews",
    "https://www.investing.com/rss/news.rss",
]


def fetch_rss(limit_per_feed: int = 5):
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        entries = getattr(feed, "entries", [])[:limit_per_feed]
        for e in entries:
            items.append(
                {
                    "title": e.get("title", "")[:300],
                    "summary": e.get("summary", "")[:2000],
                    "link": e.get("link", ""),
                    "channel_id": None,
                    "category": None,
                }
            )
    return items

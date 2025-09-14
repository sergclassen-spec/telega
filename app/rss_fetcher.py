import feedparser

FEEDS = [
    "https://www.investing.com/rss/news.rss",
    "https://www.reuters.com/rssFeed/businessNews",
]


def fetch_rss():
    """Fetch and parse RSS feeds into items."""
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            items.append({"title": entry.title, "summary": getattr(entry, "summary", "")})
    return items

"""
News Service - Aggregates financial news from multiple sources
"""

import feedparser
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from cachetools import TTLCache
import re

# Cache news for 10 minutes
_cache = TTLCache(maxsize=10, ttl=600)

# RSS Feed sources
NEWS_FEEDS = {
    # Global sources
    "cnbc": {
        "name": "CNBC",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "category": "global"
    },
    "bloomberg": {
        "name": "Bloomberg Markets",
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "category": "global"
    },
    "reuters": {
        "name": "Reuters Business",
        "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
        "category": "global"
    },
    "yahoo_finance": {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "category": "global"
    },
    "marketwatch": {
        "name": "MarketWatch",
        "url": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "category": "global"
    },
    # Indonesian sources
    "cnbc_id": {
        "name": "CNBC Indonesia",
        "url": "https://www.cnbcindonesia.com/rss",
        "category": "indonesia"
    },
    "kontan": {
        "name": "Kontan",
        "url": "https://www.kontan.co.id/rss",
        "category": "indonesia"
    },
    "bisnis": {
        "name": "Bisnis Indonesia",
        "url": "https://www.bisnis.com/rss",
        "category": "indonesia"
    },
    "detik_finance": {
        "name": "Detik Finance",
        "url": "https://rss.detik.com/index.php/finance",
        "category": "indonesia"
    },
    "investor_daily": {
        "name": "Investor Daily",
        "url": "https://investor.id/rss",
        "category": "indonesia"
    }
}

def clean_html(html_text: str) -> str:
    """Remove HTML tags from text"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text().strip()

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Simple keyword-based sentiment analysis
    Returns sentiment score and label
    """
    positive_words = [
        'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'climb', 'advance',
        'bullish', 'profit', 'growth', 'positive', 'upgrade', 'beat', 'strong',
        'naik', 'untung', 'positif', 'menguat', 'tumbuh', 'melonjak'
    ]
    negative_words = [
        'fall', 'drop', 'decline', 'plunge', 'crash', 'tumble', 'sink', 'slump',
        'bearish', 'loss', 'negative', 'downgrade', 'miss', 'weak', 'fear',
        'turun', 'rugi', 'negatif', 'melemah', 'anjlok', 'jatuh'
    ]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return {"score": min(positive_count * 0.2, 1.0), "label": "positive"}
    elif negative_count > positive_count:
        return {"score": min(negative_count * -0.2, -1.0), "label": "negative"}
    return {"score": 0, "label": "neutral"}

def detect_stock_mentions(text: str) -> List[str]:
    """
    Detect stock symbols mentioned in text
    """
    from services.stock_service import DEFAULT_STOCKS
    
    mentions = []
    text_upper = text.upper()
    
    for symbol, info in DEFAULT_STOCKS.items():
        # Check for symbol (without .JK suffix)
        short_symbol = symbol.replace(".JK", "")
        if short_symbol in text_upper:
            mentions.append(symbol)
        # Check for company name
        elif info["name"].upper() in text_upper:
            mentions.append(symbol)
    
    return list(set(mentions))

def fetch_feed(feed_key: str) -> List[Dict[str, Any]]:
    """
    Fetch and parse a single RSS feed
    """
    feed_info = NEWS_FEEDS.get(feed_key)
    if not feed_info:
        return []
    
    try:
        feed = feedparser.parse(feed_info["url"])
        articles = []
        
        for entry in feed.entries[:10]:  # Limit to 10 articles per source
            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            full_text = f"{title} {summary}"
            
            pub_date = parse_date(entry.get("published", entry.get("pubDate", "")))
            
            article = {
                "title": title,
                "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "link": entry.get("link", ""),
                "source": feed_info["name"],
                "sourceKey": feed_key,
                "category": feed_info["category"],
                "publishedAt": pub_date.isoformat() if pub_date else None,
                "sentiment": analyze_sentiment(full_text),
                "stockMentions": detect_stock_mentions(full_text)
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        print(f"Error fetching {feed_key}: {e}")
        return []

def get_all_news(
    category: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get news from all sources
    
    Args:
        category: Filter by category ('global', 'indonesia')
        limit: Maximum number of articles to return
    """
    cache_key = f"all_news_{category}_{limit}"
    
    if cache_key in _cache:
        return _cache[cache_key]
    
    all_articles = []
    
    for feed_key, feed_info in NEWS_FEEDS.items():
        if category and feed_info["category"] != category:
            continue
        articles = fetch_feed(feed_key)
        all_articles.extend(articles)
    
    # Sort by date (newest first)
    all_articles.sort(
        key=lambda x: x["publishedAt"] or "",
        reverse=True
    )
    
    result = all_articles[:limit]
    _cache[cache_key] = result
    return result

def get_news_for_stock(
    symbol: str, 
    limit: int = 20,
    keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get news related to a specific stock or commodity keywords
    """
    all_news = get_all_news(limit=100)
    
    related_news = []
    for article in all_news:
        is_match = False
        
        # Check stock mentions
        if symbol in article.get("stockMentions", []):
            is_match = True
        
        # Check keywords (for commodities)
        if keywords and not is_match:
            text = (article["title"] + " " + article["summary"]).lower()
            for kw in keywords:
                if kw.lower() in text:
                    is_match = True
                    break
        
        if is_match:
            related_news.append(article)
    
    return related_news[:limit]

def get_available_sources() -> List[Dict[str, str]]:
    """
    Get list of available news sources
    """
    return [
        {"key": k, "name": v["name"], "category": v["category"]}
        for k, v in NEWS_FEEDS.items()
    ]

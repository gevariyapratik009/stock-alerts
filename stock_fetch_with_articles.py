#!/usr/bin/env python3
"""
Stock Fetch with Articles - Config-Driven
Fetches stock data and news for a single symbol
All display options controlled by config.json

Usage:
    python stock_fetch_with_articles.py QQQ
    python stock_fetch_with_articles.py TSLA --full
"""

import yfinance as yf
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import sys
import os

# ═══════════════════════════════════════════════════════════════
# CONFIG LOADING
# ═══════════════════════════════════════════════════════════════

def load_config():
    """Load config.json"""
    try:
        # Try local config.json first
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        # Fallback to default
        return {
            "stock_display": {
                "show_sentiment": True,
                "show_news": True,
                "news_articles_count": 5,
                "show_summaries": False,
                "show_urls": True
            }
        }
    except Exception as e:
        print(f"[WARNING] Could not load config.json: {e}")
        return {}

CONFIG = load_config()
DISPLAY_CONFIG = CONFIG.get('stock_display', {})

# ═══════════════════════════════════════════════════════════════
# FORMATTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fmt_price(price):
    """Format price"""
    if price is None:
        return "N/A"
    return f"${price:.2f}"

def fmt_change(current, prev):
    """Format price change"""
    if current is None or prev is None or prev == 0:
        return ""
    change = current - prev
    percent = (change / prev) * 100
    emoji = "🟢" if change >= 0 else "🔴"
    return f"{emoji} {change:+.2f} ({percent:+.2f}%)"

# ═══════════════════════════════════════════════════════════════
# SENTIMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════

def get_market_sentiment(info):
    """Calculate sentiment score from financial metrics"""
    score = 0
    factors = []
    
    # P/E Ratio (lower is better, but reasonable)
    pe = info.get('trailingPE')
    if pe:
        if pe < 15:
            score += 15
            factors.append("✅ P/E < 15 (undervalued)")
        elif pe < 25:
            score += 5
            factors.append("➖ P/E 15-25 (fair)")
        else:
            score -= 10
            factors.append("⚠️ P/E > 25 (overvalued)")
    
    # 52-Week momentum
    high_52w = info.get('fiftyTwoWeekHigh')
    low_52w = info.get('fiftyTwoWeekLow')
    current_price = info.get('currentPrice')
    
    if high_52w and low_52w and current_price:
        momentum = (current_price - low_52w) / (high_52w - low_52w) * 100
        if momentum > 75:
            score += 20
            factors.append("📈 Trading near 52-week high")
        elif momentum < 25:
            score -= 20
            factors.append("📉 Trading near 52-week low")
    
    # Dividend
    div = info.get('dividendYield')
    if div and div > 0.02:
        score += 10
        factors.append(f"💰 Dividend {div*100:.2f}%")
    
    # Volume
    volume = info.get('volume')
    avg_vol = info.get('averageVolume')
    if volume and avg_vol:
        vol_ratio = volume / avg_vol
        if vol_ratio > 1.5:
            score += 5
            factors.append(f"📊 High volume ({vol_ratio:.1f}x avg)")
    
    # Beta
    beta = info.get('beta')
    if beta:
        if beta < 1:
            score += 5
            factors.append("🛡️ Low volatility")
        elif beta > 1.5:
            score -= 5
            factors.append("⚡ High volatility")
    
    # Clamp score
    score = max(-100, min(100, score))
    
    if score > 40:
        label = "📈 BULLISH"
    elif score > 10:
        label = "➖ NEUTRAL"
    elif score > -40:
        label = "📉 BEARISH"
    else:
        label = "🔴 VERY BEARISH"
    
    return score, label, factors

# ═══════════════════════════════════════════════════════════════
# NEWS FETCHING
# ═══════════════════════════════════════════════════════════════

def fetch_news(ticker):
    """Fetch news from yfinance ticker"""
    try:
        news = ticker.news
        if not news:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=72)
        recent_news = []
        
        for item in news:
            title = item.get("content", {}).get("title", "") or item.get("title", "")
            url = item.get("content", {}).get("canonicalUrl", "") or item.get("link", "")
            pub_time = item.get("content", {}).get("pubDate", "") or ""
            publisher = item.get("content", {}).get("provider", {}).get("displayName", "") or item.get("publisher", "")
            
            if pub_time:
                try:
                    dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                    if dt.replace(tzinfo=None) >= cutoff_time:
                        pub_time_display = dt.strftime("%b %d, %H:%M")
                        recent_news.append({
                            'time': pub_time_display,
                            'title': title,
                            'publisher': publisher,
                            'url': url
                        })
                except Exception:
                    pass
        
        return recent_news
    except Exception as e:
        return []

# ═══════════════════════════════════════════════════════════════
# MAIN STOCK FETCH
# ═══════════════════════════════════════════════════════════════

def fetch_and_format_stock(symbol):
    """Fetch stock data and format output"""
    
    try:
        print(f"[⏳] Fetching {symbol}...", file=sys.stderr)
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        info = ticker.info
        
        # Extract data
        price = info.get('currentPrice') or data['Close'].iloc[-1] if not data.empty else None
        prev_close = info.get('previousClose')
        name = info.get('longName', symbol)
        
        premarket_price = info.get('preMarketPrice')
        
        day_low = info.get('dayLow')
        day_high = info.get('dayHigh')
        week_low = info.get('fiftyTwoWeekLow')
        week_high = info.get('fiftyTwoWeekHigh')
        
        volume = info.get('volume')
        avg_volume = info.get('averageVolume')
        mkt_cap = info.get('marketCap')
        sector = info.get('sector')
        industry = info.get('industry')
        
        # Format output
        lines = []
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        
        lines.append(f"\n{'='*80}")
        lines.append(f"📈 {symbol.upper()} | {name}")
        lines.append(f"📅 {current_date}")
        lines.append(f"{'='*80}\n")
        
        # Current Price Section
        lines.append(f"💰 PRICE")
        lines.append(f"  Current:     {fmt_price(price)}  {fmt_change(price, prev_close)}")
        lines.append(f"  Prev Close:  {fmt_price(prev_close)}")
        lines.append(f"  Range:       {fmt_price(day_low)} — {fmt_price(day_high)}")
        
        # Premarket
        if premarket_price:
            lines.append(f"\n🌅 PREMARKET")
            lines.append(f"  Price:  {fmt_price(premarket_price)}  {fmt_change(premarket_price, prev_close)}")
        
        # Key Metrics
        lines.append(f"\n📊 METRICS")
        lines.append(f"  52-Wk:  {fmt_price(week_low)} — {fmt_price(week_high)}")
        if volume and avg_volume:
            vol_ratio = volume / avg_volume
            lines.append(f"  Volume: {volume:,} ({vol_ratio:.1f}x avg)")
        if mkt_cap:
            lines.append(f"  Market Cap: ${mkt_cap/1e9:.2f}B")
        
        # Financials (compact)
        pe = info.get("trailingPE")
        eps = info.get("trailingEps")
        div = info.get("dividendYield")
        beta = info.get("beta")
        
        lines.append(f"\n💹 FINANCIALS")
        lines.append(f"  P/E: {f'{pe:.2f}' if pe else 'N/A'} | EPS: {fmt_price(eps) if eps else 'N/A'} | Div: {f'{div*100:.2f}%' if div else 'None'} | Beta: {f'{beta:.2f}' if beta else 'N/A'}")
        
        # Sentiment
        if DISPLAY_CONFIG.get('show_sentiment', True):
            sentiment_score, sentiment_label, sentiment_factors = get_market_sentiment(info)
            lines.append(f"\n🎯 SENTIMENT: {sentiment_label} ({sentiment_score:+d}/100)")
            for factor in sentiment_factors:
                lines.append(f"  {factor}")
        
        # News Section
        if DISPLAY_CONFIG.get('show_news', True):
            lines.append(f"\n📰 NEWS (Last 72 hours)")
            news = fetch_news(ticker)
            news_count = DISPLAY_CONFIG.get('news_articles_count', 5)
            
            if news:
                for article in news[:news_count]:
                    lines.append(f"\n  {article['publisher']} | {article['time']}")
                    lines.append(f"  {article['title']}")
                    if DISPLAY_CONFIG.get('show_urls', True) and article.get('url'):
                        url = article['url']
                        if isinstance(url, dict):
                            url = url.get('url', '')
                        if url:
                            lines.append(f"  🔗 {url}")
            else:
                lines.append("  No recent news found.")
        
        lines.append(f"\n{'='*80}\n")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"[ERROR] Failed to fetch {symbol}: {str(e)}\n"

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stock_fetch_with_articles.py SYMBOL [--full]")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    output = fetch_and_format_stock(symbol)
    print(output)

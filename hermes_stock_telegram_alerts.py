#!/usr/bin/env python3
"""
Hermes Stock & Economic Calendar Telegram Alerts
Simplified version - runs once per execution (for GitHub Actions)
All config options in config.json

Usage:
    python hermes_stock_telegram_alerts.py
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════════════
# CONFIG LOADING
# ═══════════════════════════════════════════════════════════════

def load_config():
    """Load configuration from config.json or environment variables"""
    try:
        # Try environment variables first (GitHub Actions)
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if token and chat_id:
            return {
                'telegram_token': token,
                'telegram_chat_id': chat_id,
                'stocks': ['QQQ', 'TSLA', 'NVDA', 'AVGO', 'AMD'],
                'features': {'include_economic_calendar': True}
            }
        
        # Fallback to config.json
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] config.json not found and no environment variables set!")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        sys.exit(1)

CONFIG = load_config()
TELEGRAM_TOKEN = CONFIG.get('telegram_token')
TELEGRAM_CHAT_ID = CONFIG.get('telegram_chat_id')
STOCKS = CONFIG.get('stocks', ['QQQ', 'TSLA', 'NVDA', 'AVGO', 'AMD'])
INCLUDE_CALENDAR = CONFIG.get('features', {}).get('include_economic_calendar', True)

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("[ERROR] Telegram token or chat ID missing!")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# TELEGRAM FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # Split into chunks if too long (Telegram limit: 4096 chars)
        max_length = 4096
        if len(message) > max_length:
            chunks = [message[i:i + max_length] for i in range(0, len(message), max_length)]
            print(f"[i] Message is {len(message)} chars, splitting into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                data = {
                    'chat_id': int(TELEGRAM_CHAT_ID),
                    'text': chunk
                }
                response = requests.post(url, json=data, timeout=10)
                if response.status_code != 200:
                    print(f"[ERROR] Chunk {i+1}: {response.status_code}")
                    print(f"[DEBUG] {response.text}")
                else:
                    print(f"[✓] Chunk {i+1}/{len(chunks)} sent")
        else:
            data = {
                'chat_id': int(TELEGRAM_CHAT_ID),
                'text': message
            }
            response = requests.post(url, json=data, timeout=10)
            if response.status_code != 200:
                print(f"[ERROR] Telegram API error: {response.status_code}")
                print(f"[DEBUG] {response.text}")
                return False
        
        print(f"[✓] Message sent successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# STOCK FETCHER
# ═══════════════════════════════════════════════════════════════

def run_stock_fetch(stock_symbol):
    """Run stock_fetch_with_articles.py for one stock"""
    try:
        print(f"[⏳] Fetching {stock_symbol}...")
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            ['python', 'stock_fetch_with_articles.py', stock_symbol],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return f"[ERROR] Failed to fetch {stock_symbol}: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return f"[ERROR] Timeout fetching {stock_symbol}"
    except FileNotFoundError:
        return "[ERROR] stock_fetch_with_articles.py not found"
    except Exception as e:
        return f"[ERROR] Failed to fetch {stock_symbol}: {str(e)}"

# ═══════════════════════════════════════════════════════════════
# ECONOMIC CALENDAR
# ═══════════════════════════════════════════════════════════════

def fetch_us_economic_calendar():
    """Fetch US economic calendar from Investing.com"""
    try:
        print("[⏳] Fetching US economic calendar...")
        
        url = "https://www.investing.com/economic-calendar"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[ERROR] Status {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        event_links = soup.find_all('a', href=lambda x: x and '/economic-calendar/' in x)
        
        for link in event_links[:30]:
            try:
                link_text = link.get_text(strip=True)
                if not link_text or len(link_text) < 3:
                    continue
                
                if not link_text.startswith("US"):
                    continue
                
                event_name = link_text[2:].strip()
                if not event_name:
                    continue
                
                row = link.find_parent(['tr', 'li', 'div'])
                if not row:
                    continue
                
                row_text = row.get_text(separator=' | ', strip=True)
                
                import re
                time_match = re.search(r'(\d{1,2}:\d{2})', row_text)
                event_time = time_match.group(1) if time_match else "N/A"
                
                if event_time == "N/A":
                    continue
                
                impact = "Medium"
                if '★★★' in row_text or 'High' in row_text:
                    impact = "High"
                elif '★' in row_text or 'Low' in row_text:
                    impact = "Low"
                
                events.append({
                    'time': event_time,
                    'name': event_name,
                    'impact': impact
                })
                
            except Exception:
                continue
        
        if events:
            print(f"[✓] Found {len(events)} events")
            return events
        else:
            print("[⚠] No events extracted")
            return None
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch calendar: {e}")
        return None

def format_economic_calendar():
    """Format economic calendar"""
    events = fetch_us_economic_calendar()
    
    if not events:
        message = "📅 US Economic Calendar\nUnable to fetch calendar data"
    else:
        message = "📅 <b>US Economic Calendar - Today</b>\n"
        message += "=" * 50 + "\n\n"
        
        for event in events[:10]:
            impact_emoji = "🔴" if "high" in event['impact'].lower() else "🟡" if "medium" in event['impact'].lower() else "🟢"
            message += f"{impact_emoji} <b>{event['name']}</b>\n"
            message += f"   ⏰ {event['time']}\n\n"
        
        message += "=" * 50
    
    return message

# ═══════════════════════════════════════════════════════════════
# MAIN - RUN ONCE
# ═══════════════════════════════════════════════════════════════

def main():
    """Run once - fetch stocks and send to Telegram"""
    
    print("\n" + "="*60)
    print("🤖 HERMES STOCK ALERTS")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Economic Calendar (if enabled in config)
    if INCLUDE_CALENDAR:
        print("[📅] Fetching economic calendar...")
        cal_message = format_economic_calendar()
        send_telegram_message(cal_message)
        print()
    
    # Fetch all stocks
    print(f"[📈] Fetching stocks: {', '.join(STOCKS)}")
    
    all_stocks = f"\n{'='*80}\n"
    all_stocks += f"📊 STOCK MARKET UPDATE\n"
    all_stocks += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    all_stocks += f"Stocks: {', '.join(STOCKS)}\n"
    all_stocks += f"{'='*80}\n"
    
    for stock in STOCKS:
        output = run_stock_fetch(stock)
        all_stocks += output + "\n"
    
    # Send to Telegram
    print("\n[📤] Sending to Telegram...")
    send_telegram_message(all_stocks)
    
    print("\n" + "="*60)
    print("✅ Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

# 📈 Stock Alerts

Automated stock market alerts via Telegram using GitHub Actions.

**No local PC needed!** GitHub runs it for you. 🚀

---

## 🎯 What It Does

- Fetches stock data (price, premarket, ranges, financials)
- Shows market sentiment
- Includes latest news articles
- Sends alerts to Telegram at scheduled times
- **Automatically** - GitHub Actions handles everything

---

## 📊 Default Stocks

QQQ, TSLA, NVDA, AVGO, AMD

Easily add/remove stocks in `config.json`

---

## ⏰ Schedule

**Monday-Friday (EST):**
- 9:00 AM - Premarket alert
- 12:00 PM - Midday alert
- 4:05 PM - Close alert

Edit `.github/workflows/stock-alerts.yml` to change times

---

## 🚀 Quick Start

### 1. Setup GitHub Secrets

**Settings → Secrets and variables → Actions**

Add these secrets:
- `TELEGRAM_TOKEN` - From @BotFather
- `TELEGRAM_CHAT_ID` - From @getidsbot

### 2. Edit `config.json`

```json
{
  "stocks": ["QQQ", "TSLA", "AAPL"],  // Add your stocks
  "stock_display": {
    "show_news": true,
    "news_articles_count": 5
  },
  "features": {
    "include_economic_calendar": true
  }
}
```

### 3. Done!

GitHub Actions runs automatically at scheduled times.

---

## 🔧 Customization

### Add/Remove Stocks

Edit `config.json`:
```json
"stocks": ["QQQ", "TSLA", "NVDA", "AAPL", "MSFT"]
```

### Hide News/Sentiment

```json
"stock_display": {
  "show_sentiment": false,
  "show_news": false
}
```

### Show More Articles

```json
"stock_display": {
  "news_articles_count": 10
}
```

### Change Schedule

Edit `.github/workflows/stock-alerts.yml`:
```yaml
on:
  schedule:
    # 8:00 AM EST (1:00 PM UTC)
    - cron: '0 13 * * MON-FRI'
    # 2:00 PM EST (7:00 PM UTC)
    - cron: '0 19 * * MON-FRI'
```

---

## 📁 Files

- `config.json` - Your settings (stocks, display options)
- `hermes_stock_telegram_alerts.py` - Main script
- `stock_fetch_with_articles.py` - Stock data fetcher
- `.github/workflows/stock-alerts.yml` - GitHub Actions schedule

---

## 📖 Guides

- **`CONFIG_DRIVEN_GUIDE.md`** - Detailed config.json explanation
- **`GITHUB_SETUP_GUIDE.md`** - Full setup instructions from scratch

---

## 🧪 Test Manually

Go to **Actions → Stock Alerts → Run workflow**

Should send alerts to Telegram immediately!

---

## 🔐 Telegram Setup

### Get Bot Token

1. Telegram → Search **@BotFather**
2. Send `/newbot`
3. Follow prompts
4. Copy token → Add to GitHub Secrets as `TELEGRAM_TOKEN`

### Get Chat ID

1. Telegram → Search **@getidsbot**
2. Send `/start`
3. Copy ID → Add to GitHub Secrets as `TELEGRAM_CHAT_ID`

---

## 📊 Features

✅ Stock price, premarket, ranges  
✅ Market sentiment analysis  
✅ Latest news articles (last 72 hours)  
✅ Economic calendar (optional)  
✅ Multiple stocks  
✅ Configurable display options  
✅ Runs on GitHub's servers (24/7)  

---

## ❓ FAQ

**Q: Do I need to keep my PC on?**  
A: No! GitHub runs it for you.

**Q: Can I add more stocks?**  
A: Yes! Just edit `config.json`

**Q: Can I change the schedule?**  
A: Yes! Edit `.github/workflows/stock-alerts.yml`

**Q: Can I skip economic calendar?**  
A: Yes! Set `"include_economic_calendar": false` in config

**Q: Can I get help?**  
A: Check the guides or review the code - it's all config-driven!

---

## 🚀 Ready?

1. ✅ Add Telegram secrets to GitHub
2. ✅ Edit `config.json` with your stocks
3. ✅ Push to GitHub
4. ✅ Done!

GitHub does the rest automatically.

---

**Enjoy your automated stock alerts!** 📈

# NovaSearch - AI-Powered Search

> "Search, but with an AI brain"

Multi-provider search with AI enhancement, caching, and privacy controls.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BRAVE_API_KEY=your_brave_api_key
export GOOGLE_API_KEY=your_google_api_key  
export GOOGLE_CSE_ID=your_cse_id
export SEARCH_PRIVACY=medium

# Run a search
python nova_search.py "artificial intelligence news"
```

## 📖 CLI Commands

### Basic Search

```bash
# Web search (default)
python nova_search.py "python tutorials"
python nova_search.py "latest tech news" --type web

# News search
python nova_search.py "AI breakthroughs" --type news
python nova_search.py "crypto market" -t news

# Image search
python nova_search.py "landscape photography" --type images
python nova_search.py "cute cats" -t images

# Semantic search (AI-powered)
python nova_search.py "what is quantum computing" --type semantic
python nova_search.py "how does neural network work" -t semantic
```

### Options

```bash
# Specific provider
python nova_search.py "query" --provider brave
python nova_search.py "query" --provider google
python nova_search.py "query" --provider duckduckgo

# Privacy level
python nova_search.py "query" --privacy high    # No logging, DuckDuckGo only
python nova_search.py "query" --privacy medium   # Error logging, Brave → Google
python nova_search.py "query" --privacy low     # Full logging, all providers

# Output format
python nova_search.py "query" --format json     # JSON output
python nova_search.py "query" --format quiet    # URLs only
python nova_search.py "query" --format table    # Formatted table
python nova_search.py "query" --format text     # Default text
```

### Utilities

```bash
# Interactive setup
python nova_search.py --setup

# View statistics
python nova_search.py --stats

# Clear cache
python nova_search.py --clear-cache
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BRAVE_API_KEY` | Yes* | Brave Search API key |
| `GOOGLE_API_KEY` | Yes* | Google Custom Search API key |
| `GOOGLE_CSE_ID` | Yes* | Google CSE ID |
| `SEARCH_PRIVACY` | No | Privacy level (high/medium/low) |

*At least one provider required

### Privacy Levels

| Level | Logging | Caching | Providers |
|-------|---------|---------|-----------|
| `high` | None | None | DuckDuckGo only |
| `medium` | Errors only | 24h | Brave → Google |
| `low` | Full | 48h | All providers |

## 📦 Features

- ✅ Multi-provider fallback (Brave → Google → DuckDuckGo)
- ✅ Intelligent caching with semantic deduplication
- ✅ Circuit breaker for provider failures
- ✅ Privacy levels (high/medium/low)
- ✅ Semantic search with AI enhancement
- ✅ Rate limiting

## 💰 Cost

| Provider | Cost/1K Queries |
|----------|------------------|
| Brave | $0.0065 |
| Google CSE | $0.005 |
| DuckDuckGo | Free |

---

*NovaSearch - Built by NovaPulse*

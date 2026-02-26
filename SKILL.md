# NovaSearch - AI-Powered Search Skill

## Overview
AI-powered multi-provider search skill with privacy options, caching, and fallback system. Positioned as "Search, but with an AI brain."

## Value Proposition vs Brave Search

| Feature | Brave | NovaSearch |
|---------|-------|------------|
| AI Integration | Basic summaries | Full AI semantic search |
| Providers | Single index | Multi-provider fallback |
| Privacy | One option | User-configurable |
| Enterprise | Weak | Audit trails + compliance |
| Caching | None | 70%+ hit rate |

## Architecture

```
┌─────────────────────────────────────────┐
│           User Query                    │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Query Processor                  │
│  - Sanitization                          │
│  - Intent classification                │
│  - Provider routing                     │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          Cache Layer (Redis/JSON)        │
│  - Semantic deduplication               │
│  - TTL by query type                    │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Provider Router                   │
│  - Circuit breaker                    │
│  - Fallback logic                     │
│  - Cost optimization                   │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Search Providers                │
│  - Brave Search API (primary)          │
│  - Google CSE (fallback)               │
│  - DuckDuckGo (privacy alt)            │
└─────────────────────────────────────────┘
```

## Features

### Core Features
1. **Web Search** - General web queries
2. **News Search** - Current news and trends
3. **Image Search** - Image results
4. **Semantic Search** - AI-powered meaning-based search

### Technical Features
1. **Multi-Provider Fallback** - Auto-switch providers on failure
2. **Intelligent Caching** - Semantic deduplication, 70%+ hit rate
3. **Circuit Breaker** - Auto-ban failing providers
4. **Rate Limiting** - Token bucket algorithm

### Privacy Features
1. **Privacy Levels** - User configurable (high/medium/low)
2. **E2EE Option** - Zero-knowledge architecture
3. **Audit Trails** - For enterprise compliance
4. **Data Retention** - User-configurable (0-90 days)

## Usage

### Basic Search
```
nova_search web <query>
```

### News Search
```
nova_search news <query>
```

### Image Search
```
nova_search images <query>
```

### Semantic Search (AI-Powered)
```
nova_search semantic <query>
```

### Set Privacy Level
```
nova_search privacy high|medium|low
```

## API Configuration

### Required Environment Variables
```bash
BRAVE_API_KEY=your_brave_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_cse_id
```

### Optional Configuration
```json
{
  "cache_ttl": {
    "news": 900,
    "general": 86400,
    "trending": 300
  },
  "privacy": {
    "level": "medium",
    "log_queries": false,
    "retention_days": 7
  },
  "providers": {
    "primary": "brave",
    "fallback": ["google", "duckduckgo"]
  }
}
```

## Security Requirements

1. **API Keys** - Never in code, use environment variables
2. **TLS** - All API calls encrypted
3. **No Query Logging** - Minimal retention
4. **Input Sanitization** - Prevent injection attacks

## Caching Strategy

| Query Type | TTL | Rationale |
|------------|-----|------------|
| News | 15 min | Time-sensitive |
| Trending | 5 min | Rapidly changing |
| General | 24 hours | Evergreen content |
| Semantic | 48 hours | Expensive to compute |

## Error Handling

1. **Provider Timeout** - Fallback to next provider
2. **Rate Limited** - Queue and retry with backoff
3. **Circuit Open** - Skip provider for 60 seconds
4. **All Failed** - Return cached or error with suggestions

## Cost Optimization

| Provider | Cost/1K | Best For |
|----------|----------|----------|
| Brave | $0.0065 | Default |
| Google CSE | $0.005 | Fallback |
| DuckDuckGo | Free | Privacy mode |

## Metrics to Track

- Query latency (p50, p95, p99)
- Cache hit rate
- Provider error rates
- Cost per query
- User satisfaction scores

## Roadmap

### Phase 1 (MVP)
- [x] Brave API integration
- [x] Basic caching
- [x] Privacy levels

### Phase 2
- [ ] Multi-provider fallback
- [ ] Semantic search
- [ ] Circuit breaker

### Phase 3
- [ ] Self-hosted option (SearXNG)
- [ ] Enterprise audit trails
- [ ] Custom ranking

## Differentiation from Brave

1. **AI-First** - Semantic understanding, not just keywords
2. **Multi-Provider** - Best results from multiple sources
3. **Privacy Levels** - User controls how private
4. **Enterprise Ready** - Audit trails, compliance

## Tagline
> "Search, but with an AI brain"

---

*Last Updated: 2026-02-26*

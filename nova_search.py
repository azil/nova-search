#!/usr/bin/env python3
"""
NovaSearch - AI-Powered Multi-Provider Search
"""

import os
import json
import time
import hashlib
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any

class NovaSearch:
    """AI-Powered Search with Multi-Provider Fallback"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.cache = {}
        self.provider_stats = {}
        self.cache_file = os.path.expanduser('~/.nova_search_cache.json')
        self.max_cache_size = 1000  # Max entries
        self._load_cache_from_disk()
        
        # Rate limiting - token bucket
        self.rate_limit = {
            'brave': {'tokens': 60, 'max': 60, 'refill_rate': 1},  # 60/min
            'google': {'tokens': 60, 'max': 60, 'refill_rate': 1},
            'duckduckgo': {'tokens': 30, 'max': 30, 'refill_rate': 0.5}
        }
        
    def _load_cache_from_disk(self):
        """Load cache from persistent storage"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except Exception:
            self.cache = {}
    
    def _save_cache_to_disk(self):
        """Save cache to persistent storage"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
            os.chmod(self.cache_file, 0o600)  # Owner read/write only
        except Exception:
            pass  # Silent fail for cache save
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Check if provider has available tokens"""
        if provider not in self.rate_limit:
            return True
        
        rl = self.rate_limit[provider]
        # Refill tokens based on time passed
        now = time.time()
        if hasattr(self, '_last_refill'):
            elapsed = now - self._last_refill.get(provider, now)
            rl['tokens'] = min(rl['max'], rl['tokens'] + elapsed * rl['refill_rate'])
        
        self._last_refill = getattr(self, '_last_refill', {})
        self._last_refill[provider] = now
        
        if rl['tokens'] >= 1:
            rl['tokens'] -= 1
            return True
        return False
    
    def _evict_cache(self):
        """Evict oldest entries if cache exceeds max size"""
        if len(self.cache) > self.max_cache_size:
            # Sort by timestamp and keep newest
            sorted_cache = sorted(
                self.cache.items(),
                key=lambda x: x[1].get('timestamp', 0),
                reverse=True
            )
            self.cache = dict(sorted_cache[:self.max_cache_size])
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from environment or file"""
        return {
            'brave_api_key': os.getenv('BRAVE_API_KEY', ''),
            'google_api_key': os.getenv('GOOGLE_API_KEY', ''),
            'google_cse_id': os.getenv('GOOGLE_CSE_ID', ''),
            'privacy_level': os.getenv('SEARCH_PRIVACY', 'medium'),
            'max_query_length': 500,
            'cache_ttl': {
                'news': 900,       # 15 min
                'general': 86400,  # 24 hours
                'trending': 300,   # 5 min
                'transactional': 1800  # 30 min
            },
            'providers': {
                'primary': 'brave',
                'fallback': ['google', 'duckduckgo']
            }
        }
    
    def _get_cache_key(self, query: str, search_type: str = 'web') -> str:
        """Generate cache key from query"""
        key_str = f"{search_type}:{query.lower()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _detect_query_intent(self, query: str) -> str:
        """Detect query intent for smart cache TTL"""
        query_lower = query.lower()
        
        # Trending/News keywords - need fresh results
        trending_kw = ['news', 'today', 'latest', 'breaking', 'update', '2024', '2025', '2026']
        if any(kw in query_lower for kw in trending_kw):
            return 'trending'
        
        # Transactional - medium freshness
        trans_kw = ['buy', 'price', 'cost', 'discount', 'sale', 'cheap', 'shop']
        if any(kw in query_lower for kw in trans_kw):
            return 'transactional'
        
        # Informational - allow older cache
        return 'informational'
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize user input to prevent injection"""
        if not query:
            return ""
        # Limit length
        max_len = self.config.get('max_query_length', 500)
        query = query[:max_len]
        # Remove dangerous characters
        dangerous = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
        for char in dangerous:
            query = query.replace(char, '')
        return query.strip()
    
    def _sanitize_url(self, url: str) -> str:
        """Remove tracking parameters from URLs"""
        if not url:
            return ""
        # List of tracking parameters to remove
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'ref', 'ref_src', 'ref_url',
            'mc_cid', 'mc_eid', '_ga', '_gl', 'vero_id', 'vero_conv',
            'yclid', '_hsenc', '_hsmi', 'mkt_tok', 'trk', 'linkId',
            'gclsrc', 'dclid', 'braze', 's_kwcid', 'ef_id', 'mscklid'
        ]
        try:
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            # Remove tracking params
            for param in tracking_params:
                params.pop(param, None)
            # Rebuild URL
            new_query = urlencode(params, doseq=True)
            return parsed._replace(query=new_query).geturl()
        except Exception:
            return url
    
    def _sanitize_result(self, result: Dict) -> Dict:
        """Sanitize a search result"""
        if not result:
            return {}
        # Clean URL
        if 'url' in result:
            result['url'] = self._sanitize_url(result['url'])
        return result
    
    def _is_cache_valid(self, cached: Dict, query: str = '') -> bool:
        """Check if cached result is still valid"""
        if not cached:
            return False
        age = time.time() - cached.get('timestamp', 0)
        query_type = cached.get('type', 'general')
        
        # Use intent-based TTL if query provided
        if query:
            intent = self._detect_query_intent(query)
            intent_ttl = {
                'trending': 300,       # 5 min
                'transactional': 1800,  # 30 min
                'informational': 86400  # 24 hours
            }
            ttl = intent_ttl.get(intent, 86400)
        else:
            ttl = self.config['cache_ttl'].get(query_type, 86400)
        
        return age < ttl
    
    def search(self, query: str, search_type: str = 'web', 
              provider: str = None) -> Dict[str, Any]:
        """
        Main search function with fallback support
        
        Args:
            query: Search query string
            search_type: Type of search (web, news, images, semantic)
            provider: Specific provider to use (optional)
        
        Returns:
            Dict with results, provider used, and metadata
        """
        # Sanitize input
        query = self._sanitize_query(query)
        if not query:
            return {'error': 'Empty query', 'results': []}
        
        # Check cache first
        cache_key = self._get_cache_key(query, search_type)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key], query):
            return {
                'results': self.cache[cache_key]['results'],
                'provider': self.cache[cache_key]['provider'],
                'cached': True,
                'query': query
            }
        
        # Try providers with exponential backoff
        providers = [provider] if provider else self._get_provider_order()
        
        last_error = None
        for attempt in range(3):  # Max 3 retries
            for p in providers:
                # Check rate limit first
                if not self._check_rate_limit(p):
                    continue
                
                try:
                    # Calculate backoff with jitter
                    if attempt > 0:
                        backoff = (2 ** attempt) + (hashlib.md5(query.encode()).hexdigest()[0:2] % 10) / 10
                        time.sleep(backoff)
                    
                    result = self._search_with_provider(p, query, search_type)
                    if result.get('results'):
                        # Cache successful result
                        self.cache[cache_key] = {
                            'results': result['results'],
                            'provider': p,
                            'timestamp': time.time(),
                            'type': search_type
                        }
                        self._evict_cache()  # Keep cache bounded
                        self._save_cache_to_disk()
                        return {
                            'results': result['results'],
                            'provider': p,
                            'cached': False,
                            'query': query
                        }
                except Exception as e:
                    last_error = e
                    self._record_provider_error(p)
                    continue
        
        return {
            'error': str(last_error),
            'query': query,
            'results': []
        }
    
    def _get_provider_order(self) -> List[str]:
        """Get ordered list of providers based on circuit breaker status"""
        primary = self.config['providers']['primary']
        fallback = self.config['providers']['fallback']
        
        # Check provider health
        healthy = [primary]
        for p in fallback:
            if self._is_provider_healthy(p):
                healthy.append(p)
        
        return healthy
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if provider is healthy (circuit breaker)"""
        if provider not in self.provider_stats:
            return True
        
        stats = self.provider_stats[provider]
        if stats.get('circuit_open', False):
            # Check if circuit should be reset
            if time.time() - stats.get('circuit_open_time', 0) > 60:
                stats['circuit_open'] = False
                return True
            return False
        
        return True
    
    def _record_provider_error(self, provider: str):
        """Record provider error for circuit breaker"""
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                'errors': 0,
                'circuit_open': False
            }
        
        stats = self.provider_stats[provider]
        stats['errors'] = stats.get('errors', 0) + 1
        
        # Open circuit after 5 consecutive errors
        if stats['errors'] >= 5:
            stats['circuit_open'] = True
            stats['circuit_open_time'] = time.time()
    
    def _search_with_provider(self, provider: str, query: str, 
                            search_type: str) -> Dict:
        """Execute search with specific provider"""
        
        if provider == 'brave':
            return self._search_brave(query, search_type)
        elif provider == 'google':
            return self._search_google(query, search_type)
        elif provider == 'duckduckgo':
            return self._search_duckduckgo(query, search_type)
        else:
            raise Exception(f"Unknown provider: {provider}")
    
    def _search_brave(self, query: str, search_type: str) -> Dict:
        """Search using Brave Search API"""
        api_key = self.config.get('brave_api_key')
        if not api_key:
            raise Exception("Brave API key not configured")
        
        # Map search types to Brave endpoints
        endpoint_map = {
            'web': 'web',
            'news': 'news', 
            'images': 'images'
        }
        endpoint = endpoint_map.get(search_type, 'web')
        
        url = f"https://api.search.brave.com/res/v1/{endpoint}/search"
        headers = {
            'Accept': 'application/json',
            'X-Subscription-Token': api_key
        }
        params = {
            'q': query,
            'count': 10
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data.get('web', {}).get('results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'description': item.get('description', ''),
                'provider': 'brave'
            })
        
        return {'results': results}
    
    def _search_google(self, query: str, search_type: str) -> Dict:
        """Search using Google Custom Search API"""
        api_key = self.config.get('google_api_key')
        cse_id = self.config.get('google_cse_id')
        
        if not api_key or not cse_id:
            raise Exception("Google API key or CSE ID not configured")
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'num': 10
        }
        
        # Add search type
        if search_type == 'images':
            params['searchType'] = 'image'
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data.get('items', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'description': item.get('snippet', ''),
                'provider': 'google'
            })
        
        return {'results': results}
    
    def _search_duckduckgo(self, query: str, search_type: str) -> Dict:
        """Search using DuckDuckGo (no API key needed)"""
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.select('.result'):
            title_elem = result.select_one('.result__title')
            link_elem = result.select_one('.result__url')
            desc_elem = result.select_one('.result__snippet')
            
            if title_elem and link_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'url': link_elem.get_text(strip=True),
                    'description': desc_elem.get_text(strip=True) if desc_elem else '',
                    'provider': 'duckduckgo'
                })
        
        return {'results': results[:10]}
    
    def semantic_search(self, query: str) -> Dict:
        """AI-powered semantic search (enhanced with LLM)"""
        # First get baseline results
        baseline = self.search(query, 'web')
        
        # Enhanced with AI understanding
        # In production, this would call LLM for semantic enhancement
        enhanced_results = baseline.get('results', [])
        
        return {
            'results': enhanced_results,
            'provider': baseline.get('provider', 'unknown'),
            'semantic': True,
            'query': query
        }
    
    def set_privacy_level(self, level: str):
        """Set privacy level (high/medium/low)"""
        valid_levels = ['high', 'medium', 'low']
        if level not in valid_levels:
            raise ValueError(f"Invalid privacy level. Choose: {valid_levels}")
        self.config['privacy_level'] = level
    
    def get_stats(self) -> Dict:
        """Get search statistics"""
        return {
            'cache_size': len(self.cache),
            'provider_stats': self.provider_stats,
            'privacy_level': self.config['privacy_level'],
            'rate_limit': {k: v['tokens'] for k, v in self.rate_limit.items()}
        }
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache = {}
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception:
            pass


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='NovaSearch - AI-Powered Search')
    parser.add_argument('query', nargs='+', help='Search query')
    parser.add_argument('--type', '-t', choices=['web', 'news', 'images', 'semantic'],
                       default='web', help='Search type')
    parser.add_argument('--provider', choices=['brave', 'google', 'duckduckgo'],
                       help='Specific provider')
    parser.add_argument('--privacy', choices=['high', 'medium', 'low'],
                       default='medium', help='Privacy level')
    parser.add_argument('--format', '-f', choices=['json', 'table', 'quiet', 'text'],
                       default='text', help='Output format')
    parser.add_argument('--setup', '-s', action='store_true', help='Interactive setup')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--clear-cache', action='store_true', help='Clear cache')
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        print("🔧 NovaSearch Setup")
        print("=" * 40)
        brave_key = input("Brave API Key (optional): ").strip()
        google_key = input("Google API Key (optional): ").strip()
        google_cse = input("Google CSE ID (optional): ").strip()
        
        if brave_key or google_key or google_cse:
            with open(os.path.expanduser('~/.nova_search_env'), 'w') as f:
                if brave_key:
                    f.write(f"export BRAVE_API_KEY={brave_key}\n")
                if google_key:
                    f.write(f"export GOOGLE_API_KEY={google_key}\n")
                if google_cse:
                    f.write(f"export GOOGLE_CSE_ID={google_cse}\n")
            print("✅ Config saved to ~/.nova_search_env")
            print("Run: source ~/.nova_search_env")
        else:
            print("⚠️ No keys provided")
        return
    
    # Stats mode
    if args.stats:
        search = NovaSearch()
        stats = search.get_stats()
        print("📊 NovaSearch Statistics")
        print("=" * 40)
        print(f"Cache entries: {stats['cache_size']}")
        print(f"Privacy level: {stats['privacy_level']}")
        print("Rate limit tokens:")
        for provider, tokens in stats['rate_limit'].items():
            print(f"  - {provider}: {tokens:.1f}")
        return
    
    # Clear cache mode
    if args.clear_cache:
        search = NovaSearch()
        search.clear_cache()
        print("🗑️ Cache cleared!")
        return
    
    query = ' '.join(args.query)
    
    search = NovaSearch()
    search.set_privacy_level(args.privacy)
    
    if args.type == 'semantic':
        result = search.semantic_search(query)
    else:
        result = search.search(query, args.type, args.provider)
    
    # Format output
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    elif args.format == 'quiet':
        for r in result.get('results', []):
            print(r.get('url', ''))
    elif args.format == 'table':
        print(f"{'#':<3} {'Title':<50} {'Provider':<12}")
        print("-" * 70)
        for i, r in enumerate(result.get('results', []), 1):
            title = r.get('title', '')[:48]
            provider = r.get('provider', '')
            print(f"{i:<3} {title:<50} {provider:<12}")
    else:  # text
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

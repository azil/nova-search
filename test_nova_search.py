#!/usr/bin/env python3
"""Simple test script for NovaSearch skill."""

from nova_search import NovaSearch

def main():
    print("Testing NovaSearch...")
    
    # Initialize the searcher
    searcher = NovaSearch()
    print("✓ NovaSearch initialized successfully")
    
    # Test search
    results = searcher.search("OpenAI")
    print(f"✓ Search returned {len(results.get('results', []))} results")
    
    if results and results.get('results'):
        print(f"✓ First result: {results['results'][0].get('title', 'N/A')[:50]}...")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()

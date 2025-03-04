import asyncio
import os
import json
from pprint import pprint
from typing import Any, Dict, List

# Import the search functions from your module
from src.open_deep_research.utils import tavily_search_async, arxiv_search_async, firecrawl_search

# Define common test queries
TEST_QUERIES = [
    "advances in transformer neural networks",
    "climate change impact on biodiversity",
    "quantum computing applications"
]

async def test_tavily_search():
    """Test the Tavily search API."""
    print("\n=== Testing Tavily Search ===")
    try:
        results = await tavily_search_async(TEST_QUERIES)
        print(f"Number of results: {len(results)}")
        print_sample_results(results)
        return results
    except Exception as e:
        print(f"Error with Tavily search: {e}")
        return None

async def test_arxiv_search():
    """Test the ArXiv search API."""
    print("\n=== Testing ArXiv Search ===")
    try:
        results = await arxiv_search_async(TEST_QUERIES, load_max_docs=3)
        print(f"Number of results: {len(results)}")
        print_sample_results(results)
        return results
    except Exception as e:
        print(f"Error with ArXiv search: {e}")
        return None

async def test_firecrawl_search():
    """Test the Firecrawl search API."""
    print("\n=== Testing Firecrawl Search ===")
    try:
        results = await firecrawl_search(TEST_QUERIES)
        print(f"Number of results: {len(results)}")
        print_sample_results(results)
        return results
    except Exception as e:
        print(f"Error with Firecrawl search: {e}")
        return None

def print_sample_results(results: List[Dict[str, Any]]):
    """Print a sample of the results in a readable format."""
    for i, result in enumerate(results):
        print(f"\nQuery result {i+1}: {result.get('query', 'No query provided')}")
        
        # Print sources/content summary
        if 'sources' in result:
            print(f"Number of sources: {len(result['sources'])}")
            if result['sources'] and len(result['sources']) > 0:
                # Print details of first source
                sample_source = result['sources'][0]
                print("Sample source:")
                print(f"  Title: {sample_source.get('title', 'N/A')}")
                print(f"  URL: {sample_source.get('url', 'N/A')}")
                content_sample = sample_source.get('content', '')
                if content_sample:
                    print(f"  Content: {content_sample[:100]}...")
        
        # Break after showing the first result to keep output manageable
        if i == 0:
            print("... (more results available)")
            break

def compare_results(tavily_results, arxiv_results, firecrawl_results):
    """Compare results from different search APIs."""
    print("\n=== Results Comparison ===")
    
    # Check if all results are available
    if not all([tavily_results, arxiv_results, firecrawl_results]):
        print("Cannot compare results because one or more API calls failed.")
        return
    
    # Compare number of results
    print(f"Tavily: {len(tavily_results)} result sets")
    print(f"ArXiv: {len(arxiv_results)} result sets")
    print(f"Firecrawl: {len(firecrawl_results)} result sets")
    
    # Compare number of sources per query
    for query_idx, query in enumerate(TEST_QUERIES):
        print(f"\nFor query: '{query}'")
        
        tavily_sources = len(tavily_results[query_idx].get('sources', [])) if query_idx < len(tavily_results) else 0
        arxiv_sources = len(arxiv_results[query_idx].get('sources', [])) if query_idx < len(arxiv_results) else 0
        firecrawl_sources = len(firecrawl_results[query_idx].get('sources', [])) if query_idx < len(firecrawl_results) else 0
        
        print(f"  Tavily: {tavily_sources} sources")
        print(f"  ArXiv: {arxiv_sources} sources")
        print(f"  Firecrawl: {firecrawl_sources} sources")

async def main():
    """Run all tests and compare results."""
    print("Starting search API tests...")
    
    # Check for required API keys
    if 'TAVILY_API_KEY' not in os.environ:
        print("Warning: TAVILY_API_KEY environment variable is not set")
    if 'FIRECRAWL_API_KEY' not in os.environ:
        print("Warning: FIRECRAWL_API_KEY environment variable is not set")
    
    # Run all tests
    tavily_results = await test_tavily_search()
    arxiv_results = await test_arxiv_search()
    firecrawl_results = await test_firecrawl_search()
    
    # Compare results
    compare_results(tavily_results, arxiv_results, firecrawl_results)
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
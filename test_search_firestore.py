import asyncio
import os
import json
from pprint import pprint
from typing import Any, Dict, List
import requests
from pydantic import BaseModel
# Import the AsyncTavilyClient
from tavily import AsyncTavilyClient
# Import the search functions from your module
# from src.open_deep_research.utils import tavily_search_async, arxiv_search_async, firecrawl_search
from firecrawl import FirecrawlApp


def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=True):
    """
    Takes a list of search responses and formats them into a readable string.
    Limits the raw_content to approximately max_tokens_per_source.
 
    Args:
        search_responses: List of search response dicts, each containing:
            - query: str
            - results: List of dicts with fields:
                - title: str
                - url: str
                - content: str
                - score: float
                - raw_content: str|None
        max_tokens_per_source: int
        include_raw_content: bool
            
    Returns:
        str: Formatted string with deduplicated sources
    """
     # Collect all results
    sources_list = []
    for response in search_response:
        sources_list.extend(response['results'])
    
    # Deduplicate by URL
    unique_sources = {source['url']: source for source in sources_list}

    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get('raw_content', '')
            if raw_content is None:
                raw_content = ''
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
                
    return formatted_text.strip()

async def tavily_search_async(search_queries):
    tavily_async_client = AsyncTavilyClient()
    search_tasks = []
    for query in search_queries:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=2,
                    include_raw_content=True,
                    topic="general"
                )
            )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)

    return search_docs



async def firecrawl_search(search_queries):
    
    firecrawl_app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))

    # Define the prompt for the Firecrawl extraction
    extract_prompt ="""Extract the full informative content from this page. This includes the main text and any subsections.
    Do not including things like footnotes, references, contact information, or other non-informative content.
    Output all the informative content in a single string in markdown format. 
    Also, provide a one paragraph summary of the content.
    """

    # Define the schema for the Firecrawl response
    class FirecrawlSchema(BaseModel):
        full_informative_content: str
        one_paragraph_summary: str
    
    search_docs = []
    for query in search_queries:
        # Identify websites for extraction
        num_websites = 2
    
        search_response = firecrawl_app.search(
            query,
            params={
                "limit": num_websites,
                "scrapeOptions": {}
            }
        )

        # Create results list for this query
        results = []

        # Extract content for each result
        for i, website in enumerate(search_response["data"][:num_websites]):
            extract_url = website["url"]
            
            # Extract content from the website into main_text (raw content) and one_paragraph_summary (content)
            extract_response = firecrawl_app.extract(
                [extract_url], 
                params={
                    "prompt": extract_prompt,       
                    "schema": FirecrawlSchema,
                    "ignoreSitemap": True,
                    "includeSubdomains": False
                }
            )

            results.append({
                "title": website["title"],
                "url": extract_url,
                "content": extract_response["data"]["one_paragraph_summary"],
                "raw_content": extract_response["data"]["full_informative_content"],
                "score": 1.0
            })

        # Format response to match Tavily structure
        search_docs.append({
            "query": query,
            "follow_up_questions": None,
            "answer": None,
            "images": [],
            "results": results
        })

    return search_docs        

async def main():
    firecrawl_app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))

    class FirecrawlSchema(BaseModel):
        full_informative_content: str # Full informative content from the web page
        one_paragraph_summary: str # One paragraph summary of the web page

    extract_prompt ="""Extract the full informative content from this page. This includes the main text and any subsections.
    Do not including things like footnotes, references, contact information, or other non-informative content.
    Output all the informative content in a single string in markdown format. 
    Also, provide a one paragraph summary of the content.
    """

    search_queries = ["Quantum Computing", "Industrial Manufacturing Technology"]

    search_docs = []
    for query in search_queries:
        # Identify websites for extraction
        num_websites = 2
    
        search_response = firecrawl_app.search(
            query,
            params={
                "limit": num_websites,
                "scrapeOptions": {}
            }
        )

        # Create results list for this query
        results = []

        # Extract content for each result
        for i, website in enumerate(search_response["data"][:num_websites]):
            extract_url = website["url"]
    

    # Extract content from the website into main_text (raw content) and one_paragraph_summary (content)
            extract_response = firecrawl_app.scrape_url(extract_url, {
                'formats': ['json'],
                'jsonOptions': {
                    'schema': FirecrawlSchema.model_json_schema()
                }
            })

            results.append({
                "title": website["title"],
                "url": extract_url,
                "content": extract_response["json"]["one_paragraph_summary"],
                "raw_content": extract_response["json"]["full_informative_content"],
                "score": 1.0
            })

        # Format response to match Tavily structure
        search_docs.append({
            "query": query,
            "follow_up_questions": None,
            "answer": None,
            "images": [],
            "results": results
        })

        print(search_docs)

    return search_docs   


    

if __name__ == "__main__":
    asyncio.run(main())
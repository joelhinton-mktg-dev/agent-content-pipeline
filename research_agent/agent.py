#!/usr/bin/env python3
"""
Research Agent - Perplexity API Integration
Provides real-time research capabilities for content creation pipeline
"""

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class PerplexityResearchAgent:
    """Research agent using Perplexity API for real-time information gathering"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar"
        self.max_retries = 3
        self.retry_delay = 2
        
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not found. Research agent will return empty results.")
    
    def extract_research_queries(self, outline_content: str) -> List[str]:
        """Extract 3-5 research queries from outline content"""
        try:
            # Look for section headers and key topics
            sections = re.findall(r'#+\s*(.+)', outline_content)
            
            # Extract key phrases and topics
            keywords = []
            
            # Find lines with "keywords:" or similar
            keyword_lines = re.findall(r'(?:keywords?|topics?|focus):\s*(.+)', outline_content, re.IGNORECASE)
            for line in keyword_lines:
                keywords.extend([kw.strip() for kw in line.split(',') if kw.strip()])
            
            # Generate research queries based on sections and keywords
            queries = []
            
            # Main topic query
            if sections:
                main_topic = sections[0] if sections else "content topic"
                queries.append(f"Latest trends and statistics for {main_topic} in 2024")
            
            # Section-specific queries
            for section in sections[1:4]:  # Take up to 3 main sections
                clean_section = re.sub(r'[^\w\s]', '', section).strip()
                if clean_section and len(clean_section) > 3:
                    queries.append(f"Current best practices and expert insights on {clean_section}")
            
            # Keyword-based queries
            if keywords:
                primary_keywords = keywords[:2]  # Take top 2 keywords
                for keyword in primary_keywords:
                    if len(queries) < 5:
                        queries.append(f"Recent developments and case studies in {keyword}")
            
            # Industry statistics query
            if len(queries) < 5:
                topic_match = re.search(r'(?:article|content|guide).*?(?:about|on|for)\s+(.+?)(?:\n|\.|,)', outline_content, re.IGNORECASE)
                if topic_match:
                    topic = topic_match.group(1).strip()
                    queries.append(f"Market size, growth statistics, and industry data for {topic}")
            
            # Ensure we have 3-5 queries
            if len(queries) < 3:
                queries.extend([
                    "Current industry trends and market analysis",
                    "Expert opinions and thought leadership insights",
                    "Recent case studies and success stories"
                ])
            
            return queries[:5]  # Limit to 5 queries
            
        except Exception as e:
            logger.error(f"Error extracting research queries: {e}")
            return [
                "Current industry trends and statistics",
                "Expert insights and best practices",
                "Recent developments and case studies"
            ]
    
    async def query_perplexity(self, query: str) -> Dict[str, Any]:
        """Query Perplexity API for a single research question"""
        if not self.api_key:
            return {
                "query": query,
                "answer": "Research API not configured",
                "sources": [],
                "error": "PERPLEXITY_API_KEY not set"
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant. Provide comprehensive, factual answers with specific data, statistics, and expert insights. Include recent information and cite reliable sources."
                },
                {
                    "role": "user",
                    "content": f"Research question: {query}\n\nPlease provide:\n1. Key findings and current data\n2. Specific statistics with dates\n3. Expert quotes or insights\n4. Recent trends or developments\n5. Reliable sources"
                }
            ],
            "temperature": 0.2,
            "max_tokens": 1500,
            "top_p": 0.9
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # Extract sources from citations
                        sources = self._extract_sources(content)
                        
                        return {
                            "query": query,
                            "answer": content,
                            "sources": sources,
                            "token_usage": data.get("usage", {}),
                            "model": self.model
                        }
                    
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited on attempt {attempt + 1}, retrying in {self.retry_delay} seconds")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    
                    else:
                        logger.error(f"Perplexity API error {response.status_code}: {response.text}")
                        return {
                            "query": query,
                            "answer": f"API Error: {response.status_code}",
                            "sources": [],
                            "error": f"HTTP {response.status_code}"
                        }
            
            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "query": query,
                        "answer": "Request timed out",
                        "sources": [],
                        "error": "Timeout"
                    }
            
            except Exception as e:
                logger.error(f"Error querying Perplexity API: {e}")
                return {
                    "query": query,
                    "answer": f"Research error: {str(e)}",
                    "sources": [],
                    "error": str(e)
                }
        
        return {
            "query": query,
            "answer": "Failed after multiple retries",
            "sources": [],
            "error": "Max retries exceeded"
        }
    
    def _extract_sources(self, content: str) -> List[str]:
        """Extract source URLs and citations from Perplexity response"""
        sources = []
        
        # Look for URLs
        url_pattern = r'https?://[^\s\)]+[^\s\.\,\)\]]'
        urls = re.findall(url_pattern, content)
        sources.extend(urls)
        
        # Look for citation patterns like [1], (Source: ...), etc.
        citation_patterns = [
            r'\[(\d+)\]',
            r'Source:\s*([^,\n]+)',
            r'According to\s+([^,\n]+)',
            r'(?:via|from)\s+([A-Z][^,\n]{10,50})'
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sources.extend(matches)
        
        # Clean and deduplicate sources
        cleaned_sources = []
        for source in sources:
            if isinstance(source, str):
                source = source.strip().rstrip('.,)')
                if len(source) > 5 and source not in cleaned_sources:
                    cleaned_sources.append(source)
        
        return cleaned_sources[:10]  # Limit to 10 sources
    
    async def conduct_research(self, outline_content: str) -> Dict[str, Any]:
        """Main research function - extract queries and get results"""
        start_time = time.time()
        
        logger.info("Starting research phase for content outline")
        
        # Extract research queries from outline
        queries = self.extract_research_queries(outline_content)
        logger.info(f"Extracted {len(queries)} research queries")
        
        # Execute research queries
        research_results = []
        statistics = []
        expert_quotes = []
        all_sources = []
        
        for i, query in enumerate(queries):
            logger.info(f"Researching query {i+1}/{len(queries)}: {query[:50]}...")
            
            result = await self.query_perplexity(query)
            research_results.append(result)
            
            # Extract statistics and quotes from answers
            if "error" not in result:
                stats = self._extract_statistics(result["answer"])
                quotes = self._extract_quotes(result["answer"])
                
                statistics.extend(stats)
                expert_quotes.extend(quotes)
                all_sources.extend(result.get("sources", []))
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        # Deduplicate sources
        unique_sources = list(dict.fromkeys(all_sources))
        
        processing_time = time.time() - start_time
        
        research_data = {
            "queries": queries,
            "results": research_results,
            "statistics": statistics[:15],  # Limit to 15 best statistics
            "expert_quotes": expert_quotes[:10],  # Limit to 10 best quotes
            "sources": unique_sources[:20],  # Limit to 20 sources
            "metadata": {
                "total_queries": len(queries),
                "successful_queries": len([r for r in research_results if "error" not in r]),
                "processing_time": processing_time,
                "timestamp": time.time(),
                "model": self.model
            }
        }
        
        logger.info(f"Research completed: {len(research_results)} queries, {len(statistics)} statistics, {len(expert_quotes)} quotes")
        
        return research_data
    
    def _extract_statistics(self, text: str) -> List[str]:
        """Extract statistics and data points from research text"""
        statistics = []
        
        # Patterns for statistics
        stat_patterns = [
            r'\b\d+(?:\.\d+)?%[^.]*',  # Percentages
            r'\$\d+(?:[\d,]*)?(?:\.\d+)?\s*(?:billion|million|thousand)?[^.]*',  # Dollar amounts
            r'\b\d+(?:[\d,]*)?(?:\.\d+)?\s*(?:million|billion|thousand|users|customers|companies)[^.]*',  # Large numbers
            r'(?:grew|increased|decreased|rose|fell)\s+(?:by\s+)?\d+(?:\.\d+)?%[^.]*',  # Growth statistics
            r'\b(?:in\s+)?20\d{2}[^.]*\d+(?:\.\d+)?%[^.]*',  # Year-based statistics
        ]
        
        for pattern in stat_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_stat = match.strip()
                if len(clean_stat) > 10 and clean_stat not in statistics:
                    statistics.append(clean_stat)
        
        return statistics[:5]  # Return top 5 statistics per query
    
    def _extract_quotes(self, text: str) -> List[str]:
        """Extract expert quotes and insights from research text"""
        quotes = []
        
        # Look for quoted text
        quote_patterns = [
            r'"([^"]{30,200})"',  # Direct quotes
            r'according to [^,]+ said[^.]*"([^"]{20,150})"',  # Attribution quotes
            r'[A-Z][^.]*(?:stated|said|noted|explained|commented)[^.]*[.:][\s]*"?([^"]{30,200})"?',  # Expert statements
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_quote = match.strip().strip('"')
                if len(clean_quote) > 20 and clean_quote not in quotes:
                    quotes.append(clean_quote)
        
        return quotes[:3]  # Return top 3 quotes per query

# Create default research agent instance
research_agent = PerplexityResearchAgent()

# ADK Agent Integration
from google.adk import Agent
from google.genai import types

# Create ADK-compatible agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="research_agent",
    description="Research coordinator that interfaces with real-time research capabilities",
    instruction="""You are a research coordinator that interfaces with real-time research capabilities.

When asked to conduct research on a topic or outline:
1. Analyze the provided outline content
2. Extract key research areas and questions
3. Use the research capabilities to gather current data, statistics, and expert insights
4. Summarize findings in a structured format
5. Provide the research data for integration into content creation

Focus on:
- Current statistics and market data
- Expert quotes and insights  
- Recent trends and developments
- Reliable sources and citations
- Factual, verifiable information

Format your response as structured research data that can be easily integrated into content creation workflows."""
)

async def query_perplexity(outline_content: str) -> Dict[str, Any]:
    """Main entry point for research functionality"""
    return await research_agent.conduct_research(outline_content)
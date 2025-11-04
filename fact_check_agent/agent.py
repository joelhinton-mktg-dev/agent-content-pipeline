#!/usr/bin/env python3
"""
Fact-Checking Agent - Content Verification and Accuracy Scoring
Verifies factual claims in content against research data and sources
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class FactCheckAgent:
    """Agent for verifying factual claims against research data"""
    
    def __init__(self):
        # Configuration from environment
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.flag_unsupported = os.getenv("FLAG_UNSUPPORTED", "true").lower() == "true"
        self.min_claim_length = int(os.getenv("MIN_CLAIM_LENGTH", "10"))
        self.max_claim_length = int(os.getenv("MAX_CLAIM_LENGTH", "200"))
        
        # Claim patterns for extraction
        self.claim_patterns = self._initialize_claim_patterns()
    
    def _initialize_claim_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for extracting factual claims"""
        return [
            # Statistics and percentages
            {
                "name": "percentage_statistics",
                "pattern": r'([^.]*?\b\d+(?:\.\d+)?%[^.]*?)',
                "type": "statistic",
                "priority": 1,
                "description": "Percentage-based statistics"
            },
            # Financial data
            {
                "name": "financial_figures",
                "pattern": r'([^.]*?\$\d+(?:[\d,]*)?(?:\.\d+)?\s*(?:billion|million|thousand|k)?[^.]*?)',
                "type": "financial",
                "priority": 1,
                "description": "Financial figures and amounts"
            },
            # Growth metrics
            {
                "name": "growth_metrics",
                "pattern": r'([^.]*?(?:grew|increased|decreased|rose|fell|improved|declined)\s+(?:by\s+)?\d+(?:\.\d+)?%[^.]*?)',
                "type": "growth",
                "priority": 1,
                "description": "Growth and change metrics"
            },
            # Market data
            {
                "name": "market_data",
                "pattern": r'([^.]*?(?:market|industry|sector)\s+(?:size|value|worth)[^.]*?\$?\d+[^.]*?)',
                "type": "market",
                "priority": 2,
                "description": "Market size and industry data"
            },
            # Temporal claims with specific years
            {
                "name": "temporal_claims",
                "pattern": r'([^.]*?(?:in\s+20\d{2}|during\s+20\d{2}|by\s+20\d{2})[^.]*?)',
                "type": "temporal",
                "priority": 2,
                "description": "Time-specific claims"
            },
            # Research findings
            {
                "name": "research_findings",
                "pattern": r'([^.]*?(?:study|research|survey|report|analysis)\s+(?:shows|found|indicates|reveals|suggests)[^.]*?)',
                "type": "research",
                "priority": 2,
                "description": "Research and study findings"
            },
            # Quantitative claims
            {
                "name": "quantitative_claims",
                "pattern": r'([^.]*?\b\d+(?:[\d,]*)?(?:\.\d+)?\s*(?:users|customers|companies|businesses|people|organizations)[^.]*?)',
                "type": "quantitative",
                "priority": 3,
                "description": "Quantitative business claims"
            },
            # Comparative claims
            {
                "name": "comparative_claims",
                "pattern": r'([^.]*?(?:\d+(?:\.\d+)?x|times)\s+(?:more|less|faster|slower|better|worse)[^.]*?)',
                "type": "comparative",
                "priority": 3,
                "description": "Comparative performance claims"
            },
            # Expert attributions
            {
                "name": "expert_attributions",
                "pattern": r'([^.]*?(?:according to|experts|analysts|researchers)\s+[^.]*?)',
                "type": "attribution",
                "priority": 3,
                "description": "Expert opinion attributions"
            }
        ]
    
    def extract_factual_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract factual claims from content that need verification"""
        claims = []
        claim_id = 1
        
        # Track claim positions to avoid duplicates
        processed_positions = set()
        
        for pattern_info in self.claim_patterns:
            pattern = pattern_info["pattern"]
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
            
            for match in matches:
                claim_text = match.group(1).strip()
                start_pos = match.start(1)
                end_pos = match.end(1)
                
                # Skip if this position was already processed
                if any(abs(start_pos - pos) < 10 for pos in processed_positions):
                    continue
                
                # Validate claim length and content
                if (self.min_claim_length <= len(claim_text) <= self.max_claim_length and
                    self._is_valid_claim(claim_text)):
                    
                    claim = {
                        "id": claim_id,
                        "claim": claim_text,
                        "type": pattern_info["type"],
                        "pattern_name": pattern_info["name"],
                        "priority": pattern_info["priority"],
                        "start_pos": start_pos,
                        "end_pos": end_pos,
                        "location": self._determine_claim_location(content, start_pos),
                        "extracted_numbers": self._extract_numbers(claim_text),
                        "extracted_dates": self._extract_dates(claim_text),
                        "keywords": self._extract_claim_keywords(claim_text)
                    }
                    
                    claims.append(claim)
                    processed_positions.add(start_pos)
                    claim_id += 1
        
        # Sort by position in content and priority
        claims.sort(key=lambda x: (x['start_pos'], x['priority']))
        
        logger.info(f"Extracted {len(claims)} factual claims for verification")
        return claims
    
    def _is_valid_claim(self, claim_text: str) -> bool:
        """Validate if extracted text is a meaningful claim"""
        # Filter out common false positives
        invalid_patterns = [
            r'^\s*\d+\.\s*$',  # Just numbered lists
            r'^\s*[•\-\*]\s*$',  # Just bullet points
            r'^\s*\([^)]*\)\s*$',  # Just parenthetical text
            r'^\s*\[[^\]]*\]\s*$',  # Just bracketed text
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, claim_text, re.IGNORECASE):
                return False
        
        # Must contain some meaningful content
        words = claim_text.split()
        if len(words) < 3:
            return False
        
        # Must contain at least one number or meaningful keyword
        has_number = bool(re.search(r'\d', claim_text))
        meaningful_keywords = ['study', 'research', 'report', 'analysis', 'found', 'shows', 'indicates']
        has_keyword = any(keyword in claim_text.lower() for keyword in meaningful_keywords)
        
        return has_number or has_keyword
    
    def _determine_claim_location(self, content: str, position: int) -> str:
        """Determine the location/section of a claim in the content"""
        # Split content into sections based on headers
        sections = re.split(r'\n#+\s+([^\n]+)', content)
        
        current_pos = 0
        current_section = "introduction"
        
        for i, section in enumerate(sections):
            if i % 2 == 1:  # Header
                current_section = section.strip().lower()
            else:  # Content
                if current_pos <= position < current_pos + len(section):
                    return current_section
                current_pos += len(section)
        
        return current_section
    
    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numerical values from claim text"""
        # Match various number formats
        number_patterns = [
            r'\d+(?:\.\d+)?%',  # Percentages
            r'\$\d+(?:[\d,]*)?(?:\.\d+)?(?:\s*(?:billion|million|thousand|k))?',  # Money
            r'\d+(?:[\d,]*)?(?:\.\d+)?(?:\s*(?:billion|million|thousand|k))?',  # Large numbers
            r'\d+(?:\.\d+)?x',  # Multipliers
            r'20\d{2}',  # Years
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        
        return list(set(numbers))  # Remove duplicates
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates and temporal references from claim text"""
        date_patterns = [
            r'20\d{2}',  # Years
            r'(?:in|during|by)\s+20\d{2}',  # Temporal phrases
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}',  # Month Year
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_claim_keywords(self, text: str) -> List[str]:
        """Extract keywords from claim for matching"""
        # Remove stop words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'
        }
        
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        return keywords[:10]  # Limit to 10 most relevant keywords
    
    def verify_claims_against_research(self, claims: List[Dict], research_data: Dict) -> List[Dict]:
        """Verify extracted claims against research data"""
        verified_claims = []
        
        # Prepare research content for matching
        research_content = self._prepare_research_content(research_data)
        
        for claim in claims:
            verification_result = self._verify_single_claim(claim, research_content)
            claim.update(verification_result)
            verified_claims.append(claim)
        
        logger.info(f"Verified {len(verified_claims)} claims against research data")
        return verified_claims
    
    def _prepare_research_content(self, research_data: Dict) -> List[Dict]:
        """Prepare research data for claim verification"""
        content = []
        
        # Add statistics
        for stat in research_data.get('statistics', []):
            content.append({
                'text': stat,
                'type': 'statistic',
                'source': 'research_statistics',
                'numbers': self._extract_numbers(stat),
                'keywords': self._extract_claim_keywords(stat)
            })
        
        # Add expert quotes
        for quote in research_data.get('expert_quotes', []):
            content.append({
                'text': quote,
                'type': 'expert_opinion',
                'source': 'expert_quotes',
                'numbers': self._extract_numbers(quote),
                'keywords': self._extract_claim_keywords(quote)
            })
        
        # Add research results
        for result in research_data.get('results', []):
            if 'answer' in result:
                content.append({
                    'text': result['answer'],
                    'type': 'research_result',
                    'source': result.get('query', 'research_query'),
                    'numbers': self._extract_numbers(result['answer']),
                    'keywords': self._extract_claim_keywords(result['answer'])
                })
        
        return content
    
    def _verify_single_claim(self, claim: Dict, research_content: List[Dict]) -> Dict:
        """Verify a single claim against research content"""
        best_match = None
        best_confidence = 0.0
        
        claim_text = claim['claim'].lower()
        claim_numbers = claim.get('extracted_numbers', [])
        claim_keywords = claim.get('keywords', [])
        
        for research_item in research_content:
            confidence = self._calculate_match_confidence(claim, research_item)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = research_item
        
        # Determine verification status
        if best_confidence >= self.confidence_threshold:
            status = "verified"
        elif best_confidence >= 0.4:
            status = "needs_review"
        else:
            status = "unsupported"
        
        return {
            "status": status,
            "confidence": round(best_confidence, 3),
            "supporting_source": best_match['source'] if best_match else None,
            "supporting_text": best_match['text'][:200] + "..." if best_match and len(best_match['text']) > 200 else best_match['text'] if best_match else None,
            "verification_details": {
                "best_match_confidence": best_confidence,
                "match_type": best_match['type'] if best_match else None,
                "matching_numbers": self._find_matching_numbers(claim_numbers, best_match['numbers'] if best_match else []),
                "matching_keywords": self._find_matching_keywords(claim_keywords, best_match['keywords'] if best_match else [])
            }
        }
    
    def _calculate_match_confidence(self, claim: Dict, research_item: Dict) -> float:
        """Calculate confidence score for claim-research match"""
        score = 0.0
        
        claim_text = claim['claim'].lower()
        research_text = research_item['text'].lower()
        
        # Text similarity (30% weight)
        text_similarity = SequenceMatcher(None, claim_text, research_text).ratio()
        score += text_similarity * 0.3
        
        # Number matching (35% weight)
        claim_numbers = claim.get('extracted_numbers', [])
        research_numbers = research_item.get('numbers', [])
        number_match_score = self._calculate_number_match_score(claim_numbers, research_numbers)
        score += number_match_score * 0.35
        
        # Keyword overlap (25% weight)
        claim_keywords = set(claim.get('keywords', []))
        research_keywords = set(research_item.get('keywords', []))
        if claim_keywords and research_keywords:
            keyword_overlap = len(claim_keywords & research_keywords) / len(claim_keywords)
            score += keyword_overlap * 0.25
        
        # Type matching bonus (10% weight)
        if claim['type'] == research_item['type'] or (claim['type'] == 'statistic' and research_item['type'] == 'statistic'):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_number_match_score(self, claim_numbers: List[str], research_numbers: List[str]) -> float:
        """Calculate score for numerical data matching"""
        if not claim_numbers or not research_numbers:
            return 0.0
        
        matches = 0
        total_claim_numbers = len(claim_numbers)
        
        for claim_num in claim_numbers:
            # Clean numbers for comparison
            clean_claim_num = re.sub(r'[^\d.]', '', claim_num)
            
            for research_num in research_numbers:
                clean_research_num = re.sub(r'[^\d.]', '', research_num)
                
                # Exact match
                if clean_claim_num == clean_research_num:
                    matches += 1
                    break
                # Close match (within 10% for percentages)
                elif self._is_close_numerical_match(clean_claim_num, clean_research_num):
                    matches += 0.7
                    break
        
        return matches / total_claim_numbers
    
    def _is_close_numerical_match(self, num1: str, num2: str) -> bool:
        """Check if two numbers are close enough to be considered matching"""
        try:
            val1 = float(num1)
            val2 = float(num2)
            
            # For small numbers, allow 1 unit difference
            if max(val1, val2) <= 10:
                return abs(val1 - val2) <= 1
            
            # For larger numbers, allow 10% difference
            larger = max(val1, val2)
            return abs(val1 - val2) / larger <= 0.1
        except ValueError:
            return False
    
    def _find_matching_numbers(self, claim_numbers: List[str], research_numbers: List[str]) -> List[str]:
        """Find numbers that match between claim and research"""
        matches = []
        for claim_num in claim_numbers:
            clean_claim = re.sub(r'[^\d.]', '', claim_num)
            for research_num in research_numbers:
                clean_research = re.sub(r'[^\d.]', '', research_num)
                if clean_claim == clean_research or self._is_close_numerical_match(clean_claim, clean_research):
                    matches.append(claim_num)
                    break
        return matches
    
    def _find_matching_keywords(self, claim_keywords: List[str], research_keywords: List[str]) -> List[str]:
        """Find keywords that match between claim and research"""
        return list(set(claim_keywords) & set(research_keywords))
    
    def generate_recommendations(self, verified_claims: List[Dict]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        unsupported_claims = [c for c in verified_claims if c['status'] == 'unsupported']
        needs_review_claims = [c for c in verified_claims if c['status'] == 'needs_review']
        
        if unsupported_claims:
            recommendations.append(f"Remove or find sources for {len(unsupported_claims)} unsupported claims")
            
            # Identify most problematic claims
            high_priority_unsupported = [c for c in unsupported_claims if c['priority'] <= 2]
            if high_priority_unsupported:
                recommendations.append(f"Priority: Verify {len(high_priority_unsupported)} high-priority statistical claims")
        
        if needs_review_claims:
            recommendations.append(f"Review and strengthen sources for {len(needs_review_claims)} partially supported claims")
        
        # Type-specific recommendations
        unsupported_by_type = {}
        for claim in unsupported_claims:
            claim_type = claim['type']
            if claim_type not in unsupported_by_type:
                unsupported_by_type[claim_type] = 0
            unsupported_by_type[claim_type] += 1
        
        for claim_type, count in unsupported_by_type.items():
            if count >= 2:
                recommendations.append(f"Focus on verifying {claim_type} claims - {count} found unsupported")
        
        if not recommendations:
            recommendations.append("All claims are well-supported by research data")
        
        return recommendations
    
    def calculate_accuracy_score(self, verified_claims: List[Dict]) -> float:
        """Calculate overall content accuracy score"""
        if not verified_claims:
            return 0.0
        
        total_weight = 0
        weighted_score = 0
        
        for claim in verified_claims:
            # Weight by priority (higher priority = more weight)
            weight = 4 - claim['priority']  # Priority 1 = weight 3, Priority 3 = weight 1
            
            # Score by verification status
            if claim['status'] == 'verified':
                score = claim['confidence']
            elif claim['status'] == 'needs_review':
                score = claim['confidence'] * 0.6  # Partial credit
            else:  # unsupported
                score = 0
            
            weighted_score += score * weight
            total_weight += weight
        
        return round(weighted_score / total_weight if total_weight > 0 else 0.0, 3)
    
    def verify_facts(self, content: str, research_data: Dict) -> Dict[str, Any]:
        """Main function to verify facts in content against research data"""
        start_time = time.time()
        
        logger.info("Starting fact-checking process")
        
        try:
            # Validate research data
            if not research_data or not any([
                research_data.get('statistics'),
                research_data.get('expert_quotes'),
                research_data.get('results')
            ]):
                logger.warning("No research data available for fact-checking")
                return {
                    "verified_claims": [],
                    "statistics": {
                        "total_claims": 0,
                        "verified": 0,
                        "unsupported": 0,
                        "needs_review": 0
                    },
                    "recommendations": ["No research data available for fact verification"],
                    "accuracy_score": 0.0,
                    "metadata": {
                        "processing_time": time.time() - start_time,
                        "error": "No research data available"
                    }
                }
            
            # Step 1: Extract factual claims
            claims = self.extract_factual_claims(content)
            
            if not claims:
                return {
                    "verified_claims": [],
                    "statistics": {
                        "total_claims": 0,
                        "verified": 0,
                        "unsupported": 0,
                        "needs_review": 0
                    },
                    "recommendations": ["No factual claims detected for verification"],
                    "accuracy_score": 1.0,  # No claims = technically accurate
                    "metadata": {
                        "processing_time": time.time() - start_time,
                        "claims_extracted": 0
                    }
                }
            
            # Step 2: Verify claims against research
            verified_claims = self.verify_claims_against_research(claims, research_data)
            
            # Step 3: Calculate statistics
            stats = {
                "total_claims": len(verified_claims),
                "verified": len([c for c in verified_claims if c['status'] == 'verified']),
                "unsupported": len([c for c in verified_claims if c['status'] == 'unsupported']),
                "needs_review": len([c for c in verified_claims if c['status'] == 'needs_review'])
            }
            
            # Step 4: Generate recommendations
            recommendations = self.generate_recommendations(verified_claims)
            
            # Step 5: Calculate accuracy score
            accuracy_score = self.calculate_accuracy_score(verified_claims)
            
            processing_time = time.time() - start_time
            
            result = {
                "verified_claims": verified_claims,
                "statistics": stats,
                "recommendations": recommendations,
                "accuracy_score": accuracy_score,
                "metadata": {
                    "processing_time": processing_time,
                    "claims_extracted": len(claims),
                    "confidence_threshold": self.confidence_threshold,
                    "verification_complete": True
                }
            }
            
            logger.info(f"Fact-checking completed: {stats['verified']}/{stats['total_claims']} claims verified, accuracy score: {accuracy_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fact-checking process: {e}")
            return {
                "verified_claims": [],
                "statistics": {
                    "total_claims": 0,
                    "verified": 0,
                    "unsupported": 0,
                    "needs_review": 0
                },
                "recommendations": [f"Fact-checking failed: {str(e)}"],
                "accuracy_score": 0.0,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "error": str(e)
                }
            }

# Create default fact-checking agent instance
fact_check_agent = FactCheckAgent()

# ADK Agent Integration
from google.adk import Agent
from google.genai import types

# Create ADK-compatible agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="fact_check_agent",
    description="Fact-checking specialist that verifies content accuracy against research data",
    instruction="""You are a fact-checking specialist that verifies content accuracy against research data.

When provided with content and research data:
1. Extract factual claims, statistics, and verifiable statements
2. Cross-reference claims with available research sources
3. Assign confidence scores based on supporting evidence
4. Flag unsupported or questionable claims
5. Generate recommendations for improving content accuracy

Focus on:
- Statistical claims and numerical data
- Expert attributions and quotes
- Temporal claims and dates
- Market data and financial figures
- Research findings and study results

Provide detailed verification results with confidence scoring and specific recommendations for enhancing content credibility."""
)

async def verify_facts(content: str, research_data: Dict) -> Dict[str, Any]:
    """Main entry point for fact-checking functionality"""
    return fact_check_agent.verify_facts(content, research_data)
#!/usr/bin/env python3
"""
Image Generation Agent - DALL-E 3 Integration
Automatically generates relevant images for content using OpenAI's DALL-E 3 API
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ImageGenerationAgent:
    """Agent for generating contextual images using DALL-E 3"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/images/generations"
        self.model = "dall-e-3"
        
        # Configuration from environment
        self.image_quality = os.getenv("IMAGE_QUALITY", "standard")  # standard|hd
        self.image_size = os.getenv("IMAGE_SIZE", "1024x1024")  # 1024x1024|1024x1792|1792x1024
        self.max_images = int(os.getenv("MAX_IMAGES", "5"))
        self.style = os.getenv("IMAGE_STYLE", "natural")  # natural|vivid
        
        # Output configuration
        self.outputs_dir = Path("/home/joel/ai-content-pipeline/outputs")
        self.images_dir = self.outputs_dir / "images"
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Image generation will be disabled.")
    
    def analyze_content_for_images(self, content: str, outline: str) -> List[Dict[str, Any]]:
        """Analyze content and outline to identify optimal image opportunities"""
        image_opportunities = []
        
        # Combine content and outline for analysis
        full_text = f"{outline}\n\n{content}"
        
        # Extract sections from content
        sections = self._extract_sections(content)
        
        # Define image opportunity patterns
        opportunity_patterns = [
            # Header/hero image
            {
                "type": "hero",
                "priority": 1,
                "placement": "header",
                "description": "Main topic visualization",
                "section": "introduction"
            },
            # Process/workflow images
            {
                "type": "process",
                "priority": 2,
                "placement": "mid-content",
                "keywords": ["process", "workflow", "steps", "methodology", "framework"],
                "description": "Process or workflow illustration"
            },
            # Data/statistics images
            {
                "type": "data",
                "priority": 3,
                "placement": "mid-content",
                "keywords": ["statistics", "data", "chart", "graph", "metrics", "performance"],
                "description": "Data visualization or infographic"
            },
            # Technology/tools images
            {
                "type": "technology",
                "priority": 2,
                "placement": "mid-content",
                "keywords": ["technology", "tools", "software", "platform", "AI", "automation"],
                "description": "Technology or tools illustration"
            },
            # Business/strategy images
            {
                "type": "business",
                "priority": 3,
                "placement": "mid-content",
                "keywords": ["business", "strategy", "growth", "success", "team", "collaboration"],
                "description": "Business or strategy concept"
            },
            # Conclusion/summary image
            {
                "type": "conclusion",
                "priority": 4,
                "placement": "conclusion",
                "description": "Summary or future outlook",
                "section": "conclusion"
            }
        ]
        
        opportunity_id = 1
        
        # Always include hero image
        hero_opportunity = {
            "id": opportunity_id,
            "type": "hero",
            "priority": 1,
            "placement": "header",
            "section": "introduction",
            "description": "Main topic hero image",
            "content_context": self._extract_main_topic(outline, content)
        }
        image_opportunities.append(hero_opportunity)
        opportunity_id += 1
        
        # Analyze sections for specific image opportunities
        for section in sections:
            if len(image_opportunities) >= self.max_images:
                break
                
            section_text = section['content'].lower()
            section_name = section['title']
            
            for pattern in opportunity_patterns[1:]:  # Skip hero (already added)
                if len(image_opportunities) >= self.max_images:
                    break
                    
                # Check if pattern keywords match section content
                if pattern.get('keywords'):
                    keyword_matches = sum(1 for keyword in pattern['keywords'] if keyword in section_text)
                    if keyword_matches > 0:
                        opportunity = {
                            "id": opportunity_id,
                            "type": pattern["type"],
                            "priority": pattern["priority"],
                            "placement": f"section_{section['index']}",
                            "section": section_name,
                            "description": pattern["description"],
                            "content_context": section['content'][:500],  # Limit context
                            "keyword_matches": keyword_matches
                        }
                        image_opportunities.append(opportunity)
                        opportunity_id += 1
                        break
        
        # Add conclusion image if we have fewer than max_images
        if len(image_opportunities) < self.max_images:
            conclusion_sections = [s for s in sections if 'conclusion' in s['title'].lower() or 'summary' in s['title'].lower()]
            if conclusion_sections:
                conclusion_opportunity = {
                    "id": opportunity_id,
                    "type": "conclusion",
                    "priority": 4,
                    "placement": "conclusion", 
                    "section": conclusion_sections[0]['title'],
                    "description": "Conclusion or summary visualization",
                    "content_context": conclusion_sections[0]['content'][:300]
                }
                image_opportunities.append(conclusion_opportunity)
        
        # Sort by priority and limit to max_images
        image_opportunities.sort(key=lambda x: x['priority'])
        return image_opportunities[:self.max_images]
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from content based on headers"""
        sections = []
        
        # Split by headers (markdown style)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = None
        section_index = 0
        
        for line in lines:
            header_match = re.match(header_pattern, line.strip())
            if header_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                header_level = len(header_match.group(1))
                header_title = header_match.group(2).strip()
                
                current_section = {
                    "index": section_index,
                    "title": header_title,
                    "level": header_level,
                    "content": ""
                }
                section_index += 1
            else:
                # Add content to current section
                if current_section:
                    current_section["content"] += line + "\n"
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        # If no headers found, treat entire content as one section
        if not sections:
            sections.append({
                "index": 0,
                "title": "Content",
                "level": 1,
                "content": content
            })
        
        return sections
    
    def _extract_main_topic(self, outline: str, content: str) -> str:
        """Extract the main topic for hero image generation"""
        # Look for the main title in outline
        title_patterns = [
            r'^#\s+(.+)$',  # Main header
            r'[Tt]itle:\s*(.+)$',  # Title: format
            r'[Tt]opic:\s*(.+)$',  # Topic: format
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, outline, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first significant line
        lines = outline.split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 10 and not clean_line.startswith('-'):
                return clean_line
        
        return "Content topic"
    
    def generate_image_prompts(self, opportunities: List[Dict], topic_context: str) -> List[Dict[str, Any]]:
        """Generate DALL-E prompts for each image opportunity"""
        prompts = []
        
        for opp in opportunities:
            prompt_data = {
                "id": opp["id"],
                "type": opp["type"],
                "placement": opp["placement"],
                "section": opp["section"],
                "dalle_prompt": "",
                "alt_text": "",
                "placement_suggestion": ""
            }
            
            # Generate DALL-E prompt based on type and context
            if opp["type"] == "hero":
                prompt_data["dalle_prompt"] = self._generate_hero_prompt(topic_context, opp.get("content_context", ""))
                prompt_data["alt_text"] = f"Hero image representing {topic_context}"
                prompt_data["placement_suggestion"] = "Place at the top of the article as a header image"
                
            elif opp["type"] == "process":
                prompt_data["dalle_prompt"] = self._generate_process_prompt(opp.get("content_context", ""), topic_context)
                prompt_data["alt_text"] = f"Process diagram illustrating {opp.get('section', 'workflow')}"
                prompt_data["placement_suggestion"] = f"Insert in the {opp.get('section', 'process')} section"
                
            elif opp["type"] == "data":
                prompt_data["dalle_prompt"] = self._generate_data_prompt(opp.get("content_context", ""), topic_context)
                prompt_data["alt_text"] = f"Data visualization for {opp.get('section', 'statistics')}"
                prompt_data["placement_suggestion"] = f"Place alongside statistics in {opp.get('section', 'data')} section"
                
            elif opp["type"] == "technology":
                prompt_data["dalle_prompt"] = self._generate_technology_prompt(opp.get("content_context", ""), topic_context)
                prompt_data["alt_text"] = f"Technology illustration for {opp.get('section', 'tools')}"
                prompt_data["placement_suggestion"] = f"Insert in {opp.get('section', 'technology')} section"
                
            elif opp["type"] == "business":
                prompt_data["dalle_prompt"] = self._generate_business_prompt(opp.get("content_context", ""), topic_context)
                prompt_data["alt_text"] = f"Business concept illustration for {opp.get('section', 'strategy')}"
                prompt_data["placement_suggestion"] = f"Place in {opp.get('section', 'business')} section"
                
            elif opp["type"] == "conclusion":
                prompt_data["dalle_prompt"] = self._generate_conclusion_prompt(opp.get("content_context", ""), topic_context)
                prompt_data["alt_text"] = f"Summary visualization for {topic_context}"
                prompt_data["placement_suggestion"] = "Place at the end of the article in conclusion section"
            
            prompts.append(prompt_data)
        
        return prompts
    
    def _generate_hero_prompt(self, topic: str, context: str) -> str:
        """Generate hero image prompt"""
        clean_topic = re.sub(r'[^\w\s-]', '', topic).strip()
        return f"Professional, modern illustration representing {clean_topic}. Clean, minimalist design with vibrant colors. Corporate style, high-quality digital art. No text or words in the image."
    
    def _generate_process_prompt(self, context: str, topic: str) -> str:
        """Generate process/workflow image prompt"""
        return f"Clean infographic showing a step-by-step process or workflow related to {topic}. Modern flat design with arrows and connected elements. Professional color scheme. No text in the image."
    
    def _generate_data_prompt(self, context: str, topic: str) -> str:
        """Generate data visualization prompt"""
        return f"Modern data visualization dashboard or analytics screen showing charts and graphs related to {topic}. Clean interface design with colorful charts. Professional business style. No specific numbers or text."
    
    def _generate_technology_prompt(self, context: str, topic: str) -> str:
        """Generate technology illustration prompt"""
        return f"Modern technology illustration showing digital devices, networks, or AI concepts related to {topic}. Futuristic design with clean lines and tech aesthetic. Blue and white color scheme."
    
    def _generate_business_prompt(self, context: str, topic: str) -> str:
        """Generate business concept prompt"""
        return f"Professional business illustration showing teamwork, growth, or strategy concepts related to {topic}. Clean corporate style with people working together. Modern office aesthetic."
    
    def _generate_conclusion_prompt(self, context: str, topic: str) -> str:
        """Generate conclusion/summary prompt"""
        return f"Optimistic illustration showing success, achievement, or future growth related to {topic}. Upward trending elements, bright colors, positive business imagery. Clean professional style."
    
    async def generate_single_image(self, prompt_data: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
        """Generate a single image using DALL-E 3"""
        if not self.api_key:
            logger.warning("OpenAI API key not available, skipping image generation")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "prompt": prompt_data["dalle_prompt"],
                "size": self.image_size,
                "quality": self.image_quality,
                "style": self.style,
                "n": 1
            }
            
            logger.info(f"Generating image for: {prompt_data['section']}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"DALL-E API error {response.status_code}: {response.text}")
                    return None
                
                result = response.json()
                image_url = result["data"][0]["url"]
                revised_prompt = result["data"][0].get("revised_prompt", prompt_data["dalle_prompt"])
                
                # Download the image
                image_filename = f"{job_id}_{prompt_data['type']}_{prompt_data['id']}.png"
                image_path = await self._download_image(image_url, image_filename, job_id)
                
                if image_path:
                    return {
                        "filename": image_filename,
                        "path": str(image_path),
                        "relative_path": f"outputs/images/{job_id}/{image_filename}",
                        "prompt": revised_prompt,
                        "original_prompt": prompt_data["dalle_prompt"],
                        "alt_text": prompt_data["alt_text"],
                        "placement_suggestion": prompt_data["placement_suggestion"],
                        "section": prompt_data["section"],
                        "type": prompt_data["type"],
                        "size": self.image_size,
                        "quality": self.image_quality,
                        "generated_at": datetime.now().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"Error generating image for {prompt_data['section']}: {e}")
            return None
    
    async def _download_image(self, image_url: str, filename: str, job_id: str) -> Optional[Path]:
        """Download image from URL to local storage"""
        try:
            # Create job-specific directory
            job_dir = self.images_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            
            image_path = job_dir / filename
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded image: {image_path}")
                return image_path
                
        except Exception as e:
            logger.error(f"Error downloading image {filename}: {e}")
            return None
    
    def create_image_manifest(self, images: List[Dict], job_id: str, topic: str) -> Dict[str, Any]:
        """Create manifest file with image metadata"""
        manifest = {
            "job_id": job_id,
            "topic": topic,
            "generated_at": datetime.now().isoformat(),
            "image_count": len(images),
            "images": images,
            "configuration": {
                "model": self.model,
                "size": self.image_size,
                "quality": self.image_quality,
                "style": self.style,
                "max_images": self.max_images
            },
            "usage_instructions": {
                "wordpress": "Upload images to WordPress media library and insert using placement suggestions",
                "markdown": "Reference images using relative paths: ![alt_text](relative_path)",
                "html": "Use <img> tags with alt attributes for accessibility"
            }
        }
        
        # Save manifest to job directory
        try:
            job_dir = self.images_dir / job_id
            manifest_path = job_dir / "manifest.json"
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Created image manifest: {manifest_path}")
            
        except Exception as e:
            logger.error(f"Error creating manifest: {e}")
        
        return manifest
    
    async def generate_images(self, content: str, outline: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Main function to generate images for content"""
        start_time = time.time()
        
        if not job_id:
            job_id = f"img_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Starting image generation for job {job_id}")
        
        try:
            # Step 1: Analyze content for image opportunities
            opportunities = self.analyze_content_for_images(content, outline)
            logger.info(f"Identified {len(opportunities)} image opportunities")
            
            if not opportunities:
                return {
                    "images": [],
                    "manifest": {},
                    "count": 0,
                    "metadata": {
                        "processing_time": time.time() - start_time,
                        "error": "No image opportunities identified"
                    }
                }
            
            # Step 2: Generate prompts
            topic_context = self._extract_main_topic(outline, content)
            prompts = self.generate_image_prompts(opportunities, topic_context)
            
            # Step 3: Generate images
            generated_images = []
            
            for prompt_data in prompts:
                if not self.api_key:
                    # Create placeholder entry for missing API key
                    placeholder = {
                        "filename": f"placeholder_{prompt_data['type']}.png",
                        "path": "API_KEY_REQUIRED",
                        "relative_path": f"outputs/images/{job_id}/placeholder_{prompt_data['type']}.png",
                        "prompt": prompt_data.get("dalle_prompt", ""),
                        "alt_text": prompt_data.get("alt_text", ""),
                        "placement_suggestion": prompt_data.get("placement_suggestion", ""),
                        "section": prompt_data.get("section", ""),
                        "type": prompt_data.get("type", ""),
                        "status": "api_key_required"
                    }
                    generated_images.append(placeholder)
                    continue
                
                image_result = await self.generate_single_image(prompt_data, job_id)
                if image_result:
                    generated_images.append(image_result)
                
                # Small delay between API calls
                await asyncio.sleep(1)
            
            # Step 4: Create manifest
            manifest = self.create_image_manifest(generated_images, job_id, topic_context)
            
            processing_time = time.time() - start_time
            
            result = {
                "images": generated_images,
                "manifest": manifest,
                "count": len(generated_images),
                "metadata": {
                    "processing_time": processing_time,
                    "job_id": job_id,
                    "opportunities_identified": len(opportunities),
                    "prompts_generated": len(prompts),
                    "images_created": len([img for img in generated_images if img.get("status") != "api_key_required"]),
                    "api_available": bool(self.api_key)
                }
            }
            
            logger.info(f"Image generation completed: {len(generated_images)} images in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in image generation process: {e}")
            return {
                "images": [],
                "manifest": {},
                "count": 0,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "error": str(e)
                }
            }

# Create default image generation agent instance
image_agent = ImageGenerationAgent()

# ADK Agent Integration
from google.adk import Agent
from google.genai import types

# Create ADK-compatible agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="image_agent",
    description="Image generation specialist that creates relevant, high-quality images for content",
    instruction="""You are an image generation specialist that creates relevant, high-quality images for content.

When provided with content and outline:
1. Analyze the content structure and identify optimal image placement opportunities
2. Generate contextually appropriate image prompts for DALL-E 3
3. Create images that enhance content understanding and engagement
4. Provide detailed alt text for accessibility
5. Suggest optimal placement within the content structure

Focus on:
- Visual content enhancement
- Professional, clean design aesthetics
- Accessibility compliance
- Strategic placement for maximum impact
- Contextual relevance to content themes

Generate images that are professional, engaging, and directly support the content's message and goals."""
)

async def generate_images(content: str, outline: str, job_id: Optional[str] = None) -> Dict[str, Any]:
    """Main entry point for image generation functionality"""
    return await image_agent.generate_images(content, outline, job_id)
#!/usr/bin/env python3
"""
WebADK Pipeline Orchestrator - Interactive Chat Interface
Manages the entire 8-stage AI content pipeline through conversational interaction
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
import sys
import os
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
project_root = Path(__file__).parent.parent
for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator', 'research_agent', 'citation_agent', 'image_agent', 'fact_check_agent']:
    env_file = project_root / agent_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)

# Add parent directory to path for pipeline imports
sys.path.append(str(project_root))

from google.adk import Agent
from google.genai import types
from pipeline_single_session import SingleSessionPipelineOrchestrator

class DemoPipelineOrchestrator:
    """Interactive demo orchestrator for the AI content pipeline"""
    
    def __init__(self):
        self.session_id = None
        self.pipeline_orchestrator = None
        self.current_stage = 0
        self.total_stages = 8
        self.stage_names = [
            "Outline Generation",
            "Research Collection", 
            "Content Creation",
            "Citation Processing",
            "Image Generation",
            "Fact Checking",
            "SEO Optimization",
            "Publishing Preparation"
        ]
        self.results = {}
        self.start_time = None
        self.downloads_dir = Path(__file__).parent / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize the pipeline orchestrator"""
        try:
            self.pipeline_orchestrator = SingleSessionPipelineOrchestrator()
            success = await self.pipeline_orchestrator.initialize_session()
            if success:
                self.session_id = self.pipeline_orchestrator.session_id
                return True
            return False
        except Exception as e:
            print(f"Initialization error: {e}")
            return False
    
    def get_progress_percentage(self):
        """Calculate current progress percentage"""
        return int((self.current_stage / self.total_stages) * 100)
    
    def get_current_stage_name(self):
        """Get the name of the current stage"""
        if self.current_stage < len(self.stage_names):
            return self.stage_names[self.current_stage]
        return "Complete"
    
    async def process_content_request(self, topic: str, audience: str = "General audience", length: int = 1500) -> Dict[str, Any]:
        """Process a complete content generation request"""
        self.start_time = time.time()
        self.current_stage = 0
        self.results = {
            "topic": topic,
            "audience": audience,
            "target_length": length,
            "session_id": self.session_id,
            "stages": {},
            "downloads": [],
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Stage 1: Outline Generation
            await self._update_stage(1, "Generating content outline...")
            outline_prompt = f"Create a comprehensive outline for an article about '{topic}' targeting {audience}. Target length: {length} words."
            outline_result = await self.pipeline_orchestrator.run_agent_in_session('outline_generator', outline_prompt)
            logger.info(f"Outline result type: {type(outline_result)}, length: {len(str(outline_result))}")
            self.results['stages']['outline'] = outline_result
            
            # Stage 2: Research Collection
            await self._update_stage(2, "Conducting real-time research...")
            research_result = await self.pipeline_orchestrator.run_agent_in_session('research_agent', 
                f"Conduct comprehensive research for the article outline about '{topic}'. Focus on current statistics, expert insights, and reliable sources.")
            logger.info(f"Research result type: {type(research_result)}, length: {len(str(research_result))}")
            self.results['stages']['research'] = research_result
            
            # Stage 3: Content Creation
            await self._update_stage(3, "Writing comprehensive article...")
            content_prompt = f"Write a detailed article based on the outline and research data. Target audience: {audience}. Target length: {length} words. Integrate the research findings naturally."
            content_result = await self.pipeline_orchestrator.run_agent_in_session('research_content_creator', content_prompt)
            logger.info(f"Content result type: {type(content_result)}, length: {len(str(content_result))}")
            self.results['stages']['content'] = content_result
            
            # Stage 4: Citation Processing
            await self._update_stage(4, "Adding professional citations...")
            citation_prompt = "Add proper academic citations to the article content using the research data. Use APA style with inline citations and create a comprehensive bibliography."
            citation_result = await self.pipeline_orchestrator.run_agent_in_session('citation_agent', citation_prompt)
            logger.info(f"Citation result type: {type(citation_result)}, length: {len(str(citation_result))}")
            self.results['stages']['citations'] = citation_result
            
            # Stage 5: Image Generation
            await self._update_stage(5, "Generating contextual images...")
            image_prompt = f"Generate contextual images for the article about '{topic}'. Create 3-5 professional images including a hero image and section illustrations."
            image_result = await self.pipeline_orchestrator.run_agent_in_session('image_agent', image_prompt)
            logger.info(f"Image result type: {type(image_result)}, length: {len(str(image_result))}")
            self.results['stages']['images'] = image_result
            
            # Stage 6: Fact Checking
            await self._update_stage(6, "Verifying facts and claims...")
            fact_check_prompt = "Perform comprehensive fact-checking on the article content. Verify statistics, claims, and provide confidence scores."
            fact_check_result = await self.pipeline_orchestrator.run_agent_in_session('fact_check_agent', fact_check_prompt)
            logger.info(f"Fact-check result type: {type(fact_check_result)}, length: {len(str(fact_check_result))}")
            self.results['stages']['fact_check'] = fact_check_result
            
            # Stage 7: SEO Optimization
            await self._update_stage(7, "Optimizing for search engines...")
            seo_prompt = f"Analyze the article for SEO optimization. Generate meta descriptions, keywords, and optimization recommendations for '{topic}'."
            seo_result = await self.pipeline_orchestrator.run_agent_in_session('seo_optimizer', seo_prompt)
            self.results['stages']['seo'] = seo_result
            
            # Stage 8: Publishing Preparation
            await self._update_stage(8, "Preparing final publication package...")
            publish_prompt = "Create a complete publication-ready package with WordPress formatting, meta tags, and social media snippets."
            publish_result = await self.pipeline_orchestrator.run_agent_in_session('publishing_coordinator', publish_prompt)
            self.results['stages']['publish'] = publish_result
            
            # Finalize results
            await self._finalize_results()
            
            return self.results
            
        except Exception as e:
            error_msg = f"Pipeline error at stage {self.current_stage}: {str(e)}"
            self.results['errors'].append(error_msg)
            return self.results
    
    async def _update_stage(self, stage_num: int, status_message: str):
        """Update the current stage and status"""
        self.current_stage = stage_num
        print(f"[{self.get_progress_percentage()}%] Stage {stage_num}/8: {status_message}")
    
    async def _finalize_results(self):
        """Finalize the results and create download files"""
        processing_time = time.time() - self.start_time
        self.results['processing_time'] = processing_time
        self.results['completion_time'] = datetime.now().isoformat()
        self.results['progress'] = 100
        
        # Create download files
        session_id = self.session_id
        downloads_base = self.downloads_dir / session_id
        downloads_base.mkdir(exist_ok=True)
        
        # Save individual stage outputs with improved handling
        for stage_name, content in self.results['stages'].items():
            logger.info(f"Saving {stage_name}: type={type(content)}, content_preview={str(content)[:100]}...")
            
            file_path = downloads_base / f"{stage_name}.txt"
            
            # Always create the file, even if content is empty or None
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if content is None:
                        f.write(f"# {stage_name.title()} Stage\n\nNo content generated for this stage.\n")
                    elif isinstance(content, dict):
                        f.write(f"# {stage_name.title()} Stage - Structured Data\n\n")
                        f.write(json.dumps(content, indent=2, ensure_ascii=False))
                    elif isinstance(content, str) and content.strip():
                        f.write(f"# {stage_name.title()} Stage\n\n")
                        f.write(content.strip())
                    else:
                        # Handle other data types or empty content
                        f.write(f"# {stage_name.title()} Stage\n\n")
                        if hasattr(content, '__dict__'):
                            # Object with attributes
                            f.write(json.dumps(vars(content), indent=2, default=str, ensure_ascii=False))
                        else:
                            # Convert anything else to string
                            content_str = str(content).strip()
                            if content_str and content_str != 'None':
                                f.write(content_str)
                            else:
                                f.write("No content available for this stage.")
                
                # Get actual file size after writing
                actual_size = file_path.stat().st_size if file_path.exists() else 0
                logger.info(f"Saved {stage_name}.txt: {actual_size} bytes")
                
                self.results['downloads'].append({
                    'name': f"{stage_name}.txt",
                    'path': str(file_path),
                    'url': f"/download/{session_id}/{stage_name}.txt",
                    'size': actual_size
                })
            except Exception as e:
                logger.error(f"Error saving {stage_name}.txt: {e}")
                # Create error file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {stage_name.title()} Stage - Error\n\nError saving content: {e}\n")
                
                self.results['downloads'].append({
                    'name': f"{stage_name}.txt",
                    'path': str(file_path),
                    'url': f"/download/{session_id}/{stage_name}.txt",
                    'size': file_path.stat().st_size if file_path.exists() else 0
                })
        
        # Create complete package
        complete_file = downloads_base / "complete_package.json"
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.results['downloads'].append({
            'name': 'complete_package.json',
            'path': str(complete_file),
            'url': f"/download/{session_id}/complete_package.json",
            'size': complete_file.stat().st_size
        })
        
        # Generate summary
        word_count = len(str(self.results['stages'].get('content', '')).split())
        citation_count = str(self.results['stages'].get('citations', '')).count('[')
        
        self.results['summary'] = {
            'word_count': word_count,
            'citation_count': citation_count,
            'processing_time_minutes': round(processing_time / 60, 1),
            'stages_completed': self.current_stage,
            'success_rate': (self.current_stage / self.total_stages) * 100,
            'downloads_available': len(self.results['downloads'])
        }

# Create the ADK Agent for WebADK integration
demo_agent = Agent(
    model="gemini-2.5-flash",
    name="pipeline_demo_orchestrator", 
    description="Interactive demo interface for the AI content pipeline",
    instruction="""You are a friendly demo orchestrator for an advanced AI content pipeline.

When users ask you to generate content, respond conversationally and then trigger the pipeline.

Capabilities:
- Generate comprehensive articles (1500-5000+ words)
- Real-time research via Perplexity API
- Professional citations with working URLs
- AI-generated contextual images
- Fact verification with confidence scores
- SEO optimization and WordPress-ready formatting

Sample interactions:
User: "Generate an article about AI in healthcare"
You: "I'll create a comprehensive article about AI in healthcare! This will include real-time research, professional citations, and contextual images. Let me start the 8-stage pipeline..."

Then proceed with content generation.

Always be encouraging and explain what the pipeline does at each stage. Show progress updates and provide helpful information about the generated content.""",
    tools=[
        # Tool functions will be added for pipeline integration
    ]
)

# Pipeline orchestrator instance for the demo
demo_orchestrator = DemoPipelineOrchestrator()

async def generate_content(topic: str, audience: str = "General audience", length: int = 1500) -> Dict[str, Any]:
    """Main entry point for content generation"""
    if not demo_orchestrator.session_id:
        await demo_orchestrator.initialize()
    
    return await demo_orchestrator.process_content_request(topic, audience, length)

# Export for WebADK integration
__all__ = ['demo_agent', 'demo_orchestrator', 'generate_content']
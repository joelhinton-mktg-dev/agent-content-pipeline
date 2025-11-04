#!/usr/bin/env python3
"""
FastAPI Wrapper for AI Content Pipeline
Production-ready API with authentication, rate limiting, and async job processing
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Add parent directory to path for pipeline imports
import sys
sys.path.append('/home/joel/ai-content-pipeline')

from pipeline_single_session import SingleSessionPipelineOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/joel/ai-content-pipeline/api/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Global job storage and API keys
job_storage: Dict[str, Dict] = {}
api_keys: Dict[str, Dict] = {
    "demo-key-001": {"name": "Demo User", "requests_used": 0, "max_requests": 10},
    "prod-key-001": {"name": "Production User", "requests_used": 0, "max_requests": 100}
}

# Results directory
RESULTS_DIR = Path("/home/joel/ai-content-pipeline/api/results")
RESULTS_DIR.mkdir(exist_ok=True)

# ========================
# Pydantic Models
# ========================

class ContentRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200, description="Content topic")
    keywords: Optional[List[str]] = Field(default=[], description="Target keywords")
    include_images: bool = Field(default=True, description="Include image placeholders")
    include_research: bool = Field(default=False, description="Include real-time research via Perplexity API")
    include_citations: bool = Field(default=False, description="Include automatic citations and bibliography (requires research)")
    include_fact_check: bool = Field(default=False, description="Include fact-checking verification against research data (requires research)")
    generate_images: bool = Field(default=False, description="Generate AI images using DALL-E 3 (requires OpenAI API key)")
    format: str = Field(default="wordpress", pattern="^(wordpress|markdown|json)$", description="Output format")
    
    @validator('topic')
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v and len(v) > 10:
            raise ValueError('Maximum 10 keywords allowed')
        return [kw.strip() for kw in v if kw.strip()] if v else []

class ContentResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time: str
    created_at: datetime

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0-100
    current_stage: Optional[str]
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime]
    error_message: Optional[str]

class ContentResult(BaseModel):
    job_id: str
    status: str
    outline: Optional[str]
    research: Optional[Dict[str, Any]]
    content: Optional[str]
    citations: Optional[Dict[str, Any]]
    images: Optional[Dict[str, Any]]
    fact_check: Optional[Dict[str, Any]]
    seo: Optional[str]
    publish: Optional[str]
    total_chars: int
    quality_score: float
    processing_time: float
    created_at: datetime
    completed_at: Optional[datetime]

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    active_jobs: int
    total_jobs_processed: int

# ========================
# Authentication
# ========================

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key and check rate limits"""
    api_key = credentials.credentials
    
    if api_key not in api_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_info = api_keys[api_key]
    
    # Check rate limit
    if key_info["requests_used"] >= key_info["max_requests"]:
        logger.warning(f"Rate limit exceeded for API key: {api_key[:10]}...")
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Max {key_info['max_requests']} requests per hour."
        )
    
    # Increment usage
    api_keys[api_key]["requests_used"] += 1
    
    logger.info(f"API key verified: {key_info['name']} ({key_info['requests_used']}/{key_info['max_requests']})")
    return key_info

# ========================
# Background Tasks
# ========================

async def cleanup_old_results():
    """Clean up results older than 24 hours"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        cleaned_count = 0
        
        for job_id, job_info in list(job_storage.items()):
            if job_info.get("created_at") and job_info["created_at"] < cutoff_time:
                # Remove from storage
                del job_storage[job_id]
                
                # Remove result files
                result_file = RESULTS_DIR / f"{job_id}.json"
                if result_file.exists():
                    result_file.unlink()
                
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old job results")
            
    except Exception as e:
        logger.error(f"Error cleaning up old results: {e}")

async def reset_rate_limits():
    """Reset rate limits every hour"""
    try:
        for api_key in api_keys:
            api_keys[api_key]["requests_used"] = 0
        logger.info("Rate limits reset for all API keys")
    except Exception as e:
        logger.error(f"Error resetting rate limits: {e}")

async def run_content_pipeline(job_id: str, request: ContentRequest):
    """Background task to run the content pipeline"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting pipeline for job {job_id}: {request.topic}")
        
        # Update job status
        job_storage[job_id].update({
            "status": "processing",
            "progress": 10,
            "current_stage": "initializing",
            "updated_at": datetime.now()
        })
        
        # Initialize orchestrator
        orchestrator = SingleSessionPipelineOrchestrator()
        
        # Initialize session
        job_storage[job_id].update({
            "progress": 20,
            "current_stage": "session_initialization",
            "updated_at": datetime.now()
        })
        
        if not await orchestrator.initialize_session():
            raise Exception("Failed to initialize pipeline session")
        
        # Stage 1: Outline
        job_storage[job_id].update({
            "progress": 30,
            "current_stage": "generating_outline",
            "updated_at": datetime.now()
        })
        
        outline_prompt = f"""Create a comprehensive SEO-optimized outline for an article about "{request.topic}".
        
Target keywords: {', '.join(request.keywords) if request.keywords else 'N/A'}
Include images: {request.include_images}

Please provide:
- Target word count: 2500-3500 words total
- Detailed section breakdowns with suggested word counts
- Primary and secondary keywords related to "{request.topic}"
- Specific image placement recommendations
- FAQ section for featured snippets
- Internal linking opportunities

Make this outline extremely detailed and actionable for content creation."""

        outline_result = await orchestrator.run_agent_in_session('outline_generator', outline_prompt)
        
        # Stage 1.5: Research (optional)
        research_data = None
        if request.include_research:
            job_storage[job_id].update({
                "progress": 40,
                "current_stage": "conducting_research",
                "updated_at": datetime.now()
            })
            
            research_data = await orchestrator.run_research_stage(outline_result)
            
        # Stage 2: Content
        job_storage[job_id].update({
            "progress": 50,
            "current_stage": "creating_content", 
            "updated_at": datetime.now()
        })
        
        # Build content prompt with optional research data
        if request.include_research and research_data and research_data['metadata'].get('successful_queries', 0) > 0:
            research_context = f"""
RESEARCH DATA AVAILABLE:
Use this current research data to enhance your article:

STATISTICS:
{chr(10).join([f"• {stat}" for stat in research_data['statistics'][:10]])}

EXPERT INSIGHTS:  
{chr(10).join([f"• {quote}" for quote in research_data['expert_quotes'][:5]])}

SOURCES FOR ATTRIBUTION:
{chr(10).join([f"• {source}" for source in research_data['sources'][:10]])}
"""
        else:
            research_context = ""

        content_prompt = f"""Now please write a complete, comprehensive article based on the outline you just created.{research_context}

Requirements:
- Write full, detailed sections for each heading in your outline
- Include current statistics, data, and expert insights{' from the research data provided above' if research_context else ''}
- Add specific examples and case studies
- Include image placeholders as suggested in your outline
- Use proper heading structure (H1, H2, H3)
- Write engaging, publication-ready content
- Target the keyword: "{request.topic}"
- Format for: {request.format}
{f"- Incorporate the research statistics and expert quotes naturally into your content" if research_context else ""}
{f"- Attribute sources appropriately when using research data" if research_context else ""}

Please provide the complete article content now."""

        content_result = await orchestrator.run_agent_in_session('research_content_creator', content_prompt)
        
        # Stage 2.5: Citations (optional)
        citation_result = None
        final_content = content_result  # Default to original content
        
        if request.include_citations:
            if not request.include_research or not research_data or research_data['metadata'].get('successful_queries', 0) == 0:
                logger.warning(f"Citations requested for job {job_id} but no research data available")
            else:
                job_storage[job_id].update({
                    "progress": 60,
                    "current_stage": "adding_citations",
                    "updated_at": datetime.now()
                })
                
                citation_result = await orchestrator.run_citation_stage(content_result, research_data)
                
                if citation_result['citation_count'] > 0:
                    final_content = citation_result['cited_content']
        
        # Stage 2.6: Image Generation (optional)
        image_result = None
        
        if request.generate_images:
            job_storage[job_id].update({
                "progress": 60,
                "current_stage": "generating_images",
                "updated_at": datetime.now()
            })
            
            # Use cited content if available, otherwise original content
            content_for_images = final_content if citation_result else content_result
            
            image_result = await orchestrator.run_image_generation_stage(content_for_images, outline_result, job_id)
        
        # Stage 2.7: Fact-Checking (optional)
        fact_check_result = None
        
        if request.include_fact_check:
            if not request.include_research or not research_data or research_data['metadata'].get('successful_queries', 0) == 0:
                logger.warning(f"Fact-checking requested for job {job_id} but no research data available")
            else:
                job_storage[job_id].update({
                    "progress": 65,
                    "current_stage": "fact_checking",
                    "updated_at": datetime.now()
                })
                
                # Use final content (with citations if available)
                content_for_fact_check = final_content if citation_result else content_result
                
                fact_check_result = await orchestrator.run_fact_check_stage(content_for_fact_check, research_data)
        
        # Stage 3: SEO
        job_storage[job_id].update({
            "progress": 70,
            "current_stage": "seo_optimization",
            "updated_at": datetime.now()
        })
        
        # Build SEO prompt considering citations, images, and fact-checking
        content_reference = "the article content you just wrote"
        if request.include_citations and citation_result and citation_result['citation_count'] > 0:
            content_reference = "the cited article content with bibliography that you just reviewed"
        
        # Add image context if images were generated
        image_context = ""
        if request.generate_images and image_result and image_result['count'] > 0:
            image_context = f"""

GENERATED IMAGES CONTEXT:
{image_result['count']} images have been generated for this content:
{chr(10).join([f"• {img.get('type', 'image')} image for {img.get('section', 'section')}: {img.get('alt_text', 'description')}" for img in image_result['images'][:5]])}

Consider these images in your SEO analysis for image optimization recommendations."""

        # Add fact-checking context if fact-checking was performed
        fact_check_context = ""
        if request.include_fact_check and fact_check_result and fact_check_result['statistics']['total_claims'] > 0:
            fact_check_context = f"""

FACT-CHECKING RESULTS:
Content accuracy score: {fact_check_result['accuracy_score']:.2f}
Claims verified: {fact_check_result['statistics']['verified']}/{fact_check_result['statistics']['total_claims']}
{f"⚠️ Unsupported claims identified: {fact_check_result['statistics']['unsupported']}" if fact_check_result['statistics']['unsupported'] > 0 else "✅ All claims well-supported"}

Consider this accuracy assessment in your SEO recommendations for E-A-T (Expertise, Authoritativeness, Trustworthiness) optimization."""

        seo_prompt = f"""Please perform comprehensive SEO optimization analysis on {content_reference}.{image_context}{fact_check_context}

Focus on:
- Technical SEO audit of the content structure
- Meta tag optimization (title tags, descriptions)
- Schema markup recommendations with code
- Featured snippet optimization opportunities
- Voice search optimization
- Internal linking strategy
- Image alt text recommendations{' and image placement optimization' if image_result and image_result['count'] > 0 else ''}
{f"- Citation and reference optimization for authority building" if citation_result and citation_result['citation_count'] > 0 else ""}
{f"- Image SEO optimization for the {image_result['count']} generated images" if image_result and image_result['count'] > 0 else ""}
{f"- E-A-T optimization based on {fact_check_result['accuracy_score']:.2f} accuracy score and fact-checking results" if fact_check_result and fact_check_result['statistics']['total_claims'] > 0 else ""}

Target keyword: "{request.topic}"
Target keywords: {', '.join(request.keywords) if request.keywords else 'N/A'}

Please analyze the content from our conversation and provide detailed SEO recommendations."""

        seo_result = await orchestrator.run_agent_in_session('seo_optimizer', seo_prompt)
        
        # Stage 4: Publishing
        job_storage[job_id].update({
            "progress": 90,
            "current_stage": "creating_publication_package",
            "updated_at": datetime.now()
        })
        
        publish_prompt = f"""Please create a complete {request.format} publication package using the article content and SEO recommendations from our conversation.

Requirements:
- {request.format.title()}-compatible formatting
- Implementation of all SEO recommendations you provided
- Complete meta tags and descriptions
- Schema markup code (JSON-LD)
- Image optimization checklist with alt text
- Internal linking implementation plan
- Publication checklist

Please create a comprehensive publication package ready for {request.format}."""

        publish_result = await orchestrator.run_agent_in_session('publishing_coordinator', publish_prompt)
        
        # Calculate metrics
        total_chars = len(outline_result) + len(content_result) + len(seo_result) + len(publish_result)
        processing_time = time.time() - start_time
        
        # Quality score calculation (basic heuristic)
        quality_score = min(100.0, (
            (len(outline_result) > 1000) * 25 +
            (len(content_result) > 2000) * 25 +
            (len(seo_result) > 500) * 25 +
            (len(publish_result) > 500) * 25
        ))
        
        # Create result object
        result = ContentResult(
            job_id=job_id,
            status="completed",
            outline=outline_result,
            research=research_data,
            content=content_result,
            citations=citation_result,
            images=image_result,
            fact_check=fact_check_result,
            seo=seo_result,
            publish=publish_result,
            total_chars=total_chars,
            quality_score=quality_score,
            processing_time=processing_time,
            created_at=job_storage[job_id]["created_at"],
            completed_at=datetime.now()
        )
        
        # Save result to file
        result_file = RESULTS_DIR / f"{job_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result.dict(), f, indent=2, default=str)
        
        # Update job storage
        job_storage[job_id].update({
            "status": "completed",
            "progress": 100,
            "current_stage": "completed",
            "updated_at": datetime.now(),
            "total_chars": total_chars,
            "quality_score": quality_score,
            "processing_time": processing_time
        })
        
        logger.info(f"Pipeline completed for job {job_id}: {total_chars} chars, {quality_score}% quality")
        
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}")
        
        job_storage[job_id].update({
            "status": "failed",
            "progress": 0,
            "current_stage": "failed",
            "updated_at": datetime.now(),
            "error_message": str(e)
        })

# ========================
# Application Lifespan
# ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting AI Content Pipeline API")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    rate_limit_task = asyncio.create_task(periodic_rate_limit_reset())
    
    yield
    
    # Cleanup
    cleanup_task.cancel()
    rate_limit_task.cancel()
    logger.info("Shutting down AI Content Pipeline API")

async def periodic_cleanup():
    """Run cleanup every hour"""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        await cleanup_old_results()

async def periodic_rate_limit_reset():
    """Reset rate limits every hour"""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        await reset_rate_limits()

# ========================
# FastAPI Application
# ========================

app = FastAPI(
    title="AI Content Pipeline API",
    description="Production-ready API for generating comprehensive, SEO-optimized content using multi-agent AI pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Track application start time
app_start_time = time.time()
total_jobs_processed = 0

# ========================
# API Endpoints
# ========================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - app_start_time,
        active_jobs=len([j for j in job_storage.values() if j.get("status") in ["queued", "processing"]]),
        total_jobs_processed=total_jobs_processed
    )

@app.post("/generate-content", response_model=ContentResponse)
@limiter.limit("10/hour")
async def generate_content(
    request: Request,
    content_request: ContentRequest,
    background_tasks: BackgroundTasks,
    api_key_info: dict = Depends(verify_api_key)
):
    """Generate content using the AI pipeline"""
    global total_jobs_processed
    
    try:
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job storage
        job_storage[job_id] = {
            "status": "queued",
            "progress": 0,
            "current_stage": "queued",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "estimated_completion": datetime.now() + timedelta(minutes=5),
            "request": content_request.dict(),
            "api_key_user": api_key_info["name"]
        }
        
        # Start background task
        background_tasks.add_task(run_content_pipeline, job_id, content_request)
        
        total_jobs_processed += 1
        
        logger.info(f"Content generation started for job {job_id} by {api_key_info['name']}")
        
        return ContentResponse(
            job_id=job_id,
            status="queued",
            message="Content generation started. Use /status/{job_id} to check progress.",
            estimated_time="2-5 minutes",
            created_at=job_storage[job_id]["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error starting content generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start content generation")

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, api_key_info: dict = Depends(verify_api_key)):
    """Get job status"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = job_storage[job_id]
    
    return JobStatus(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info["progress"],
        current_stage=job_info.get("current_stage"),
        created_at=job_info["created_at"],
        updated_at=job_info["updated_at"],
        estimated_completion=job_info.get("estimated_completion"),
        error_message=job_info.get("error_message")
    )

@app.get("/results/{job_id}", response_model=ContentResult)
async def get_job_results(job_id: str, api_key_info: dict = Depends(verify_api_key)):
    """Get job results"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = job_storage[job_id]
    
    if job_info["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Job not completed. Current status: {job_info['status']}"
        )
    
    # Load result from file
    result_file = RESULTS_DIR / f"{job_id}.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return ContentResult(**result_data)
        
    except Exception as e:
        logger.error(f"Error loading result file for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load results")

@app.get("/jobs", response_model=List[JobStatus])
async def list_jobs(api_key_info: dict = Depends(verify_api_key)):
    """List all jobs for debugging (admin only)"""
    jobs = []
    for job_id, job_info in job_storage.items():
        jobs.append(JobStatus(
            job_id=job_id,
            status=job_info["status"],
            progress=job_info["progress"],
            current_stage=job_info.get("current_stage"),
            created_at=job_info["created_at"],
            updated_at=job_info["updated_at"],
            estimated_completion=job_info.get("estimated_completion"),
            error_message=job_info.get("error_message")
        ))
    
    return jobs

# ========================
# Error Handlers
# ========================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
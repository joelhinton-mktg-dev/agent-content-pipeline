#!/usr/bin/env python3
"""
Single Session Multi-Agent Pipeline - BREAKTHROUGH APPROACH
Uses ONE continuous session with multiple agents, preserving conversation history
"""

import asyncio
import json
import time
import os
import uuid
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables from agent .env files
project_root = Path(__file__).parent
for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator', 'research_agent', 'citation_agent', 'image_agent', 'fact_check_agent']:
    env_file = project_root / agent_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded .env from {agent_dir}")

# Add agent directories to path for imports
sys.path.append('/home/joel/ai-content-pipeline')

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

class SingleSessionPipelineOrchestrator:
    """Single session orchestrator using natural conversation flow"""
    
    def __init__(self):
        self.workflow_data = {}
        self.session_service = InMemorySessionService()
        self.session = None
        self.runner = None
        self.user_id = f"pipeline_user_{int(time.time())}"
        self.session_id = f"pipeline_session_{int(time.time())}"
        
    async def initialize_session(self):
        """Initialize single session for entire pipeline"""
        try:
            print("🔧 Initializing single session for pipeline...")
            
            # Create session service
            self.session_service = InMemorySessionService()
            
            # Create the session that will be used throughout
            self.session = await self.session_service.create_session(
                app_name="ai-content-pipeline",
                user_id=self.user_id,
                session_id=self.session_id,
                state={}
            )
            
            print(f"   Session created: {self.session_id}")
            print(f"   User ID: {self.user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing session: {e}")
            return False
    
    async def run_agent_in_session(self, agent_name, prompt):
        """Run agent in the existing session (preserves conversation history)"""
        try:
            print(f"🤖 Running {agent_name} in continuous session...")
            print(f"   Session ID: {self.session_id}")
            print(f"   Prompt: {prompt[:100]}...")
            
            # Import the specific agent - Updated for all 8 agents
            if agent_name == 'outline_generator':
                from outline_generator.agent import root_agent as agent
            elif agent_name == 'research_agent':
                from research_agent.agent import root_agent as agent
            elif agent_name == 'research_content_creator':
                from research_content_creator.agent import root_agent as agent
            elif agent_name == 'citation_agent':
                from citation_agent.agent import root_agent as agent
            elif agent_name == 'image_agent':
                from image_agent.agent import root_agent as agent
            elif agent_name == 'fact_check_agent':
                from fact_check_agent.agent import root_agent as agent
            elif agent_name == 'seo_optimizer':
                from seo_optimizer.agent import root_agent as agent
            elif agent_name == 'publishing_coordinator':
                from publishing_coordinator.agent import root_agent as agent
            else:
                return f"Error: Unknown agent {agent_name}. Available agents: outline_generator, research_agent, research_content_creator, citation_agent, image_agent, fact_check_agent, seo_optimizer, publishing_coordinator"
            
            # Create runner for this agent (but use same session)
            runner = Runner(
                app_name="ai-content-pipeline",
                agent=agent,
                session_service=self.session_service
            )
            
            # Create message
            message = types.Content(parts=[types.Part(text=prompt)])
            
            # Run agent in the SAME session
            response_text = ""
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,  # Same session for all agents!
                new_message=message
            ):
                # Extract text from events
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
            
            print(f"   ✅ {agent_name} completed - {len(response_text)} characters")
            
            # Get updated session to see conversation history
            updated_session = await self.session_service.get_session(
                app_name="ai-content-pipeline",
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            print(f"   Session now has {len(updated_session.events)} events in history")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error running {agent_name} in session: {e}")
            import traceback
            traceback.print_exc()
            return f"Error running {agent_name}: {e}"
    
    async def run_research_stage(self, outline_content):
        """Stage 1.5: Conduct research using Perplexity API"""
        try:
            print("🔍 Stage 1.5: Conducting real-time research...")
            
            # Import research agent
            from research_agent.agent import research_agent
            
            # Conduct research
            research_data = await research_agent.conduct_research(outline_content)
            
            # Store research data
            self.workflow_data['research'] = research_data
            
            print(f"   ✅ Research completed: {research_data['metadata']['successful_queries']}/{research_data['metadata']['total_queries']} queries successful")
            print(f"   📊 Found: {len(research_data['statistics'])} statistics, {len(research_data['expert_quotes'])} quotes")
            
            return research_data
            
        except Exception as e:
            print(f"⚠️  Research stage failed: {e}")
            # Return empty research data so pipeline can continue
            return {
                "queries": [],
                "results": [],
                "statistics": [],
                "expert_quotes": [],
                "sources": [],
                "metadata": {"error": str(e), "successful_queries": 0, "total_queries": 0}
            }
    
    async def run_citation_stage(self, content, research_data):
        """Stage 2.5: Add citations to content based on research data"""
        try:
            print("📚 Stage 2.5: Adding citations to content...")
            
            # Import citation agent
            from citation_agent.agent import citation_agent
            
            # Add citations
            citation_result = citation_agent.add_citations(content, research_data)
            
            # Store citation data
            self.workflow_data['citations'] = citation_result
            
            print(f"   ✅ Citations added: {citation_result['citation_count']} citations")
            print(f"   📖 Bibliography entries: {len(citation_result['bibliography'])}")
            if citation_result['uncited_claims']:
                print(f"   ⚠️  Uncited claims: {len(citation_result['uncited_claims'])}")
            
            return citation_result
            
        except Exception as e:
            print(f"⚠️  Citation stage failed: {e}")
            # Return minimal citation data so pipeline can continue
            return {
                "cited_content": content,  # Return original content
                "bibliography": [],
                "citation_count": 0,
                "uncited_claims": [],
                "metadata": {"error": str(e)}
            }

    async def run_image_generation_stage(self, content, outline, job_id=None):
        """Stage 2.6: Generate images for content"""
        try:
            print("🎨 Stage 2.6: Generating contextual images...")
            
            # Import image agent
            from image_agent.agent import image_agent
            
            # Generate images
            image_result = await image_agent.generate_images(content, outline, job_id)
            
            # Store image data
            self.workflow_data['images'] = image_result
            
            print(f"   ✅ Images generated: {image_result['count']} images")
            if image_result['count'] > 0:
                print(f"   📁 Output directory: outputs/images/{image_result['metadata'].get('job_id', 'unknown')}")
                for img in image_result['images'][:3]:  # Show first 3
                    print(f"   🖼️  {img.get('type', 'image')}: {img.get('section', 'section')}")
            
            return image_result
            
        except Exception as e:
            print(f"⚠️  Image generation stage failed: {e}")
            # Return minimal image data so pipeline can continue
            return {
                "images": [],
                "manifest": {},
                "count": 0,
                "metadata": {"error": str(e)}
            }

    async def run_fact_check_stage(self, content, research_data):
        """Stage 2.7: Fact-check content against research data"""
        try:
            print("🔍 Stage 2.7: Fact-checking content claims...")
            
            # Import fact-checking agent
            from fact_check_agent.agent import fact_check_agent
            
            # Verify facts
            fact_check_result = fact_check_agent.verify_facts(content, research_data)
            
            # Store fact-checking data
            self.workflow_data['fact_check'] = fact_check_result
            
            print(f"   ✅ Fact-checking completed: {fact_check_result['statistics']['verified']}/{fact_check_result['statistics']['total_claims']} claims verified")
            print(f"   📊 Accuracy score: {fact_check_result['accuracy_score']:.2f}")
            if fact_check_result['statistics']['unsupported'] > 0:
                print(f"   ⚠️  Unsupported claims: {fact_check_result['statistics']['unsupported']}")
            
            return fact_check_result
            
        except Exception as e:
            print(f"⚠️  Fact-checking stage failed: {e}")
            # Return minimal fact-check data so pipeline can continue
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
                "metadata": {"error": str(e)}
            }

    async def run_pipeline(self, topic, include_images=True, include_research=False, include_citations=False, generate_images=False, include_fact_check=False):
        """Execute the complete single-session pipeline"""
        
        print(f"Starting Single Session Content Pipeline for: {topic}")
        print("Using ONE continuous session with natural conversation flow")
        print("=" * 60)
        
        # Initialize the single session
        if not await self.initialize_session():
            print("❌ Failed to initialize session")
            return {}
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        
        outline_prompt = f"""I need you to create a comprehensive SEO-optimized outline for an article about "{topic}".

Please provide:
- Target word count: 2500-3500 words total
- Detailed section breakdowns with suggested word counts
- Primary and secondary keywords related to "{topic}"
- Specific image placement recommendations
- FAQ section for featured snippets
- Internal linking opportunities

Make this outline extremely detailed and actionable for content creation."""

        outline_result = await self.run_agent_in_session('outline_generator', outline_prompt)
        self.workflow_data['outline'] = outline_result
        
        print("\nOUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:500] + "..." if len(outline_result) > 500 else outline_result)
        
        approval = input("\n✅ Approve outline and continue to content creation? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at outline stage")
            return self.workflow_data
        
        # Stage 1.5: Research (optional)
        research_data = None
        if include_research:
            research_data = await self.run_research_stage(outline_result)
            
            if research_data['metadata'].get('successful_queries', 0) > 0:
                print("\nRESEARCH PREVIEW:")
                print("-" * 30)
                print(f"Statistics found: {len(research_data['statistics'])}")
                for stat in research_data['statistics'][:3]:
                    print(f"  • {stat}")
                if len(research_data['expert_quotes']) > 0:
                    print(f"Expert quotes: {len(research_data['expert_quotes'])}")
                    print(f"  • \"{research_data['expert_quotes'][0][:100]}...\"")
                
                approval = input("\n✅ Approve research data and continue to content creation? (y/n): ").lower()
                if approval != 'y':
                    print("Pipeline stopped at research stage")
                    return self.workflow_data
        
        # Stage 2: Content Creation (same session - outline + research in conversation history)
        print("\n✍️ Stage 2: Creating comprehensive content...")
        
        # Build content prompt with optional research data
        if include_research and research_data and research_data['metadata'].get('successful_queries', 0) > 0:
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
- Target the keyword: "{topic}"
{f"- Incorporate the research statistics and expert quotes naturally into your content" if research_context else ""}
{f"- Attribute sources appropriately when using research data" if research_context else ""}

Please provide the complete article content now."""

        content_result = await self.run_agent_in_session('research_content_creator', content_prompt)
        self.workflow_data['content'] = content_result
        
        print("\nCONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:500] + "..." if len(content_result) > 500 else content_result)
        
        # Debug Stage 2 output
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Contains headers: {'#' in content_result or 'introduction' in content_result.lower()}")
        print(f"Contains questions asking for more: {any(phrase in content_result.lower() for phrase in ['would you like', 'should i', 'please provide', 'let me know'])}")
        
        approval = input("\n✅ Approve content and continue to citations/SEO? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 2.5: Citations (optional)
        citation_result = None
        final_content = content_result  # Default to original content
        
        if include_citations:
            if not include_research or not research_data or research_data['metadata'].get('successful_queries', 0) == 0:
                print("\n⚠️  Citations requested but no research data available. Skipping citation stage.")
            else:
                citation_result = await self.run_citation_stage(content_result, research_data)
                
                if citation_result['citation_count'] > 0:
                    final_content = citation_result['cited_content']
                    
                    print("\nCITATION PREVIEW:")
                    print("-" * 30)
                    print(f"Citations added: {citation_result['citation_count']}")
                    print(f"Bibliography entries: {len(citation_result['bibliography'])}")
                    if citation_result['uncited_claims']:
                        print(f"Uncited claims: {len(citation_result['uncited_claims'])}")
                        for claim in citation_result['uncited_claims'][:3]:
                            print(f"  • {claim['text'][:80]}...")
                    
                    approval = input("\n✅ Approve citations and continue to SEO optimization? (y/n): ").lower()
                    if approval != 'y':
                        print("Pipeline stopped at citation stage")
                        return self.workflow_data
        
        # Stage 2.6: Image Generation (optional)
        image_result = None
        
        if generate_images:
            # Create job ID for image organization
            pipeline_job_id = f"pipeline_{int(time.time())}"
            
            # Use cited content if available, otherwise original content
            content_for_images = final_content if citation_result else content_result
            
            image_result = await self.run_image_generation_stage(content_for_images, outline_result, pipeline_job_id)
            
            if image_result['count'] > 0:
                print("\nIMAGE GENERATION PREVIEW:")
                print("-" * 30)
                print(f"Images generated: {image_result['count']}")
                print(f"Output directory: outputs/images/{pipeline_job_id}")
                for img in image_result['images'][:3]:
                    print(f"  🖼️  {img.get('type', 'unknown')}: {img.get('section', 'section')}")
                
                approval = input("\n✅ Approve generated images and continue to fact-checking? (y/n): ").lower()
                if approval != 'y':
                    print("Pipeline stopped at image generation stage")
                    return self.workflow_data
        
        # Stage 2.7: Fact-Checking (optional)
        fact_check_result = None
        
        if include_fact_check:
            if not include_research or not research_data or research_data['metadata'].get('successful_queries', 0) == 0:
                print("\n⚠️  Fact-checking requested but no research data available. Skipping fact-checking stage.")
            else:
                # Use final content (with citations if available)
                content_for_fact_check = final_content if citation_result else content_result
                
                fact_check_result = await self.run_fact_check_stage(content_for_fact_check, research_data)
                
                if fact_check_result['statistics']['total_claims'] > 0:
                    print("\nFACT-CHECKING PREVIEW:")
                    print("-" * 30)
                    print(f"Claims verified: {fact_check_result['statistics']['verified']}/{fact_check_result['statistics']['total_claims']}")
                    print(f"Accuracy score: {fact_check_result['accuracy_score']:.2f}")
                    if fact_check_result['statistics']['unsupported'] > 0:
                        print(f"⚠️  Unsupported claims: {fact_check_result['statistics']['unsupported']}")
                        for claim in [c for c in fact_check_result['verified_claims'] if c['status'] == 'unsupported'][:3]:
                            print(f"  • {claim['claim'][:80]}...")
                    if fact_check_result['recommendations']:
                        print(f"📋 Recommendations: {len(fact_check_result['recommendations'])}")
                        for rec in fact_check_result['recommendations'][:2]:
                            print(f"  • {rec}")
                    
                    approval = input("\n✅ Approve fact-checking results and continue to SEO optimization? (y/n): ").lower()
                    if approval != 'y':
                        print("Pipeline stopped at fact-checking stage")
                        return self.workflow_data
        
        # Stage 3: SEO Optimization (same session - outline + content + citations + images + fact-check in conversation history)
        print("\n🎯 Stage 3: SEO optimization analysis...")
        
        # Build SEO prompt considering citations, images, and fact-checking
        content_reference = "the article content you just wrote"
        if include_citations and citation_result and citation_result['citation_count'] > 0:
            content_reference = "the cited article content with bibliography that you just reviewed"
        
        # Add image context if images were generated
        image_context = ""
        if generate_images and image_result and image_result['count'] > 0:
            image_context = f"""

GENERATED IMAGES CONTEXT:
{image_result['count']} images have been generated for this content:
{chr(10).join([f"• {img.get('type', 'image')} image for {img.get('section', 'section')}: {img.get('alt_text', 'description')}" for img in image_result['images'][:5]])}

Consider these images in your SEO analysis for image optimization recommendations."""

        # Add fact-checking context if fact-checking was performed
        fact_check_context = ""
        if include_fact_check and fact_check_result and fact_check_result['statistics']['total_claims'] > 0:
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

Target keyword: "{topic}"

Please analyze the content from our conversation and provide detailed SEO recommendations."""

        seo_result = await self.run_agent_in_session('seo_optimizer', seo_prompt)
        self.workflow_data['seo'] = seo_result
        
        print("\nSEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:500] + "..." if len(seo_result) > 500 else seo_result)
        
        # Debug Stage 3 output
        print(f"\n🔍 DEBUG Stage 3 Output:")
        print(f"SEO result length: {len(seo_result)} characters")
        print(f"Contains SEO elements: {any(term in seo_result.lower() for term in ['meta', 'title', 'schema', 'keywords', 'optimization'])}")
        print(f"References conversation context: {'article' in seo_result.lower() or 'content' in seo_result.lower()}")
        
        approval = input("\n✅ Approve SEO optimization and continue to publication package? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at SEO stage")
            return self.workflow_data
        
        # Stage 4: Publication Package (same session - full conversation history available)
        print("\n📦 Stage 4: Creating publication package...")
        
        publish_prompt = f"""Please create a complete WordPress publication package using the article content and SEO recommendations from our conversation.

Requirements:
- WordPress-compatible HTML formatting
- Implementation of all SEO recommendations you provided
- Complete meta tags and descriptions
- Schema markup code (JSON-LD)
- Image optimization checklist with alt text
- Internal linking implementation plan
- Publication checklist
- Yoast SEO settings

Please create a comprehensive publication package ready for WordPress."""

        publish_result = await self.run_agent_in_session('publishing_coordinator', publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("Single session pipeline finished successfully!")
        
        # Final session summary
        final_session = await self.session_service.get_session(
            app_name="ai-content-pipeline",
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        print(f"\n🔍 FINAL SESSION SUMMARY:")
        print(f"Total conversation events: {len(final_session.events)}")
        print(f"Session state keys: {list(final_session.state.keys())}")
        print(f"Pipeline stages completed: {len(self.workflow_data)}")
        
        for stage, content in self.workflow_data.items():
            print(f"  - {stage}: {len(content)} characters")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results to output directory"""
        timestamp = int(time.time())
        output_dir = Path(f"single_session_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                if stage in ['research', 'citations', 'images', 'fact_check'] and isinstance(content, dict):
                    # Save structured data as formatted JSON
                    f.write(json.dumps(content, indent=2, default=str))
                else:
                    f.write(str(content))
        
        # Also save session summary
        session_summary = f"""Single Session Pipeline Results
Topic: {topic}
Session ID: {self.session_id}
User ID: {self.user_id}
Completed Stages: {len(self.workflow_data)}

Stage Results:
"""
        for stage, content in self.workflow_data.items():
            session_summary += f"- {stage}: {len(content)} characters\n"
        
        summary_file = output_dir / "session_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(session_summary)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir

async def main():
    orchestrator = SingleSessionPipelineOrchestrator()
    
    try:
        print("🚀 Single Session AI Content Pipeline - Natural Conversation Flow")
        print("=" * 60)
        
        topic = input("Enter your content topic: ")
        include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
        include_research = input("Include real-time research? (y/n): ").lower() == 'y'
        include_citations = False
        include_fact_check = False
        generate_images = False
        
        if include_research:
            include_citations = input("Include automatic citations? (y/n): ").lower() == 'y'
            include_fact_check = input("Include fact-checking verification? (y/n): ").lower() == 'y'
        
        generate_images = input("Generate AI images with DALL-E 3? (y/n): ").lower() == 'y'
        
        print(f"\n🎬 Starting single session pipeline...")
        print("Note: All agents work in ONE continuous conversation")
        print("Previous outputs automatically available to subsequent agents")
        if include_research:
            print("🔍 Research stage enabled - will gather current data and insights")
        if include_citations:
            print("📚 Citation stage enabled - will add citations and bibliography")
        if include_fact_check:
            print("🔍 Fact-checking stage enabled - will verify content accuracy")
        if generate_images:
            print("🎨 Image generation enabled - will create contextual images")
        
        # Run the single session pipeline
        results = await orchestrator.run_pipeline(topic, include_images, include_research, include_citations, generate_images, include_fact_check)
        
        # Save results
        output_dir = orchestrator.save_results(topic)
        
        print(f"\n✨ Single session pipeline completed! Check {output_dir} for all outputs.")
        print("\n🎯 KEY BREAKTHROUGH:")
        print("This approach uses natural conversation flow - each agent builds on previous context!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
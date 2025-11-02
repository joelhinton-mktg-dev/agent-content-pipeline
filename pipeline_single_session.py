#!/usr/bin/env python3
"""
Single Session Multi-Agent Pipeline - BREAKTHROUGH APPROACH
Uses ONE continuous session with multiple agents, preserving conversation history
"""

import asyncio
import time
import os
import uuid
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables from agent .env files
project_root = Path(__file__).parent
for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator']:
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
            
            # Import the specific agent
            if agent_name == 'outline_generator':
                from outline_generator.agent import root_agent as agent
            elif agent_name == 'research_content_creator':
                from research_content_creator.agent import root_agent as agent
            elif agent_name == 'seo_optimizer':
                from seo_optimizer.agent import root_agent as agent
            elif agent_name == 'publishing_coordinator':
                from publishing_coordinator.agent import root_agent as agent
            else:
                return f"Error: Unknown agent {agent_name}"
            
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
    
    async def run_pipeline(self, topic, include_images=True):
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
        
        # Stage 2: Content Creation (same session - outline is in conversation history)
        print("\n✍️ Stage 2: Creating comprehensive content...")
        
        content_prompt = f"""Now please write a complete, comprehensive article based on the outline you just created.

Requirements:
- Write full, detailed sections for each heading in your outline
- Include current statistics, data, and expert insights
- Add specific examples and case studies
- Include image placeholders as suggested in your outline
- Use proper heading structure (H1, H2, H3)
- Write engaging, publication-ready content
- Target the keyword: "{topic}"

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
        
        approval = input("\n✅ Approve content and continue to SEO optimization? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization (same session - outline + content in conversation history)
        print("\n🎯 Stage 3: SEO optimization analysis...")
        
        seo_prompt = f"""Please perform comprehensive SEO optimization analysis on the article content you just wrote.

Focus on:
- Technical SEO audit of the content structure
- Meta tag optimization (title tags, descriptions)
- Schema markup recommendations with code
- Featured snippet optimization opportunities
- Voice search optimization
- Internal linking strategy
- Image alt text recommendations

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
                f.write(content)
        
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
        
        print(f"\n🎬 Starting single session pipeline...")
        print("Note: All agents work in ONE continuous conversation")
        print("Previous outputs automatically available to subsequent agents")
        
        # Run the single session pipeline
        results = await orchestrator.run_pipeline(topic, include_images)
        
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
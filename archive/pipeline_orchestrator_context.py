#!/usr/bin/env python3
"""
Context-Based ADK Multi-Agent Pipeline with Proper Runner Integration
Uses ADK's Runner and Session API for context passing between stages
"""

import asyncio
import time
import uuid
from pathlib import Path
import sys
import os

# Add agent directories to path for imports
sys.path.append('/home/joel/ai-content-pipeline')

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from outline_generator.agent import root_agent as outline_agent
from research_content_creator.agent import root_agent as content_agent  
from seo_optimizer.agent import root_agent as seo_agent
from publishing_coordinator.agent import root_agent as publish_agent

class ContextPipelineOrchestrator:
    """Context-based orchestrator that uses ADK Runner and Sessions for data passing"""
    
    def __init__(self):
        self.workflow_data = {}
        self.agents = {
            'outline_generator': outline_agent,
            'research_content_creator': content_agent,
            'seo_optimizer': seo_agent,
            'publishing_coordinator': publish_agent
        }
        self.session_service = InMemorySessionService()
        
    async def run_agent_with_runner(self, agent_name, prompt, session_state=None):
        """Run agent using proper ADK Runner with session state"""
        try:
            agent = self.agents[agent_name]
            
            # Create a runner for this agent
            runner = Runner(
                app_name="content_pipeline",
                agent=agent,
                session_service=self.session_service
            )
            
            # Create user and session IDs
            user_id = "pipeline_user"
            session_id = f"{agent_name}_{int(time.time())}"
            
            print(f"🤖 Running {agent_name} with Runner...")
            print(f"   Session ID: {session_id}")
            print(f"   State keys: {list(session_state.keys()) if session_state else 'None'}")
            
            # Create session with initial state
            session = await self.session_service.create_session(
                app_name="content_pipeline",
                user_id=user_id,
                session_id=session_id,
                state=session_state or {}
            )
            
            print(f"   Session created with state: {session.state}")
            
            # Create message content
            message = types.Content(parts=[types.Part(text=prompt)])
            
            # Run the agent
            result_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ):
                # Extract text from agent response events
                if hasattr(event, 'type') and event.type == 'agent_response':
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                result_text += part.text
                elif hasattr(event, 'content') and event.content:
                    # Handle other event types that might contain content
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            result_text += part.text
            
            # Get updated session state
            updated_session = await self.session_service.get_session(
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"✅ {agent_name} completed - {len(result_text)} chars")
            print(f"   Updated state keys: {list(updated_session.state.keys())}")
            
            return result_text, updated_session.state
            
        except Exception as e:
            print(f"❌ Error in run_agent_with_runner for {agent_name}: {e}")
            import traceback
            traceback.print_exc()
            return f"Error running {agent_name}: {e}", session_state or {}
    
    async def run_pipeline(self, topic, include_images=True):
        """Execute the complete context-based pipeline"""
        
        print(f"Starting Context-Based Content Pipeline for: {topic}")
        print("=" * 60)
        
        # Initialize shared session state
        session_state = {
            "temp:pipeline_topic": topic,
            "temp:include_images": include_images
        }
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        outline_prompt = f"""Create a comprehensive SEO-optimized outline for "{topic}".

CONTEXT ACCESS: 
- Topic is available in context.state["temp:pipeline_topic"]
- Use context.state.get("temp:pipeline_topic") to access it
- Store your outline in context.state["temp:outline_result"]

REQUIREMENTS:
- Target word count: 2500-3500 words
- Include primary and secondary keywords
- Detailed section breakdowns with word counts
- Specific image placement recommendations with descriptions
- FAQ section for featured snippets

Make this outline extremely detailed and actionable for content creation."""

        outline_result, session_state = await self.run_agent_with_runner(
            'outline_generator', outline_prompt, session_state
        )
        self.workflow_data['outline'] = outline_result
        
        print("OUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:400] + "..." if len(outline_result) > 400 else outline_result)
        
        approval = input("\n✅ Approve outline and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at outline stage")
            return self.workflow_data
        
        # Stage 2: Content Creation
        print("\n✍️ Stage 2: Creating content...")
        content_prompt = f"""Write a complete, comprehensive article.

CONTEXT ACCESS:
- Retrieve outline from context.state.get("temp:outline_result")
- Retrieve topic from context.state.get("temp:pipeline_topic")
- Store your article in context.state["temp:content_article"]

INSTRUCTIONS:
- Write full sections with proper depth and detail for each heading in the outline
- Include current statistics and data
- Add specific examples and case studies
- Include image placeholders and visual content suggestions
- Use proper heading structure (H1, H2, H3) as specified in the outline
- Write actual content, not questions or requests for more information

OUTPUT: Provide the complete, publication-ready article content."""

        content_result, session_state = await self.run_agent_with_runner(
            'research_content_creator', content_prompt, session_state
        )
        self.workflow_data['content'] = content_result
        
        print("CONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:400] + "..." if len(content_result) > 400 else content_result)
        
        # Debug content quality
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Content contains questions: {any(phrase in content_result.lower() for phrase in ['would you like', 'should i', 'please provide'])}")
        
        approval = input("\n✅ Approve content and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization
        print("\n🎯 Stage 3: SEO optimization...")
        seo_prompt = f"""Perform SEO optimization analysis.

CONTEXT ACCESS:
- Retrieve article content from context.state.get("temp:content_article")
- Retrieve topic from context.state.get("temp:pipeline_topic")
- Store your SEO analysis in context.state["temp:seo_recommendations"]

TASK: Analyze the article content from context and provide:
- Complete technical SEO audit
- Schema markup recommendations with code
- Meta tag optimization (multiple variations)
- Featured snippet optimization
- Voice search optimization

Base ALL recommendations on the specific content retrieved from context."""

        seo_result, session_state = await self.run_agent_with_runner(
            'seo_optimizer', seo_prompt, session_state
        )
        self.workflow_data['seo'] = seo_result
        
        print("SEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:400] + "..." if len(seo_result) > 400 else seo_result)
        
        approval = input("\n✅ Approve SEO optimization and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at SEO stage")
            return self.workflow_data
        
        # Stage 4: Publication Package
        print("\n📦 Stage 4: Creating publication package...")
        publish_prompt = f"""Create complete publication package.

CONTEXT ACCESS:
- Retrieve article content from context.state.get("temp:content_article")
- Retrieve SEO recommendations from context.state.get("temp:seo_recommendations") 
- Retrieve topic from context.state.get("temp:pipeline_topic")
- Store your package in context.state["temp:publication_package"]

PUBLISHING PLATFORM: WordPress with Yoast SEO

PACKAGE REQUIREMENTS:
- WordPress-formatted HTML with proper blocks
- Complete meta tags and descriptions
- Schema markup code
- Image optimization checklist
- Internal linking implementation"""

        publish_result, session_state = await self.run_agent_with_runner(
            'publishing_coordinator', publish_prompt, session_state
        )
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("Context-based pipeline finished successfully!")
        print(f"\n🔍 FINAL SESSION STATE:")
        print(f"   State keys: {list(session_state.keys())}")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results"""
        timestamp = int(time.time())
        output_dir = Path(f"context_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir

async def main():
    orchestrator = ContextPipelineOrchestrator()
    
    print("🚀 AI Content Pipeline - Context-Based Agent Communication")
    print("=" * 60)
    
    topic = input("Enter your content topic: ")
    include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
    
    print(f"\n🎬 Starting context-based pipeline...")
    print("Note: Data passes via ADK context.state between agents")
    
    # Run the context-based pipeline
    results = await orchestrator.run_pipeline(topic, include_images)
    
    # Save results
    output_dir = orchestrator.save_results(topic)
    
    print(f"\n✨ Context-based pipeline completed! Check {output_dir} for all outputs.")

if __name__ == "__main__":
    asyncio.run(main())
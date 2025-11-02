#!/usr/bin/env python3
"""
Direct Import ADK Multi-Agent Pipeline - No Context Required
Uses direct prompts but with proper agent imports instead of subprocess calls
"""

import asyncio
import time
from pathlib import Path
import sys
import os

# Add agent directories to path for imports
sys.path.append('/home/joel/ai-content-pipeline')

try:
    from outline_generator.agent import root_agent as outline_agent
    from research_content_creator.agent import root_agent as content_agent  
    from seo_optimizer.agent import root_agent as seo_agent
    from publishing_coordinator.agent import root_agent as publish_agent
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class DirectPipelineOrchestrator:
    """Direct import orchestrator - cleaner than subprocess approach"""
    
    def __init__(self):
        self.workflow_data = {}
        self.agents = {
            'outline_generator': outline_agent,
            'research_content_creator': content_agent,
            'seo_optimizer': seo_agent,
            'publishing_coordinator': publish_agent
        }
        
    async def run_agent_direct(self, agent_name, prompt):
        """Run agent directly with prompt"""
        try:
            agent = self.agents[agent_name]
            
            print(f"🤖 Running {agent_name} directly...")
            print(f"   Prompt length: {len(prompt)} characters")
            
            # Run agent - try different methods based on ADK version
            try:
                if hasattr(agent, 'run_async'):
                    # Use async method if available
                    result_generator = agent.run_async(prompt)
                    result = ""
                    async for chunk in result_generator:
                        result += chunk
                elif hasattr(agent, 'invoke'):
                    # Use invoke method if available  
                    result = await agent.invoke(prompt)
                elif hasattr(agent, 'run'):
                    # Use sync run method
                    result = agent.run(prompt)
                else:
                    # Try calling the agent directly
                    result = await agent(prompt)
                    
            except Exception as e:
                print(f"❌ Error running {agent_name}: {e}")
                return f"Error running {agent_name}: {e}"
            
            print(f"✅ {agent_name} completed - {len(result)} characters")
            return result
            
        except Exception as e:
            print(f"❌ Error in run_agent_direct for {agent_name}: {e}")
            return f"Error running {agent_name}: {e}"
    
    async def run_pipeline(self, topic, include_images=True):
        """Execute the complete direct import pipeline"""
        
        print(f"Starting Direct Import Content Pipeline for: {topic}")
        print("=" * 60)
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        outline_prompt = f"""Create a comprehensive SEO-optimized outline for "{topic}".

REQUIREMENTS:
- Target word count: 2500-3500 words
- Include primary and secondary keywords
- Detailed section breakdowns with word counts
- Specific image placement recommendations with descriptions
- FAQ section for featured snippets
- Competitor analysis insights

Store your final outline in context using: context.state["temp:outline_result"] = your_outline

Make this outline extremely detailed and actionable for content creation."""

        outline_result = await self.run_agent_direct('outline_generator', outline_prompt)
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
        content_prompt = f"""TASK: Write a complete, comprehensive article based on the outline provided below.

Your instructions specify to retrieve the outline from context.state["temp:outline_result"], but since context isn't working, here is the outline directly:

OUTLINE PROVIDED:
{outline_result}

INSTRUCTIONS:
- Write full sections with proper depth and detail for each heading in the outline
- Include current statistics and data
- Add specific examples and case studies
- Include image placeholders and visual content suggestions throughout the final content
- Use proper heading structure (H1, H2, H3) as specified in the outline
- Include internal linking suggestions
- Write actual content, not questions or requests for more information
- Store your final article in context using: context.state["temp:content_article"] = your_article

OUTPUT: Provide the complete, publication-ready article content with all sections written out in full.
DO NOT ask questions. DO NOT request additional information. Write the complete article now."""

        content_result = await self.run_agent_direct('research_content_creator', content_prompt)
        self.workflow_data['content'] = content_result
        
        print("CONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:400] + "..." if len(content_result) > 400 else content_result)
        
        # Debug content_result
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Content contains questions: {any(phrase in content_result.lower() for phrase in ['would you like', 'should i', 'please provide', 'once you'])}")
        
        approval = input("\n✅ Approve content and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization
        print("\n🎯 Stage 3: SEO optimization...")
        seo_prompt = f"""Your instructions specify to retrieve article content from context.state["temp:content_article"], but since context isn't working, here is the complete article content:

TARGET KEYWORD: "{topic}"
FOCUS AREAS: Featured snippets and People Also Ask optimization

COMPLETE ARTICLE CONTENT:
{content_result}

MANDATORY TASK: Perform SEO optimization analysis on the article content provided above.

ANALYSIS REQUIREMENTS:
- Complete technical SEO audit of the content provided above
- Schema markup recommendations with code
- Meta tag optimization (multiple variations) 
- Featured snippet optimization
- Voice search optimization
- ALL recommendations must be based on the article content shown above
- Store your SEO recommendations in context using: context.state["temp:seo_recommendations"] = your_seo_analysis

BEGIN YOUR SEO ANALYSIS OF THE ARTICLE CONTENT PROVIDED ABOVE NOW."""

        seo_result = await self.run_agent_direct('seo_optimizer', seo_prompt)
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
        publish_prompt = f"""Your instructions specify to retrieve content from context.state["temp:content_article"] and SEO data from context.state["temp:seo_recommendations"], but since context isn't working, here is the data directly:

CONTENT:
{content_result}

SEO RECOMMENDATIONS:
{seo_result}

PUBLISHING PLATFORM: WordPress with Yoast SEO
INSTRUCTION: Create complete publication package with all required elements.

PACKAGE REQUIREMENTS:
- WordPress-formatted HTML with proper blocks
- Complete meta tags and descriptions
- Schema markup code
- Image optimization checklist
- Internal linking implementation
- Store your publication package in context using: context.state["temp:publication_package"] = your_package"""

        publish_result = await self.run_agent_direct('publishing_coordinator', publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("Direct import pipeline finished successfully!")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results"""
        timestamp = int(time.time())
        output_dir = Path(f"direct_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir

async def main():
    orchestrator = DirectPipelineOrchestrator()
    
    print("🚀 AI Content Pipeline - Direct Import Agent Communication")
    print("=" * 60)
    
    topic = input("Enter your content topic: ")
    include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
    
    print(f"\n🎬 Starting direct import pipeline...")
    print("Note: Using direct agent imports instead of subprocess calls")
    
    # Run the direct import pipeline
    results = await orchestrator.run_pipeline(topic, include_images)
    
    # Save results
    output_dir = orchestrator.save_results(topic)
    
    print(f"\n✨ Direct import pipeline completed! Check {output_dir} for all outputs.")

if __name__ == "__main__":
    asyncio.run(main())
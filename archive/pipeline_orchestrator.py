#!/usr/bin/env python3
"""
ADK Multi-Agent Pipeline with Automatic Agent Communication
Eliminates copy-paste between agents while maintaining approval checkpoints
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
import sys
import os

# Import your existing agents
sys.path.append('outline_generator')
sys.path.append('research_content_creator')
sys.path.append('seo_optimizer')
sys.path.append('publishing_coordinator')

from outline_generator.agent import root_agent as outline_agent
from research_content_creator.agent import root_agent as content_agent
from seo_optimizer.agent import root_agent as seo_agent
from publishing_coordinator.agent import root_agent as publish_agent

class ContentPipelineOrchestrator(Agent):
    """Orchestrator agent that manages the 4-agent workflow"""
    
    def __init__(self):
        super().__init__(
            model='gemini-2.5-flash',
            name='pipeline_orchestrator',
            description='Orchestrates the complete content creation pipeline with agent-to-agent communication',
            instruction="""You are the Content Pipeline Orchestrator. Your role is to manage a 4-stage content creation workflow:

1. OUTLINE GENERATION: Create comprehensive SEO outline with image recommendations
2. CONTENT CREATION: Write detailed content based on the outline  
3. SEO OPTIMIZATION: Analyze and optimize content for search engines
4. PUBLICATION PACKAGE: Create ready-to-publish WordPress package

WORKFLOW PROCESS:
- Take user's topic input
- Automatically coordinate between all 4 agents
- Pass outputs seamlessly between stages
- Provide approval checkpoints for human oversight (20%)
- Deliver final publication-ready package

You will ask for approval after each major stage while automating the data transfer between agents.""",
            tools=[google_search]
        )
        
        self.agents = {
            'outline': outline_agent,
            'content': content_agent,
            'seo': seo_agent,
            'publish': publish_agent
        }
        
        self.workflow_data = {}
    
    async def run_pipeline(self, topic, include_images=True):
        """Execute the complete pipeline with agent-to-agent communication"""
        
        print(f"Starting Content Pipeline for: {topic}")
        print("=" * 50)
        
        # Stage 1: Outline Generation
        print("Stage 1: Generating outline...")
        outline_prompt = f"Create a comprehensive SEO-optimized outline for '{topic}'"
        if include_images:
            outline_prompt += " with specific image placement recommendations"
        
        outline_result = await self.agents['outline'].invoke(outline_prompt)
        self.workflow_data['outline'] = outline_result
        
        # Human approval checkpoint
        print("\nOUTLINE GENERATED:")
        print("-" * 30)
        print(outline_result[:500] + "..." if len(outline_result) > 500 else outline_result)
        
        approval = input("\nApprove outline? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at outline stage")
            return self.workflow_data
        
        # Stage 2: Content Creation (automatic handoff)
        print("\nStage 2: Creating content...")
        content_prompt = f"Using this outline, write comprehensive content with current data and research:\n\n{outline_result}"
        if include_images:
            content_prompt += "\n\nInclude image placeholders as specified in the outline."
        
        content_result = await self.agents['content'].invoke(content_prompt)
        self.workflow_data['content'] = content_result
        
        # Human approval checkpoint
        print("\nCONTENT CREATED:")
        print("-" * 30)
        print(content_result[:500] + "..." if len(content_result) > 500 else content_result)
        
        approval = input("\nApprove content? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization (automatic handoff)
        print("\nStage 3: SEO optimization...")
        seo_prompt = f"Optimize this content for SEO/AEO/GEO with target keyword '{topic}':\n\n{content_result}"
        
        seo_result = await self.agents['seo'].invoke(seo_prompt)
        self.workflow_data['seo'] = seo_result
        
        # Human approval checkpoint
        print("\nSEO OPTIMIZATION COMPLETE:")
        print("-" * 30)
        print(seo_result[:500] + "..." if len(seo_result) > 500 else seo_result)
        
        approval = input("\nApprove SEO optimization? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at SEO stage")
            return self.workflow_data
        
        # Stage 4: Publication Package (automatic handoff)
        print("\nStage 4: Creating publication package...")
        publish_prompt = f"""Create WordPress publication package using:

CONTENT:
{content_result}

SEO RECOMMENDATIONS:
{seo_result}

Platform: WordPress with Yoast SEO"""
        
        publish_result = await self.agents['publish'].invoke(publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        # Final output
        print("\nPUBLICATION PACKAGE COMPLETE:")
        print("-" * 30)
        print("Complete pipeline finished successfully!")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results"""
        import time
        from pathlib import Path
        
        timestamp = int(time.time())
        output_dir = Path(f"automated_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\nAll results saved to: {output_dir}")
        return output_dir

# Main pipeline execution
async def main():
    orchestrator = ContentPipelineOrchestrator()
    
    print("AI Content Pipeline - Automated Agent Communication")
    print("=" * 55)
    
    topic = input("Enter your content topic: ")
    include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
    
    # Run the automated pipeline
    results = await orchestrator.run_pipeline(topic, include_images)
    
    # Save results
    output_dir = orchestrator.save_results(topic)
    
    print(f"\nPipeline completed! Check {output_dir} for all outputs.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

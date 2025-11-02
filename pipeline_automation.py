#!/usr/bin/env python3
"""
AI Content Pipeline Automation
Orchestrates the 4-agent workflow with minimal human intervention
"""

import subprocess
import json
import time
import os
from pathlib import Path

class ContentPipelineOrchestrator:
    def __init__(self):
        self.agents = [
            'outline_generator',
            'research_content_creator', 
            'seo_optimizer',
            'publishing_coordinator'
        ]
        self.workflow_data = {}
        
    def run_agent_query(self, agent_name, prompt):
        """Run a query against a specific agent via ADK CLI"""
        try:
            # Use ADK CLI to run agent with prompt
            cmd = f"echo '{prompt}' | adk run {agent_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=".")
            return result.stdout
        except Exception as e:
            print(f"Error running {agent_name}: {e}")
            return None
    
    def get_user_approval(self, stage, content_preview):
        """Get user approval before proceeding to next stage"""
        print(f"\n{'='*60}")
        print(f"STAGE: {stage}")
        print(f"{'='*60}")
        print(f"Preview:\n{content_preview[:500]}...")
        print(f"{'='*60}")
        
        response = input(f"\nApprove {stage}? (y/n/edit): ").lower()
        
        if response == 'y':
            return 'approved'
        elif response == 'edit':
            return 'edit'
        else:
            return 'rejected'
    
    def run_pipeline(self, topic, target_keyword=None, include_images=True):
        """Run the complete 4-agent pipeline"""
        print(f"Starting AI Content Pipeline for topic: {topic}")
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        outline_prompt = f"Create an SEO-optimized outline for '{topic}'"
        if include_images:
            outline_prompt += " with image placement recommendations"
            
        outline_result = self.run_agent_query('outline_generator', outline_prompt)
        
        approval = self.get_user_approval("Outline Generation", outline_result)
        if approval != 'approved':
            print("Pipeline stopped at outline stage")
            return
            
        self.workflow_data['outline'] = outline_result
        
        # Stage 2: Content Creation
        print("\n✍️ Stage 2: Creating content...")
        content_prompt = f"Using this outline, write comprehensive content with current data and research:\n\n{outline_result}"
        if include_images:
            content_prompt += "\n\nInclude image placeholders as specified in the outline."
            
        content_result = self.run_agent_query('research_content_creator', content_prompt)
        
        approval = self.get_user_approval("Content Creation", content_result)
        if approval != 'approved':
            print("Pipeline stopped at content stage")
            return
            
        self.workflow_data['content'] = content_result
        
        # Stage 3: SEO Optimization  
        print("\n🎯 Stage 3: SEO optimization...")
        seo_prompt = f"Optimize this content for SEO/AEO/GEO"
        if target_keyword:
            seo_prompt += f" with target keyword '{target_keyword}'"
        seo_prompt += f":\n\n{content_result}"
        
        seo_result = self.run_agent_query('seo_optimizer', seo_prompt)
        
        approval = self.get_user_approval("SEO Optimization", seo_result)
        if approval != 'approved':
            print("Pipeline stopped at SEO stage")
            return
            
        self.workflow_data['seo_recommendations'] = seo_result
        
        # Stage 4: Publishing Preparation
        print("\n📦 Stage 4: Preparing publication package...")
        publish_prompt = f"Create WordPress publication package using:\n\nCONTENT:\n{content_result}\n\nSEO RECOMMENDATIONS:\n{seo_result}"
        
        publish_result = self.run_agent_query('publishing_coordinator', publish_prompt)
        
        approval = self.get_user_approval("Publication Package", publish_result)
        if approval == 'approved':
            self.workflow_data['final_package'] = publish_result
            self.save_workflow_results(topic)
            print("\n✅ Pipeline completed successfully!")
        else:
            print("Pipeline stopped at publishing stage")
    
    def save_workflow_results(self, topic):
        """Save all workflow results to files"""
        timestamp = int(time.time())
        output_dir = Path(f"output_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"Results saved to: {output_dir}")

def main():
    """Main pipeline interface"""
    orchestrator = ContentPipelineOrchestrator()
    
    print("AI Content Creation Pipeline - Automated Workflow")
    print("="*50)
    
    topic = input("Enter your content topic: ")
    target_keyword = input("Enter target keyword (optional): ") or None
    include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
    
    orchestrator.run_pipeline(topic, target_keyword, include_images)

if __name__ == "__main__":
    main()

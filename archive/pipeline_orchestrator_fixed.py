#!/usr/bin/env python3
"""
Fixed ADK Multi-Agent Pipeline with Automatic Agent Communication
"""

import subprocess
import asyncio
import time
from pathlib import Path

class SimplePipelineOrchestrator:
    """Simple orchestrator that manages agent communication via ADK CLI"""
    
    def __init__(self):
        self.workflow_data = {}
        self.agent_names = [
            'outline_generator',
            'research_content_creator', 
            'seo_optimizer',
            'publishing_coordinator'
        ]
    
    def run_agent(self, agent_name, prompt):
        """Run ADK agent via CLI"""
        try:
            # Write prompt to temp file
            temp_file = f"/tmp/agent_prompt_{agent_name}_{int(time.time())}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            # Run agent with timeout
            cmd = f"cat {temp_file} | timeout 120 adk run {agent_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
            return self.clean_output(result.stdout)
            
        except Exception as e:
            return f"Error running {agent_name}: {e}"
    
    def clean_output(self, raw_output):
        """Clean ADK CLI output while preserving agent responses"""
        if not raw_output or len(raw_output.strip()) == 0:
            return "No output received from agent"
        
        lines = raw_output.split('\n')
        cleaned_lines = []
        
        # Patterns to skip (system messages)
        skip_patterns = [
            'Log setup complete',
            'To access latest log',
            'Running agent',
            'type exit to exit',
            '[user]:',
            'outline_generator',
            'research_content_creator',
            'seo_optimizer',  
            'publishing_coordinator'
        ]
        
        # Look for actual agent output
        agent_output_started = False
        for line in lines:
            # Start capturing after we see meaningful content
            if any(word in line.lower() for word in ['#', 'title:', 'outline:', 'content:', 'seo:', 'analysis:', 'recommendations:']):
                agent_output_started = True
            
            # Skip system messages but capture everything else once agent output starts
            if agent_output_started or not any(skip in line for skip in skip_patterns):
                if line.strip():  # Only include non-empty lines
                    cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # If we didn't capture much, return more of the raw output
        if len(result) < 100:
            # Filter out only the most obvious system messages
            basic_skip = ['Log setup complete', 'To access latest log', 'type exit to exit']
            basic_cleaned = []
            for line in lines:
                if not any(skip in line for skip in basic_skip):
                    basic_cleaned.append(line)
            result = '\n'.join(basic_cleaned).strip()
        
        return result if result else raw_output.strip()
    
    def run_pipeline(self, topic, include_images=True):
        """Execute the complete pipeline with automatic handoffs"""
        
        print(f"Starting Automated Content Pipeline for: {topic}")
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

MANDATORY: Include specific image placement recommendations and placeholder text throughout this outline.

Make this outline extremely detailed and actionable for content creation."""

        outline_result = self.run_agent('outline_generator', outline_prompt)
        self.workflow_data['outline'] = outline_result
        
        print("OUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:400] + "..." if len(outline_result) > 400 else outline_result)
        
        approval = input("\n✅ Approve outline and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at outline stage")
            return self.workflow_data
        
        # Stage 2: Content Creation (automatic handoff)
        print("\n✍️ Stage 2: Creating content...")
        content_prompt = f"""TASK: Write a complete, comprehensive article based on the outline provided below.

OUTLINE PROVIDED:
{outline_result}

INSTRUCTIONS:
- Write full sections with proper depth and detail for each heading in the outline
- Include current statistics and data
- Add specific examples and case studies
- MANDATORY: Include image placeholders and visual content suggestions throughout the final content
- Use proper heading structure (H1, H2, H3) as specified in the outline
- Include internal linking suggestions
- Write actual content, not questions or requests for more information

OUTPUT: Provide the complete, publication-ready article content with all sections written out in full.
DO NOT ask questions. DO NOT request additional information. Write the complete article now."""

        content_result = self.run_agent('research_content_creator', content_prompt)
        self.workflow_data['content'] = content_result
        
        print("CONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:400] + "..." if len(content_result) > 400 else content_result)
        
        # Debug content_result
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Content result is empty: {len(content_result.strip()) == 0}")
        print(f"Content contains 'provide the content': {'provide the content' in content_result.lower()}")
        print(f"Content contains 'Should I include': {'Should I include' in content_result}")
        print(f"Content contains 'Would you like': {'Would you like' in content_result}")
        print(f"Content starts with actual content: {not any(phrase in content_result[:200].lower() for phrase in ['would you like', 'should i', 'please provide', 'once you'])}")
        print(f"First 200 chars of content_result: {content_result[:200]}")
        
        approval = input("\n✅ Approve content and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization (automatic handoff)
        print("\n🎯 Stage 3: SEO optimization...")
        
        # Debug content embedding
        print(f"\n🔍 DEBUG Stage 2→3 Handoff:")
        print(f"About to embed content_result ({len(content_result)} chars) into SEO prompt")
        
        seo_prompt = f"""ATTENTION: THE COMPLETE ARTICLE CONTENT IS PROVIDED BELOW IN THIS PROMPT. DO NOT ASK FOR MORE CONTENT.

TARGET KEYWORD: "{topic}"
FOCUS AREAS: Featured snippets and People Also Ask optimization

!!! IMPORTANT: THE FULL ARTICLE CONTENT IS BETWEEN THE LINES BELOW !!!
==================== START OF ARTICLE CONTENT ====================
{content_result}
===================== END OF ARTICLE CONTENT =====================

*** CRITICAL INSTRUCTIONS ***
1. THE ARTICLE CONTENT IS ALREADY PROVIDED ABOVE BETWEEN THE DELIMITER LINES
2. DO NOT ASK FOR THE CONTENT - IT IS ALREADY IN THIS PROMPT
3. THE CONTENT IS {len(content_result)} CHARACTERS LONG AND IS COMPLETE
4. ANALYZE THE CONTENT PROVIDED ABOVE - NOT SOME OTHER CONTENT

MANDATORY TASK: Perform SEO optimization analysis on the article content provided above.

ANALYSIS REQUIREMENTS:
- Complete technical SEO audit of THE CONTENT PROVIDED ABOVE
- Schema markup recommendations with code
- Meta tag optimization (multiple variations) 
- Featured snippet optimization
- Voice search optimization
- ALL recommendations must be based on THE ARTICLE CONTENT SHOWN ABOVE

*** DO NOT ASK FOR CONTENT - THE COMPLETE ARTICLE IS PROVIDED ABOVE ***
*** THE CONTENT IS BETWEEN THE "START OF ARTICLE CONTENT" AND "END OF ARTICLE CONTENT" LINES ***
*** WORK WITH THE CONTENT PROVIDED - DO NOT REQUEST ADDITIONAL CONTENT ***

BEGIN YOUR SEO ANALYSIS OF THE ARTICLE CONTENT PROVIDED ABOVE NOW."""

        # Debug SEO prompt
        print(f"SEO prompt length: {len(seo_prompt)} characters")
        print(f"Content properly embedded in SEO prompt: {len(content_result) > 100 and content_result[:50] in seo_prompt}")
        print(f"Forceful instructions count: {seo_prompt.count('DO NOT ASK')} 'DO NOT ASK' warnings")
        print(f"Content boundaries clearly marked: {'START OF ARTICLE CONTENT' in seo_prompt}")
        print(f"SEO prompt preview (first 300 chars):")
        print(seo_prompt[:300] + "...")
        
        seo_result = self.run_agent('seo_optimizer', seo_prompt)
        self.workflow_data['seo'] = seo_result
        
        print("SEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:400] + "..." if len(seo_result) > 400 else seo_result)
        
        approval = input("\n✅ Approve SEO optimization and continue? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at SEO stage")
            return self.workflow_data
        
        # Stage 4: Publication Package (automatic handoff)
        print("\n📦 Stage 4: Creating publication package...")
        publish_prompt = f"""Create a complete WordPress publication package:

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
- Internal linking implementation"""

        publish_result = self.run_agent('publishing_coordinator', publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("Pipeline finished successfully!")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results"""
        timestamp = int(time.time())
        output_dir = Path(f"automated_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir

def main():
    orchestrator = SimplePipelineOrchestrator()
    
    print("🚀 AI Content Pipeline - Automated Agent Communication")
    print("=" * 60)
    
    topic = input("Enter your content topic: ")
    include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
    
    print(f"\n🎬 Starting automated pipeline...")
    print("Note: You'll have approval checkpoints between each stage")
    
    # Run the automated pipeline
    results = orchestrator.run_pipeline(topic, include_images)
    
    # Save results
    output_dir = orchestrator.save_results(topic)
    
    print(f"\n✨ Pipeline completed! Check {output_dir} for all outputs.")

if __name__ == "__main__":
    main()

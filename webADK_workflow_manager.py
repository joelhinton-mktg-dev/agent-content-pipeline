#!/usr/bin/env python3
"""
Automated WebADK Pipeline
Fully automated 4-agent content pipeline using ADK CLI
"""

import asyncio
import json
import time
import sys
import subprocess
import tempfile
from pathlib import Path

class AutomatedWebADKPipeline:
    def __init__(self):
        self.workflow_data = {}
        self.agent_names = {
            1: 'outline_generator',
            2: 'research_content_creator',
            3: 'seo_optimizer',
            4: 'publishing_coordinator'
        }
        # Hardcoded configuration values
        self.config = {
            'include_images': True,
            'platform': 'WordPress',
            'auto_continue': True,
            'target_word_count': '2500-3500'
        }
        
    def generate_automated_prompt(self, stage, topic, context=None):
        """Generate automated prompts with hardcoded answers"""
        
        prompts = {
            1: f"""Create a comprehensive, detailed SEO-optimized outline for "{topic}".

REQUIREMENTS:
- Target word count: {self.config['target_word_count']} words
- Include primary and secondary keywords
- Detailed section breakdowns with word counts  
- Specific image placement recommendations with descriptions
- FAQ section for featured snippets
- Competitor analysis insights
- Internal linking opportunities

Would you like me to include specific image placement recommendations and placeholder text in this outline? YES - Include detailed image recommendations.

Make this outline extremely detailed and actionable for content creation.""",

            2: f"""Using this detailed outline, write comprehensive, well-researched content:

OUTLINE:
{context}

REQUIREMENTS:
- Write full sections with proper depth and detail
- Include current statistics and data
- Add specific examples and case studies
- Should I include image placeholders and visual content suggestions in the final content? YES - Include image placeholders.
- Use proper heading structure (H1, H2, H3)
- Include internal linking suggestions
- Write compelling introductions and conclusions

Provide complete, publication-ready content sections.""",

            3: f"""Optimize this content for SEO/AEO/GEO with target keyword "{topic}":

CONTENT:
{context}

What is the primary target keyword and should I focus on any specific SERP features? 
Primary keyword: "{topic}" - Focus on featured snippets and People Also Ask sections.

ANALYSIS REQUIREMENTS:
- Complete technical SEO audit
- Schema markup recommendations with code
- Meta tag optimization (multiple variations)
- Featured snippet optimization
- Voice search optimization""",

            4: f"""Create a complete WordPress publication package:

CONTENT:
{context.get('content', '') if isinstance(context, dict) else context or ''}

SEO RECOMMENDATIONS:  
{context.get('seo', '') if isinstance(context, dict) else ''}

What publishing platform are you using and should I create the complete publication package?
Platform: {self.config['platform']} with Yoast SEO - YES, create complete publication package.

Provide comprehensive, ready-to-publish package."""
        }
        
        return prompts.get(stage, f"Process: {topic}")
    
    async def run_agent_async(self, agent_name, prompt):
        """Run ADK agent via CLI with automated input"""
        try:
            # Create temporary file for prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                temp_file = f.name
            
            # Run agent with timeout
            cmd = f"cat {temp_file} | timeout 300 adk run {agent_name}"
            result = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
            if result.returncode == 0:
                return self.clean_agent_output(stdout.decode('utf-8'))
            else:
                raise Exception(f"Agent {agent_name} failed: {stderr.decode('utf-8')}")
                
        except Exception as e:
            raise Exception(f"Error running {agent_name}: {e}")
    
    def clean_agent_output(self, raw_output):
        """Clean ADK CLI output to extract agent response"""
        lines = raw_output.split('\n')
        cleaned_lines = []
        
        skip_patterns = [
            'Log setup complete',
            'To access latest log',
            'Running agent',
            'type exit to exit',
            '[user]:',
            'outline_generator',
            'research_content_creator',
            'seo_optimizer',
            'publishing_coordinator',
        ]
        
        capturing = False
        for line in lines:
            # Start capturing after we see agent output indicators
            if any(agent in line for agent in self.agent_names.values()):
                capturing = True
                continue
            
            if capturing and not any(skip in line for skip in skip_patterns):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # If result is too short, return more of the raw output
        if len(result) < 100:
            return raw_output.strip()
            
        return result
    
    def save_stage_output(self, stage, content, topic):
        """Save output from agent execution"""
        stage_names = {1: 'outline', 2: 'content', 3: 'seo', 4: 'publish'}
        
        timestamp = int(time.time())
        safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
        output_dir = Path(f"automated_webADK_{safe_topic}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / f"{stage_names[stage]}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(content))
        
        self.workflow_data[stage_names[stage]] = str(content)
        print(f"✅ Stage {stage} ({stage_names[stage]}) completed and saved to: {file_path}")
        
        return output_dir
    
    async def run_automated_pipeline(self, topic):
        """Execute the complete pipeline automatically with direct agent invocation"""
        
        print(f"🚀 Starting Automated WebADK Pipeline for: {topic}")
        print("=" * 60)
        print(f"Configuration: Images={self.config['include_images']}, Platform={self.config['platform']}")
        print("=" * 60)
        
        output_dir = None
        
        try:
            # Stage 1: Outline Generation
            print("\n🔍 Stage 1: Generating comprehensive outline...")
            outline_prompt = self.generate_automated_prompt(1, topic)
            
            print("Invoking outline_generator agent...")
            outline_result = await self.run_agent_async(self.agent_names[1], outline_prompt)
            output_dir = self.save_stage_output(1, outline_result, topic)
            
            print(f"Preview: {str(outline_result)[:200]}...")
            
            # Stage 2: Content Creation
            print("\n✍️ Stage 2: Creating detailed content...")
            content_prompt = self.generate_automated_prompt(2, topic, self.workflow_data.get('outline', ''))
            
            print("Invoking research_content_creator agent...")
            content_result = await self.run_agent_async(self.agent_names[2], content_prompt)
            output_dir = self.save_stage_output(2, content_result, topic)
            
            print(f"Preview: {str(content_result)[:200]}...")
            
            # Stage 3: SEO Optimization
            print("\n🎯 Stage 3: SEO/AEO/GEO optimization...")
            seo_prompt = self.generate_automated_prompt(3, topic, self.workflow_data.get('content', ''))
            
            print("Invoking seo_optimizer agent...")
            seo_result = await self.run_agent_async(self.agent_names[3], seo_prompt)
            output_dir = self.save_stage_output(3, seo_result, topic)
            
            print(f"Preview: {str(seo_result)[:200]}...")
            
            # Stage 4: Publication Package
            print("\n📦 Stage 4: Creating publication package...")
            publish_prompt = self.generate_automated_prompt(4, topic, {
                'content': self.workflow_data.get('content', ''),
                'seo': self.workflow_data.get('seo', '')
            })
            
            print("Invoking publishing_coordinator agent...")
            publish_result = await self.run_agent_async(self.agent_names[4], publish_prompt)
            output_dir = self.save_stage_output(4, publish_result, topic)
            
            print(f"Preview: {str(publish_result)[:200]}...")
            
            print("\n🎉 Automated WebADK Pipeline Completed Successfully!")
            print(f"📁 All outputs saved to: {output_dir}")
            
            return {
                'success': True,
                'output_directory': str(output_dir),
                'results': self.workflow_data
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed at current stage: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'output_directory': str(output_dir) if output_dir else None,
                'partial_results': self.workflow_data
            }

async def main():
    """Main function for automated pipeline execution"""
    pipeline = AutomatedWebADKPipeline()
    
    print("🚀 Automated WebADK Content Pipeline")
    print("=" * 50)
    print("Fully automated - no manual intervention required!")
    print("Configuration: Images=Yes, Platform=WordPress, Auto-continue=Yes")
    print("=" * 50)
    
    # For automated execution, we can hardcode a topic or take it as command line arg
    if len(sys.argv) > 1:
        topic = ' '.join(sys.argv[1:])
    else:
        topic = "best email marketing software for small business"  # Default topic for testing
        print(f"Using default topic: {topic}")
        print("(To specify topic: python webADK_workflow_manager.py 'your topic here')")
    
    # Run the automated pipeline
    result = await pipeline.run_automated_pipeline(topic)
    
    if result['success']:
        print("\n✅ Pipeline execution completed successfully!")
        print(f"📂 Results directory: {result['output_directory']}")
    else:
        print(f"\n❌ Pipeline failed: {result['error']}")
        if result.get('output_directory'):
            print(f"📂 Partial results saved to: {result['output_directory']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())

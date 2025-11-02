#!/usr/bin/env python3
"""
SDK-Based Pipeline Orchestrator using CLI Subprocess Pattern
Uses Python ADK SDK with isolated processes and explicit data passing
"""

import asyncio
import multiprocessing
import time
import os
import tempfile
import uuid
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import json
import sys
from dotenv import load_dotenv

# Load environment variables from agent .env files
project_root = Path(__file__).parent
for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator']:
    env_file = project_root / agent_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded .env from {agent_dir}")

# ADK imports for type hints and basic usage
try:
    from google.genai import types
except ImportError:
    # Will be imported within processes where needed
    types = None

def run_agent_in_process(agent_name, prompt, temp_dir):
    """
    Run agent in isolated process using Python SDK
    This function runs in a separate process to avoid state contamination
    """
    try:
        # Load environment variables within the process
        from pathlib import Path
        from dotenv import load_dotenv
        
        project_root = Path('/home/joel/ai-content-pipeline')
        for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator']:
            env_file = project_root / agent_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file)
        
        # Import ADK components within the process
        sys.path.append('/home/joel/ai-content-pipeline')
        
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        
        # Import specific agent
        if agent_name == 'outline_generator':
            from outline_generator.agent import root_agent as agent
        elif agent_name == 'research_content_creator':
            from research_content_creator.agent import root_agent as agent
        elif agent_name == 'seo_optimizer':
            from seo_optimizer.agent import root_agent as agent
        elif agent_name == 'publishing_coordinator':
            from publishing_coordinator.agent import root_agent as agent
        else:
            return {"error": f"Unknown agent: {agent_name}"}
        
        # Create fresh session service
        session_service = InMemorySessionService()
        
        # Create runner
        runner = Runner(
            app_name="ai-content-pipeline",
            agent=agent,
            session_service=session_service
        )
        
        # Create session with initial state
        user_id = f"user_{agent_name}"
        session_id = f"session_{int(time.time())}"
        
        # Run sync version using asyncio.run to avoid nesting
        return asyncio.run(_run_agent_async(
            runner, user_id, session_id, prompt, session_service
        ))
        
    except Exception as e:
        import traceback
        return {
            "error": f"Process execution failed: {e}",
            "traceback": traceback.format_exc()
        }

async def _run_agent_async(runner, user_id, session_id, prompt, session_service):
    """Async agent execution within process"""
    try:
        # Create session
        session = await session_service.create_session(
            app_name="ai-content-pipeline",
            user_id=user_id,
            session_id=session_id,
            state={}
        )
        
        # Create message
        message = types.Content(parts=[types.Part(text=prompt)])
        
        # Collect response
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            # Extract content from events
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text
        
        return {
            "success": True,
            "response": response_text,
            "length": len(response_text)
        }
        
    except Exception as e:
        import traceback
        return {
            "error": f"Async execution failed: {e}",
            "traceback": traceback.format_exc()
        }

class SDKPipelineOrchestrator:
    """SDK-based orchestrator using isolated process pattern"""
    
    def __init__(self):
        self.workflow_data = {}
        self.temp_dir = tempfile.mkdtemp(prefix="sdk_pipeline_")
        
    def clean_agent_output(self, raw_response):
        """Clean agent response similar to CLI pattern"""
        if not raw_response or len(raw_response.strip()) == 0:
            return "No output received from agent"
        
        # For SDK responses, we expect cleaner output
        # but still apply basic filtering
        lines = raw_response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines at start/end
            if line.strip():
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        return result if result else raw_response.strip()
    
    async def run_agent_isolated(self, agent_name, prompt):
        """Run agent in isolated process with timeout"""
        try:
            print(f"🤖 Running {agent_name} in isolated process...")
            print(f"   Prompt length: {len(prompt)} characters")
            
            # Use ProcessPoolExecutor for true isolation
            with ProcessPoolExecutor(max_workers=1) as executor:
                # Submit task to process pool
                future = executor.submit(
                    run_agent_in_process, 
                    agent_name, 
                    prompt, 
                    self.temp_dir
                )
                
                # Wait with timeout
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: future.result(timeout=300)  # 5 minute timeout
                    )
                except Exception as e:
                    print(f"   ❌ Process timeout or error: {e}")
                    return f"Process timeout or error: {e}"
            
            print(f"   Process result type: {type(result)}")
            
            # Handle result
            if isinstance(result, dict):
                if "error" in result:
                    print(f"   ❌ Agent error: {result['error']}")
                    if "traceback" in result:
                        print(f"   Traceback: {result['traceback']}")
                    return f"Agent error: {result['error']}"
                elif "success" in result and result["success"]:
                    response = result["response"]
                    print(f"   ✅ Success - Response length: {len(response)} chars")
                    return self.clean_agent_output(response)
                else:
                    print(f"   ❌ Unexpected result format: {result}")
                    return f"Unexpected result format: {result}"
            else:
                print(f"   ❌ Invalid result type: {type(result)}")
                return f"Invalid result type: {type(result)}"
            
        except Exception as e:
            print(f"   ❌ Exception in run_agent_isolated: {e}")
            import traceback
            traceback.print_exc()
            return f"Exception in agent execution: {e}"
    
    async def run_pipeline(self, topic, include_images=True):
        """Execute the complete SDK-based pipeline with isolation"""
        
        print(f"Starting SDK-Based Content Pipeline for: {topic}")
        print("Using Isolated Process Pattern with Python SDK")
        print("=" * 60)
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        
        outline_prompt = f"""Create a comprehensive SEO-optimized outline for the topic: "{topic}"

TASK: Generate a detailed content outline for a high-quality, SEO-optimized article.

REQUIREMENTS:
- Target word count: 2500-3500 words total
- Include primary and secondary keywords related to "{topic}"
- Detailed section breakdowns with suggested word counts for each section
- Specific image placement recommendations with descriptions
- FAQ section optimized for featured snippets and People Also Ask
- Competitor analysis insights and content gaps to address

OUTLINE STRUCTURE:
1. Introduction (300-400 words)
   - Hook with compelling statistic or question
   - Problem statement related to {topic}
   - Solution preview and article value proposition
   - [IMAGE: Hero image suggestion]

2. Main Content Sections (1800-2400 words total)
   - Break into 3-4 major sections with H2 headings
   - Include subsections with H3 headings
   - Provide specific talking points for each section
   - [IMAGE/SCREENSHOT suggestions for each major section]

3. Advanced Strategies/Best Practices (400-600 words)
   - Expert-level insights
   - Implementation tips
   - Common mistakes to avoid

4. Conclusion and Next Steps (200-300 words)
   - Key takeaways summary
   - Clear call-to-action
   - Next steps for readers

5. FAQ Section (300-400 words)
   - 5-7 questions optimized for voice search
   - People Also Ask query opportunities
   - Featured snippet optimization

OUTPUT REQUIREMENTS:
- Provide the complete outline with word count targets
- Include primary keyword: "{topic}"
- Suggest 5-8 related LSI keywords
- Include specific image recommendations
- Make it actionable for content creation

Create this outline now:"""

        outline_result = await self.run_agent_isolated('outline_generator', outline_prompt)
        self.workflow_data['outline'] = outline_result
        
        print("\nOUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:500] + "..." if len(outline_result) > 500 else outline_result)
        
        # Debug Stage 1 output
        print(f"\n🔍 DEBUG Stage 1 Output:")
        print(f"Outline result length: {len(outline_result)} characters")
        print(f"Contains outline markers: {'#' in outline_result or 'outline' in outline_result.lower()}")
        print(f"Contains errors: {'error' in outline_result.lower() or 'timeout' in outline_result.lower()}")
        
        if 'error' in outline_result.lower() or 'timeout' in outline_result.lower():
            print("❌ Stage 1 failed, stopping pipeline")
            return self.workflow_data
        
        approval = input("\n✅ Approve outline and continue to content creation? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at outline stage")
            return self.workflow_data
        
        # Stage 2: Content Creation
        print("\n✍️ Stage 2: Creating comprehensive content...")
        
        content_prompt = f"""TASK: Write a complete, comprehensive article based on the detailed outline provided below.

OUTLINE TO FOLLOW:
{outline_result}

CONTENT CREATION INSTRUCTIONS:
1. Write full, detailed sections for each heading in the outline above
2. Follow the word count targets specified in the outline
3. Include current statistics, data, and expert insights for each section
4. Add specific examples, case studies, and real-world applications
5. Insert image placeholders exactly as suggested in the outline: [IMAGE: description]
6. Use proper heading structure (H1 for main title, H2 for major sections, H3 for subsections)
7. Include internal linking suggestions where relevant
8. Write engaging, scannable content optimized for both readers and search engines
9. Ensure content flows naturally from one section to the next
10. Include the FAQ section with detailed answers

CONTENT QUALITY REQUIREMENTS:
- Original, plagiarism-free content
- Authoritative tone with expert-level insights
- Clear, actionable information that provides genuine value
- Mobile-optimized structure with short paragraphs
- Include relevant statistics and data points
- Optimize for featured snippets and voice search
- Write for the target keyword: "{topic}"

CRITICAL: Write the complete article content now. Do not ask questions or request additional information. Provide the full, publication-ready article based on the outline above.

Article content:"""

        content_result = await self.run_agent_isolated('research_content_creator', content_prompt)
        self.workflow_data['content'] = content_result
        
        print("\nCONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:500] + "..." if len(content_result) > 500 else content_result)
        
        # Debug Stage 2 output
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Contains headers: {'#' in content_result or 'introduction' in content_result.lower()}")
        print(f"Contains questions: {any(phrase in content_result.lower() for phrase in ['would you like', 'should i', 'please provide', 'let me know'])}")
        print(f"Contains errors: {'error' in content_result.lower() or 'timeout' in content_result.lower()}")
        print(f"Looks like complete content: {len(content_result) > 1000 and 'introduction' in content_result.lower()}")
        
        if 'error' in content_result.lower() or 'timeout' in content_result.lower():
            print("❌ Stage 2 failed, stopping pipeline")
            return self.workflow_data
        
        approval = input("\n✅ Approve content and continue to SEO optimization? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at content stage")
            return self.workflow_data
        
        # Stage 3: SEO Optimization  
        print("\n🎯 Stage 3: SEO optimization analysis...")
        
        print(f"\n🔍 DEBUG Stage 2→3 Handoff:")
        print(f"About to pass content ({len(content_result)} chars) to SEO optimizer")
        print(f"Content starts with: {content_result[:100]}...")
        
        seo_prompt = f"""TASK: Perform comprehensive SEO optimization analysis on the complete article content provided below.

TARGET KEYWORD: "{topic}"

ARTICLE CONTENT TO ANALYZE:
{content_result}

SEO ANALYSIS REQUIREMENTS:
1. TECHNICAL SEO AUDIT:
   - Analyze content structure and heading hierarchy
   - Review keyword density and distribution
   - Check for semantic keyword usage
   - Evaluate content length and readability

2. META OPTIMIZATION:
   - Create 3-5 optimized title tag variations (under 60 characters)
   - Write 2-3 meta description variations (150-160 characters)
   - Suggest Open Graph tags for social sharing

3. SCHEMA MARKUP:
   - Recommend appropriate structured data types
   - Provide JSON-LD schema markup code
   - Include Article, FAQ, or HowTo schema as relevant

4. ON-PAGE SEO:
   - Header tag optimization recommendations
   - Internal linking strategy suggestions
   - Image alt text recommendations
   - URL slug suggestion

5. FEATURED SNIPPET OPTIMIZATION:
   - Identify content sections optimized for featured snippets
   - Suggest improvements for People Also Ask targeting
   - Voice search optimization recommendations

6. CONTENT ENHANCEMENT:
   - Suggest additional LSI keywords to incorporate
   - Recommend content gaps to fill
   - Propose calls-to-action optimization

CRITICAL: Base ALL recommendations on the specific article content provided above. Analyze the actual content, not hypothetical scenarios.

SEO optimization report:"""

        seo_result = await self.run_agent_isolated('seo_optimizer', seo_prompt)
        self.workflow_data['seo'] = seo_result
        
        print("\nSEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:500] + "..." if len(seo_result) > 500 else seo_result)
        
        # Debug Stage 3 output
        print(f"\n🔍 DEBUG Stage 3 Output:")
        print(f"SEO result length: {len(seo_result)} characters")
        print(f"Contains SEO elements: {any(term in seo_result.lower() for term in ['meta', 'title', 'schema', 'keywords', 'optimization'])}")
        print(f"References the content: {topic.lower() in seo_result.lower()}")
        print(f"Contains errors: {'error' in seo_result.lower() or 'timeout' in seo_result.lower()}")
        
        if 'error' in seo_result.lower() or 'timeout' in seo_result.lower():
            print("❌ Stage 3 failed, stopping pipeline")
            return self.workflow_data
        
        approval = input("\n✅ Approve SEO optimization and continue to publication package? (y/n): ").lower()
        if approval != 'y':
            print("Pipeline stopped at SEO stage")
            return self.workflow_data
        
        # Stage 4: Publication Package
        print("\n📦 Stage 4: Creating publication package...")
        
        publish_prompt = f"""TASK: Create a complete WordPress publication package using the content and SEO recommendations provided below.

ARTICLE CONTENT:
{content_result}

SEO RECOMMENDATIONS:
{seo_result}

PUBLICATION REQUIREMENTS:
1. WORDPRESS FORMATTING:
   - Convert content to WordPress-compatible HTML blocks
   - Proper Gutenberg block structure
   - Include Yoast SEO settings
   - Mobile-responsive formatting

2. META IMPLEMENTATION:
   - Implement recommended title tags
   - Apply optimized meta descriptions
   - Include Open Graph tags
   - Add Twitter Card meta tags

3. SCHEMA MARKUP IMPLEMENTATION:
   - Include complete JSON-LD structured data
   - Implement recommended schema types
   - Ensure proper schema validation

4. IMAGE OPTIMIZATION:
   - Create image optimization checklist
   - Provide alt text for all image placeholders
   - Include image file naming conventions
   - Suggest image dimensions and formats

5. TECHNICAL IMPLEMENTATION:
   - Internal linking implementation plan
   - Core Web Vitals optimization checklist
   - Mobile-first indexing compliance
   - Page speed optimization recommendations

6. PUBLICATION CHECKLIST:
   - Pre-publication quality assurance checklist
   - SEO verification steps
   - Content review checklist
   - Launch preparation steps

CRITICAL: Create a complete, ready-to-publish package that implements all SEO recommendations from the analysis above.

Publication package:"""

        publish_result = await self.run_agent_isolated('publishing_coordinator', publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("SDK-based pipeline finished successfully!")
        
        # Final data flow verification
        print(f"\n🔍 FINAL PIPELINE DATA FLOW VERIFICATION:")
        print(f"Stage 1 (Outline): {len(self.workflow_data['outline'])} characters")
        print(f"Stage 2 (Content): {len(self.workflow_data['content'])} characters") 
        print(f"Stage 3 (SEO): {len(self.workflow_data['seo'])} characters")
        print(f"Stage 4 (Publish): {len(self.workflow_data['publish'])} characters")
        print(f"Total pipeline data: {sum(len(v) for v in self.workflow_data.values())} characters")
        
        return self.workflow_data
    
    def save_results(self, topic):
        """Save all pipeline results to output directory"""
        timestamp = int(time.time())
        output_dir = Path(f"sdk_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir
    
    def cleanup(self):
        """Clean up temporary resources"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")

async def main():
    orchestrator = SDKPipelineOrchestrator()
    
    try:
        print("🚀 SDK-Based AI Content Pipeline - Isolated Process Pattern")
        print("=" * 60)
        
        topic = input("Enter your content topic: ")
        include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
        
        print(f"\n🎬 Starting SDK-based pipeline using isolated processes...")
        print("Note: Each agent runs in separate process with 300s timeout")
        
        # Run the SDK-based pipeline
        results = await orchestrator.run_pipeline(topic, include_images)
        
        # Save results
        output_dir = orchestrator.save_results(topic)
        
        print(f"\n✨ SDK-based pipeline completed! Check {output_dir} for all outputs.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up
        orchestrator.cleanup()

if __name__ == "__main__":
    # Set multiprocessing start method for compatibility
    multiprocessing.set_start_method('spawn', force=True)
    asyncio.run(main())
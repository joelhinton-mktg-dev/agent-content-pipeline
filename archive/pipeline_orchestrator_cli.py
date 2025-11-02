#!/usr/bin/env python3
"""
CLI-Based ADK Multi-Agent Pipeline using WebADK Proven Pattern
Uses subprocess execution with explicit prompt-based data passing
"""

import asyncio
import time
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from agent .env files
project_root = Path(__file__).parent
for agent_dir in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator']:
    env_file = project_root / agent_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded .env from {agent_dir}")

class CLIPipelineOrchestrator:
    """CLI-based orchestrator using proven webADK subprocess pattern"""
    
    def __init__(self):
        self.workflow_data = {}
        self.temp_files = []  # Track temp files for cleanup
        
    def clean_adk_output(self, raw_output):
        """Clean ADK CLI output to extract only agent responses"""
        if not raw_output or len(raw_output.strip()) == 0:
            return "No output received from agent"
        
        lines = raw_output.split('\n')
        cleaned_lines = []
        
        # Patterns to skip (ADK system messages)
        skip_patterns = [
            'Log setup complete',
            'To access latest log',
            'Running agent',
            'type exit to exit',
            '[user]:',
            'UserWarning:',
            'outline_generator',
            'research_content_creator',
            'seo_optimizer',
            'publishing_coordinator',
            'WARNING:',
            'INFO:',
            'DEBUG:',
            'Starting agent',
            'Agent started',
            'Session created',
            'Entering interactive mode'
        ]
        
        # Look for actual agent output
        agent_output_started = False
        in_agent_response = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Skip obvious system messages
            if any(skip in line for skip in skip_patterns):
                continue
                
            # Start capturing after we see meaningful content
            if any(word in line_lower for word in [
                '# ', 'title:', 'outline:', 'content:', 'seo:', 'analysis:', 
                'recommendations:', '## ', '### ', '1.', '2.', '3.',
                'introduction', 'conclusion', 'summary', 'overview',
                'meta', 'schema', 'keywords', 'optimization'
            ]):
                agent_output_started = True
                in_agent_response = True
            
            # Include lines once agent output has started
            if agent_output_started and line.strip():
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # If we didn't capture much, try a more lenient approach
        if len(result) < 100:
            # Filter out only the most obvious system messages
            basic_skip = [
                'Log setup complete', 
                'To access latest log', 
                'type exit to exit',
                'UserWarning:',
                'WARNING:',
                'Starting agent'
            ]
            basic_cleaned = []
            for line in lines:
                if not any(skip in line for skip in basic_skip) and line.strip():
                    basic_cleaned.append(line)
            result = '\n'.join(basic_cleaned).strip()
        
        # Final fallback - return raw output if nothing worked
        return result if result else raw_output.strip()
    
    async def run_agent_via_cli(self, agent_name, prompt):
        """Run ADK agent via CLI subprocess using webADK proven pattern"""
        try:
            # Create temporary file for prompt
            timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
            temp_file = f"/tmp/prompt_{agent_name}_{timestamp}.txt"
            
            print(f"🤖 Running {agent_name} via CLI...")
            print(f"   Temp file: {temp_file}")
            print(f"   Prompt length: {len(prompt)} characters")
            
            # Write prompt to temp file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            self.temp_files.append(temp_file)  # Track for cleanup
            
            # Execute ADK agent with timeout using webADK pattern
            cmd = f"cat {temp_file} | timeout 300 adk run {agent_name}"
            
            print(f"   Executing: {cmd}")
            
            # Create subprocess
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=320)
                stdout_text = stdout.decode('utf-8') if stdout else ""
                stderr_text = stderr.decode('utf-8') if stderr else ""
                
                print(f"   Process completed with return code: {proc.returncode}")
                print(f"   Stdout length: {len(stdout_text)} chars")
                print(f"   Stderr length: {len(stderr_text)} chars")
                
                if stderr_text:
                    print(f"   Stderr preview: {stderr_text[:200]}...")
                
            except asyncio.TimeoutError:
                print(f"   ❌ Timeout after 320 seconds, killing process")
                proc.kill()
                await proc.wait()
                return f"Timeout error: {agent_name} execution exceeded 320 seconds"
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
                self.temp_files.remove(temp_file)
            except FileNotFoundError:
                pass
            
            # Process output
            if proc.returncode == 124:  # timeout command return code
                return f"Timeout error: {agent_name} execution exceeded 300 seconds"
            elif proc.returncode != 0:
                error_msg = f"Process error (code {proc.returncode}): {stderr_text[:500]}"
                print(f"   ❌ {error_msg}")
                return error_msg
            
            # Clean and return output
            cleaned_output = self.clean_adk_output(stdout_text)
            print(f"   ✅ Cleaned output length: {len(cleaned_output)} chars")
            
            return cleaned_output
            
        except Exception as e:
            print(f"   ❌ Exception in run_agent_via_cli: {e}")
            return f"Exception error: {e}"
    
    async def run_pipeline(self, topic, include_images=True):
        """Execute the complete CLI-based pipeline using webADK pattern"""
        
        print(f"Starting CLI-Based Content Pipeline for: {topic}")
        print("Using WebADK Proven Subprocess Pattern")
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

        outline_result = await self.run_agent_via_cli('outline_generator', outline_prompt)
        self.workflow_data['outline'] = outline_result
        
        print("\nOUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:500] + "..." if len(outline_result) > 500 else outline_result)
        
        # Debug Stage 1 output
        print(f"\n🔍 DEBUG Stage 1 Output:")
        print(f"Outline result length: {len(outline_result)} characters")
        print(f"Contains outline markers: {'#' in outline_result or 'outline' in outline_result.lower()}")
        
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

        content_result = await self.run_agent_via_cli('research_content_creator', content_prompt)
        self.workflow_data['content'] = content_result
        
        print("\nCONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:500] + "..." if len(content_result) > 500 else content_result)
        
        # Debug Stage 2 output
        print(f"\n🔍 DEBUG Stage 2 Output:")
        print(f"Content result length: {len(content_result)} characters")
        print(f"Contains headers: {'#' in content_result or 'introduction' in content_result.lower()}")
        print(f"Contains questions: {any(phrase in content_result.lower() for phrase in ['would you like', 'should i', 'please provide', 'let me know'])}")
        print(f"Looks like complete content: {len(content_result) > 1000 and 'introduction' in content_result.lower()}")
        
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

        seo_result = await self.run_agent_via_cli('seo_optimizer', seo_prompt)
        self.workflow_data['seo'] = seo_result
        
        print("\nSEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:500] + "..." if len(seo_result) > 500 else seo_result)
        
        # Debug Stage 3 output
        print(f"\n🔍 DEBUG Stage 3 Output:")
        print(f"SEO result length: {len(seo_result)} characters")
        print(f"Contains SEO elements: {any(term in seo_result.lower() for term in ['meta', 'title', 'schema', 'keywords', 'optimization'])}")
        print(f"References the content: {topic.lower() in seo_result.lower()}")
        
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

        publish_result = await self.run_agent_via_cli('publishing_coordinator', publish_prompt)
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("CLI-based pipeline finished successfully!")
        
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
        output_dir = Path(f"cli_pipeline_{topic.replace(' ', '_')}_{timestamp}")
        output_dir.mkdir(exist_ok=True)
        
        for stage, content in self.workflow_data.items():
            file_path = output_dir / f"{stage}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n💾 All results saved to: {output_dir}")
        return output_dir
    
    def cleanup_temp_files(self):
        """Clean up any remaining temporary files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
                print(f"Cleaned up temp file: {temp_file}")
            except FileNotFoundError:
                pass
        self.temp_files.clear()

async def main():
    orchestrator = CLIPipelineOrchestrator()
    
    try:
        print("🚀 CLI-Based AI Content Pipeline - WebADK Proven Pattern")
        print("=" * 60)
        
        topic = input("Enter your content topic: ")
        include_images = input("Include image placeholders? (y/n): ").lower() == 'y'
        
        print(f"\n🎬 Starting CLI-based pipeline using subprocess pattern...")
        print("Note: Each agent runs via 'adk run' subprocess with 300s timeout")
        
        # Run the CLI-based pipeline
        results = await orchestrator.run_pipeline(topic, include_images)
        
        # Save results
        output_dir = orchestrator.save_results(topic)
        
        print(f"\n✨ CLI-based pipeline completed! Check {output_dir} for all outputs.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up temp files
        orchestrator.cleanup_temp_files()

if __name__ == "__main__":
    asyncio.run(main())
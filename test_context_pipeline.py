#!/usr/bin/env python3
"""
Test version of context-based pipeline with predefined inputs
"""

import asyncio
import time
from pathlib import Path
import sys
import os

# Add agent directories to path for imports
sys.path.append('/home/joel/ai-content-pipeline')

from outline_generator.agent import root_agent as outline_agent
from research_content_creator.agent import root_agent as content_agent  
from seo_optimizer.agent import root_agent as seo_agent
from publishing_coordinator.agent import root_agent as publish_agent

class ContextPipelineOrchestrator:
    """Context-based orchestrator that uses ADK context for data passing"""
    
    def __init__(self):
        self.workflow_data = {}
        self.agents = {
            'outline_generator': outline_agent,
            'research_content_creator': content_agent,
            'seo_optimizer': seo_agent,
            'publishing_coordinator': publish_agent
        }
        
    async def run_agent_with_context(self, agent_name, context_data):
        """Run agent with context data setup"""
        try:
            agent = self.agents[agent_name]
            
            # Initialize context if needed
            if not hasattr(agent, 'context'):
                # Create a simple context object
                class SimpleContext:
                    def __init__(self):
                        self.state = {}
                agent.context = SimpleContext()
            
            # Set context data
            for key, value in context_data.items():
                agent.context.state[key] = value
            
            # Set current stage
            agent.context.state["temp:pipeline_stage"] = agent_name
            
            print(f"🤖 Running {agent_name} with context data...")
            print(f"   Context keys: {list(agent.context.state.keys())}")
            
            # For testing, we'll simulate agent results
            # In reality, agents would access context.state to get data
            if agent_name == 'outline_generator':
                result = f"""# SEO-Optimized Outline for: {context_data.get('temp:pipeline_topic', 'Test Topic')}

## 1. Introduction (300 words)
- Hook: Statistical opening about the topic
- Problem statement
- Solution preview
[IMAGE: Hero image representing the main topic]

## 2. Main Content Section 1 (800 words)
- Key concept explanation
- Benefits and features
- Real-world examples
[IMAGE: Infographic showing key statistics]

## 3. Main Content Section 2 (600 words)
- Advanced strategies
- Best practices
- Common mistakes to avoid
[SCREENSHOT: Example interface or process]

## 4. Conclusion (200 words)
- Summary of key points
- Call to action
- Next steps

## FAQ Section
- Question 1: [Based on search data]
- Question 2: [People Also Ask optimization]
- Question 3: [Voice search optimization]

Target Word Count: 1900 words
Primary Keywords: [Derived from topic]
Secondary Keywords: [LSI and semantic keywords]"""
                
                # Store in context for next agent
                agent.context.state["temp:outline_result"] = result
                
            elif agent_name == 'research_content_creator':
                outline = context_data.get('temp:outline_result', 'No outline found')
                topic = context_data.get('temp:pipeline_topic', 'Unknown topic')
                
                result = f"""# {topic}: Complete Guide

## Introduction
This comprehensive guide covers everything you need to know about {topic}. Based on the latest research and industry best practices, we'll explore the key concepts, strategies, and implementation methods that can help you achieve success.

[IMAGE: Hero image for {topic}]

## Understanding the Fundamentals
{topic} has become increasingly important in today's digital landscape. According to recent studies, organizations that implement effective strategies see an average improvement of 40% in their key metrics.

Key benefits include:
- Enhanced performance and efficiency
- Better user experience
- Improved competitive positioning
- Measurable ROI and results

[INFOGRAPHIC: Statistics and key benefits]

## Advanced Strategies and Best Practices
When implementing {topic} strategies, it's essential to follow proven methodologies:

1. **Planning Phase**: Develop a comprehensive strategy based on your specific goals
2. **Implementation**: Execute your plan using industry-standard tools and techniques
3. **Optimization**: Continuously monitor and improve your approach
4. **Measurement**: Track key metrics to ensure success

[SCREENSHOT: Example implementation interface]

## Common Challenges and Solutions
While working with {topic}, you may encounter several challenges:

- **Challenge 1**: Resource allocation and prioritization
- **Solution**: Develop a phased approach with clear milestones

- **Challenge 2**: Technical implementation complexity
- **Solution**: Use proven frameworks and seek expert guidance

## Conclusion
{topic} represents a significant opportunity for growth and improvement. By following the strategies outlined in this guide, you can achieve measurable results and stay ahead of the competition.

Next steps:
1. Assess your current situation
2. Develop an implementation plan
3. Begin with small, manageable changes
4. Monitor progress and adjust as needed

Ready to get started? Contact our experts for personalized guidance."""
                
                # Store in context for next agent
                agent.context.state["temp:content_article"] = result
                
            elif agent_name == 'seo_optimizer':
                content = context_data.get('temp:content_article', 'No content found')
                topic = context_data.get('temp:pipeline_topic', 'Unknown topic')
                
                result = f"""# SEO Optimization Report for: {topic}

## Technical SEO Analysis
✅ Content structure: Well-organized with proper H1, H2, H3 hierarchy
✅ Word count: 1,200+ words (meets length requirements)
✅ Keyword density: Optimal distribution throughout content
✅ Image optimization: Alt text placeholders included

## Meta Tag Recommendations

### Title Tag Options:
1. "{topic}: Complete Guide [2024] | [Brand Name]"
2. "Ultimate {topic} Guide: Strategies & Best Practices"  
3. "Master {topic}: Expert Tips and Implementation Guide"

### Meta Descriptions:
1. "Comprehensive {topic} guide with proven strategies, best practices, and implementation tips. Get expert insights and measurable results."
2. "Learn {topic} from industry experts. Step-by-step guide with real examples, tools, and optimization strategies for success."

## Schema Markup Recommendations
```json
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{topic}: Complete Guide",
  "description": "Comprehensive guide covering {topic} strategies and best practices",
  "author": {{
    "@type": "Person",
    "name": "Expert Author"
  }},
  "datePublished": "2024-10-28",
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "https://example.com/{topic.lower().replace(' ', '-')}"
  }}
}}
```

## Featured Snippet Optimization
- Created FAQ section targeting People Also Ask queries
- Structured content for voice search optimization
- Added numbered lists and step-by-step processes

## Internal Linking Strategy
- Link to related topic pages
- Connect to resource and tool pages
- Create topic clusters for authority building

## Core Web Vitals Improvements
- Optimize images with proper sizing and lazy loading
- Minimize CSS and JavaScript blocking
- Implement proper caching strategies"""
                
                # Store in context for next agent
                agent.context.state["temp:seo_recommendations"] = result
                
            elif agent_name == 'publishing_coordinator':
                content = context_data.get('temp:content_article', 'No content found')
                seo_data = context_data.get('temp:seo_recommendations', 'No SEO data found')
                topic = context_data.get('temp:pipeline_topic', 'Unknown topic')
                
                result = f"""# WordPress Publication Package for: {topic}

## Publication-Ready Content
```html
<!-- Yoast SEO Settings -->
<title>{topic}: Complete Guide [2024] | Brand Name</title>
<meta name="description" content="Comprehensive {topic} guide with proven strategies, best practices, and implementation tips. Get expert insights and measurable results.">

<!-- Schema Markup -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{topic}: Complete Guide",
  "description": "Comprehensive guide covering {topic} strategies and best practices"
}}
</script>

<!-- Article Content -->
<h1>{topic}: Complete Guide</h1>

<div class="wp-block-group">
  <p>This comprehensive guide covers everything you need to know about {topic}...</p>
  <figure class="wp-block-image">
    <img src="hero-{topic.lower().replace(' ', '-')}.jpg" alt="Complete guide to {topic}" />
  </figure>
</div>
```

## Image Optimization Checklist
- [ ] Hero image: 1200x630px (Facebook/social sharing)
- [ ] Infographic: 800x1200px (Pinterest optimized)
- [ ] Screenshots: 1024x768px (retina ready)
- [ ] All images compressed and WebP format
- [ ] Alt text includes target keywords naturally

## Internal Linking Implementation
- Link to: "Advanced {topic} Strategies" (if exists)
- Link to: "{topic} Tools and Resources" (if exists)  
- Link to: "Getting Started with {topic}" (if exists)

## Publication Quality Checklist
✅ Content exceeds 1,200 words
✅ Meta title under 60 characters
✅ Meta description 150-160 characters
✅ Schema markup implemented
✅ Images optimized with alt text
✅ Internal links added (3-5 relevant links)
✅ FAQ section for featured snippets
✅ Mobile-responsive formatting
✅ Core Web Vitals optimized

## WordPress Block Structure
- Title block with H1
- Paragraph blocks for content
- Image blocks with proper alt text
- List blocks for enumerated items
- FAQ blocks for structured Q&A

**STATUS: READY FOR IMMEDIATE PUBLICATION**"""
                
                # Store in context  
                agent.context.state["temp:publication_package"] = result
            
            print(f"✅ {agent_name} completed successfully")
            return result
            
        except Exception as e:
            print(f"❌ Error in run_agent_with_context for {agent_name}: {e}")
            return f"Error running {agent_name}: {e}"
    
    async def run_pipeline_test(self, topic="AI Content Marketing", include_images=True):
        """Execute the complete context-based pipeline with test data"""
        
        print(f"Starting Context-Based Content Pipeline for: {topic}")
        print("=" * 60)
        
        # Initialize shared context data
        context_data = {
            "temp:pipeline_topic": topic,
            "temp:include_images": include_images
        }
        
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Generating outline...")
        outline_result = await self.run_agent_with_context('outline_generator', context_data)
        
        # Store outline in context for next stage
        context_data["temp:outline_result"] = outline_result
        self.workflow_data['outline'] = outline_result
        
        print("OUTLINE PREVIEW:")
        print("-" * 30)
        print(outline_result[:400] + "..." if len(outline_result) > 400 else outline_result)
        
        # Stage 2: Content Creation
        print("\n✍️ Stage 2: Creating content...")
        content_result = await self.run_agent_with_context('research_content_creator', context_data)
        
        # Store content in context for next stage
        context_data["temp:content_article"] = content_result
        self.workflow_data['content'] = content_result
        
        print("CONTENT PREVIEW:")
        print("-" * 30)
        print(content_result[:400] + "..." if len(content_result) > 400 else content_result)
        
        # Stage 3: SEO Optimization
        print("\n🎯 Stage 3: SEO optimization...")
        seo_result = await self.run_agent_with_context('seo_optimizer', context_data)
        
        # Store SEO recommendations in context for next stage
        context_data["temp:seo_recommendations"] = seo_result
        self.workflow_data['seo'] = seo_result
        
        print("SEO OPTIMIZATION PREVIEW:")
        print("-" * 30)
        print(seo_result[:400] + "..." if len(seo_result) > 400 else seo_result)
        
        # Stage 4: Publication Package
        print("\n📦 Stage 4: Creating publication package...")
        publish_result = await self.run_agent_with_context('publishing_coordinator', context_data)
        
        # Store final package
        context_data["temp:publication_package"] = publish_result
        self.workflow_data['publish'] = publish_result
        
        print("\n🎉 PUBLICATION PACKAGE COMPLETE!")
        print("Context-based pipeline finished successfully!")
        
        # Verification
        print("\n🔍 CONTEXT DATA VERIFICATION:")
        for key, value in context_data.items():
            print(f"   {key}: {len(str(value))} characters")
        
        return self.workflow_data

async def main():
    orchestrator = ContextPipelineOrchestrator()
    
    print("🚀 AI Content Pipeline - Context-Based Agent Communication TEST")
    print("=" * 60)
    
    # Run test with predefined topic
    results = await orchestrator.run_pipeline_test("AI Content Marketing", True)
    
    print(f"\n✨ Context-based pipeline test completed successfully!")
    print(f"Generated {len(results)} pipeline stages:")
    for stage, content in results.items():
        print(f"  - {stage}: {len(content)} characters")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test the corrected context-based pipeline implementation
"""

import asyncio
from pipeline_orchestrator_context import ContextPipelineOrchestrator

async def main():
    orchestrator = ContextPipelineOrchestrator()
    
    print("🚀 Testing Corrected Context-Based Pipeline")
    print("=" * 60)
    
    # Test with a simple topic
    topic = "AI Content Marketing Strategy"
    
    try:
        results = await orchestrator.run_pipeline_test(topic, True)
        print(f"\n✨ Test completed successfully!")
        print(f"Generated {len(results)} pipeline stages:")
        for stage, content in results.items():
            print(f"  - {stage}: {len(content)} characters")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

# Add a simplified test method to the orchestrator
async def run_pipeline_test(self, topic="AI Content Marketing", include_images=True):
    """Test the pipeline with minimal prompts to verify context passing"""
    
    print(f"Testing Context-Based Pipeline for: {topic}")
    print("=" * 60)
    
    # Initialize shared session state
    session_state = {
        "temp:pipeline_topic": topic,
        "temp:include_images": include_images
    }
    
    try:
        # Stage 1: Outline Generation
        print("\n🔍 Stage 1: Testing outline generation...")
        outline_prompt = f"Create an outline for {topic}. Store in context.state['temp:outline_result']."
        
        outline_result, session_state = await self.run_agent_with_runner(
            'outline_generator', outline_prompt, session_state
        )
        self.workflow_data['outline'] = outline_result
        
        print(f"   Outline result: {len(outline_result)} chars")
        print(f"   Session state keys: {list(session_state.keys())}")
        
        # Check if outline was stored in context
        outline_in_context = session_state.get("temp:outline_result", "")
        print(f"   Outline stored in context: {len(outline_in_context)} chars")
        
        return self.workflow_data
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

# Monkey patch the test method
ContextPipelineOrchestrator.run_pipeline_test = run_pipeline_test

if __name__ == "__main__":
    asyncio.run(main())
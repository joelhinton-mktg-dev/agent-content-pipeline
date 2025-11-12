#!/usr/bin/env python3
"""
Debug script to test the pipeline data flow and file saving
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_single_agent(agent_name, prompt):
    """Test a single agent and return its output"""
    try:
        from pipeline_single_session import SingleSessionPipelineOrchestrator
        
        orchestrator = SingleSessionPipelineOrchestrator()
        await orchestrator.initialize_session()
        
        logger.info(f"Testing {agent_name} with prompt: {prompt[:100]}...")
        result = await orchestrator.run_agent_in_session(agent_name, prompt)
        
        logger.info(f"{agent_name} result type: {type(result)}")
        logger.info(f"{agent_name} result length: {len(str(result))}")
        logger.info(f"{agent_name} result preview: {str(result)[:200]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing {agent_name}: {e}")
        return None

async def test_demo_orchestrator():
    """Test the demo orchestrator with detailed logging"""
    try:
        from pipeline_orchestrator import DemoPipelineOrchestrator
        
        orchestrator = DemoPipelineOrchestrator()
        await orchestrator.initialize()
        
        logger.info("Starting demo orchestrator test...")
        result = await orchestrator.process_content_request(
            "AI in healthcare", 
            "Healthcare professionals", 
            1000
        )
        
        # Analyze results
        logger.info("=== DEMO ORCHESTRATOR RESULTS ===")
        logger.info(f"Session ID: {result.get('session_id')}")
        logger.info(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        # Check stages
        stages = result.get('stages', {})
        logger.info(f"Stages captured: {list(stages.keys())}")
        
        for stage_name, content in stages.items():
            logger.info(f"\n--- {stage_name.upper()} ---")
            logger.info(f"Type: {type(content)}")
            logger.info(f"Length: {len(str(content))}")
            logger.info(f"Content preview: {str(content)[:300]}...")
            
            if isinstance(content, dict):
                logger.info(f"Dict keys: {list(content.keys())}")
            elif isinstance(content, str):
                logger.info(f"String content: {len(content.strip())} chars after strip")
            
        # Check downloads
        downloads = result.get('downloads', [])
        logger.info(f"\n=== DOWNLOADS ({len(downloads)} files) ===")
        for download in downloads:
            logger.info(f"File: {download['name']}, Size: {download['size']} bytes, URL: {download['url']}")
            
            # Check if file actually exists and has content
            file_path = Path(download['path'])
            if file_path.exists():
                actual_size = file_path.stat().st_size
                logger.info(f"  Actual file size: {actual_size} bytes")
                if actual_size > 0:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_preview = f.read(200)
                        logger.info(f"  Content preview: {content_preview}...")
                else:
                    logger.warning(f"  File is empty!")
            else:
                logger.error(f"  File does not exist!")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in demo orchestrator test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def debug_individual_agents():
    """Test each agent individually to see what they return"""
    logger.info("=== TESTING INDIVIDUAL AGENTS ===")
    
    test_cases = [
        ("outline_generator", "Create a brief outline for an article about AI in healthcare"),
        ("research_agent", "Research current trends in AI healthcare applications"),
        ("research_content_creator", "Write a 500-word article about AI in healthcare"),
        ("citation_agent", "Add citations to the healthcare AI article"),
        ("image_agent", "Generate images for AI healthcare article"),
        ("fact_check_agent", "Fact-check claims about AI in healthcare"),
        ("seo_optimizer", "Optimize AI healthcare article for SEO"),
        ("publishing_coordinator", "Prepare AI healthcare article for publication")
    ]
    
    results = {}
    for agent_name, prompt in test_cases:
        result = await test_single_agent(agent_name, prompt)
        results[agent_name] = result
    
    return results

async def main():
    """Main debug function"""
    print("🐛 Pipeline Debug & Data Flow Analysis")
    print("="*60)
    
    # Test 1: Individual agents
    print("\n1. Testing individual agents...")
    agent_results = await debug_individual_agents()
    
    # Test 2: Demo orchestrator
    print("\n2. Testing demo orchestrator (full pipeline)...")
    demo_result = await test_demo_orchestrator()
    
    # Analysis
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    if demo_result:
        stages = demo_result.get('stages', {})
        downloads = demo_result.get('downloads', [])
        
        print(f"✅ Pipeline executed successfully")
        print(f"📁 Stages captured: {len(stages)}/8")
        print(f"📄 Download files: {len(downloads)}")
        
        # Check for empty files
        empty_files = []
        for download in downloads:
            if download['size'] == 0:
                empty_files.append(download['name'])
        
        if empty_files:
            print(f"⚠️  Empty files detected: {empty_files}")
            print("🔍 This indicates the file saving logic needs investigation")
        else:
            print("✅ All files have content")
            
        # Check stage content types
        print(f"\n📋 Stage Content Analysis:")
        for stage_name, content in stages.items():
            content_type = type(content).__name__
            content_length = len(str(content))
            has_content = content is not None and str(content).strip() != '' and str(content) != 'None'
            status = "✅" if has_content else "❌"
            print(f"  {status} {stage_name:15} | {content_type:10} | {content_length:6} chars")
    
    else:
        print("❌ Pipeline test failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test the CLI-based pipeline orchestrator
"""

import asyncio
import sys
from pipeline_orchestrator_cli import CLIPipelineOrchestrator

async def test_single_agent():
    """Test single agent execution via CLI"""
    orchestrator = CLIPipelineOrchestrator()
    
    print("🧪 Testing single agent CLI execution...")
    
    test_prompt = """Create a brief outline for "AI Content Marketing" with:
- Introduction section
- 2-3 main content sections  
- Conclusion
- Keep it under 500 words total"""
    
    try:
        result = await orchestrator.run_agent_via_cli('outline_generator', test_prompt)
        
        print(f"✅ Test completed!")
        print(f"Result length: {len(result)} characters")
        print(f"Result preview:")
        print("-" * 40)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 40)
        
        # Check if result looks like outline content
        success_indicators = [
            len(result) > 50,
            any(word in result.lower() for word in ['outline', 'introduction', 'section', '#']),
            not any(phrase in result.lower() for phrase in ['error', 'timeout', 'failed'])
        ]
        
        if all(success_indicators):
            print("🎉 Single agent test PASSED!")
            return True
        else:
            print("❌ Single agent test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        orchestrator.cleanup_temp_files()

async def test_output_cleaning():
    """Test the output cleaning function"""
    orchestrator = CLIPipelineOrchestrator()
    
    print("\n🧪 Testing output cleaning function...")
    
    # Test with mock ADK output
    mock_adk_output = """Log setup complete. Learn more about ADK at https://google.github.io/adk-docs
To access latest log: tail -f /path/to/log
Running agent outline_generator
[user]: Create an outline
UserWarning: something
Starting agent...

# AI Content Marketing Outline

## Introduction
This is the actual outline content that we want to keep.

## Main Content
- Point 1
- Point 2

## Conclusion
Final thoughts here.

type exit to exit"""
    
    cleaned = orchestrator.clean_adk_output(mock_adk_output)
    
    print(f"Original length: {len(mock_adk_output)} characters")
    print(f"Cleaned length: {len(cleaned)} characters")
    print(f"Cleaned result:")
    print("-" * 40)
    print(cleaned)
    print("-" * 40)
    
    # Check cleaning effectiveness
    success_indicators = [
        'Log setup complete' not in cleaned,
        'UserWarning' not in cleaned,
        'type exit to exit' not in cleaned,
        '# AI Content Marketing Outline' in cleaned,
        'Introduction' in cleaned
    ]
    
    if all(success_indicators):
        print("🎉 Output cleaning test PASSED!")
        return True
    else:
        print("❌ Output cleaning test FAILED!")
        return False

async def test_pipeline_basic():
    """Test basic pipeline flow (without requiring API key)"""
    print("\n🧪 Testing basic pipeline structure...")
    
    # This test just verifies the pipeline structure without actual execution
    orchestrator = CLIPipelineOrchestrator()
    
    # Test that all required methods exist
    required_methods = [
        'run_agent_via_cli',
        'clean_adk_output', 
        'run_pipeline',
        'save_results',
        'cleanup_temp_files'
    ]
    
    all_methods_exist = all(hasattr(orchestrator, method) for method in required_methods)
    
    if all_methods_exist:
        print("🎉 Pipeline structure test PASSED!")
        return True
    else:
        print("❌ Pipeline structure test FAILED!")
        return False

async def main():
    print("🚀 CLI Pipeline Orchestrator Test Suite")
    print("=" * 50)
    
    # Check if adk command is available
    import subprocess
    try:
        result = subprocess.run(['which', 'adk'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Warning: 'adk' command not found in PATH")
            print("Some tests may fail without ADK CLI installed")
        else:
            print(f"✅ ADK CLI found at: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  Could not check for ADK CLI: {e}")
    
    # Run tests
    tests = [
        ("Output Cleaning", test_output_cleaning),
        ("Pipeline Structure", test_pipeline_basic),
    ]
    
    # Only run CLI test if we have ADK and API key
    if 'GOOGLE_API_KEY' in os.environ:
        tests.append(("Single Agent CLI", test_single_agent))
    else:
        print("⚠️  Skipping CLI execution test (no GOOGLE_API_KEY)")
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI orchestrator is ready.")
    else:
        print("⚠️  Some tests failed. Check implementation.")

if __name__ == "__main__":
    import os
    asyncio.run(main())
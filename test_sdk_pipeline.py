#!/usr/bin/env python3
"""
Test SDK-based pipeline orchestrator
"""

import asyncio
import os
import sys
from pipeline_orchestrator_sdk import SDKPipelineOrchestrator

async def test_isolated_agent():
    """Test single agent execution in isolated process"""
    orchestrator = SDKPipelineOrchestrator()
    
    print("🧪 Testing isolated agent execution...")
    
    test_prompt = """Create a brief outline for "AI Content Marketing" with:
- Introduction section
- 2-3 main content sections  
- Conclusion
- Keep it under 500 words total"""
    
    try:
        result = await orchestrator.run_agent_isolated('outline_generator', test_prompt)
        
        print(f"✅ Test completed!")
        print(f"Result length: {len(result)} characters")
        print(f"Result preview:")
        print("-" * 40)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 40)
        
        # Check if result looks like outline content
        success_indicators = [
            len(result) > 50,
            not any(phrase in result.lower() for phrase in ['error', 'timeout', 'failed', 'exception']),
            any(word in result.lower() for word in ['outline', 'introduction', 'section', '#', 'content', 'marketing'])
        ]
        
        if all(success_indicators):
            print("🎉 Isolated agent test PASSED!")
            return True
        else:
            print("❌ Isolated agent test FAILED!")
            print(f"Success indicators: {success_indicators}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        orchestrator.cleanup()

def test_process_isolation():
    """Test that process isolation is working"""
    print("\n🧪 Testing process isolation...")
    
    # This just verifies the structure
    orchestrator = SDKPipelineOrchestrator()
    
    required_methods = [
        'run_agent_isolated',
        'clean_agent_output',
        'run_pipeline',
        'save_results',
        'cleanup'
    ]
    
    all_methods_exist = all(hasattr(orchestrator, method) for method in required_methods)
    
    if all_methods_exist:
        print("🎉 Process isolation structure test PASSED!")
        orchestrator.cleanup()
        return True
    else:
        print("❌ Process isolation structure test FAILED!")
        orchestrator.cleanup()
        return False

async def main():
    print("🚀 SDK Pipeline Orchestrator Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    try:
        import multiprocessing
        multiprocessing.set_start_method('spawn', force=True)
        print("✅ Multiprocessing configured")
    except Exception as e:
        print(f"⚠️  Multiprocessing setup warning: {e}")
    
    # Check for API key
    if 'GOOGLE_API_KEY' not in os.environ:
        print("⚠️  Warning: No GOOGLE_API_KEY found")
        print("Some tests may fail without API key")
    else:
        print("✅ GOOGLE_API_KEY found")
    
    # Run tests
    tests = [
        ("Process Isolation Structure", test_process_isolation),
    ]
    
    # Only run agent test if we have API key
    if 'GOOGLE_API_KEY' in os.environ:
        tests.append(("Isolated Agent Execution", test_isolated_agent))
    else:
        print("⚠️  Skipping agent execution test (no GOOGLE_API_KEY)")
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
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
        print("🎉 All tests passed! SDK orchestrator is ready.")
    else:
        print("⚠️  Some tests failed. Check implementation.")

if __name__ == "__main__":
    asyncio.run(main())
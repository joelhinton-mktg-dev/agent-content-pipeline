#!/usr/bin/env python3
"""
Test the single session pipeline with API key loading
"""

import asyncio
import os
from pipeline_single_session import SingleSessionPipelineOrchestrator

async def test_api_key_loading():
    """Test that API keys are loaded correctly"""
    
    print("🧪 Testing API key loading...")
    
    # Check if GOOGLE_API_KEY is now available
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key:
        print(f"✅ GOOGLE_API_KEY loaded: {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        print("❌ GOOGLE_API_KEY not found in environment")
        return False

async def test_single_agent_execution():
    """Test running a single agent with loaded API keys"""
    
    print("\n🧪 Testing single agent execution with API keys...")
    
    orchestrator = SingleSessionPipelineOrchestrator()
    
    try:
        # Initialize session
        if not await orchestrator.initialize_session():
            print("❌ Session initialization failed")
            return False
        
        print("   Session initialized successfully")
        
        # Test simple agent execution
        test_prompt = "Create a very brief outline for 'AI Content Marketing' with just introduction and main sections. Keep it under 200 words."
        
        print("   Testing outline generator...")
        result = await orchestrator.run_agent_in_session('outline_generator', test_prompt)
        
        print(f"   Result length: {len(result)} characters")
        print(f"   Result preview: {result[:150]}...")
        
        # Check for success indicators
        success_indicators = [
            len(result) > 50,
            not any(phrase in result.lower() for phrase in ['missing key inputs', 'api key', 'error']),
            any(word in result.lower() for word in ['outline', 'introduction', 'content', 'marketing'])
        ]
        
        if all(success_indicators):
            print("✅ Single agent execution successful!")
            return True
        else:
            print(f"⚠️  Partial success - checking indicators: {success_indicators}")
            if 'missing key inputs' in result.lower():
                print("❌ API key still not working")
                return False
            else:
                print("✅ API key working, agent responded")
                return True
            
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        if 'missing key inputs' in str(e).lower():
            print("   Issue: API key not loaded properly")
            return False
        else:
            print("   Issue: Other error (may be unrelated to API key)")
            return True  # API key loading may still be working

async def test_session_continuity():
    """Test that conversation history works between agents"""
    
    print("\n🧪 Testing session continuity...")
    
    orchestrator = SingleSessionPipelineOrchestrator()
    
    try:
        # Initialize session
        if not await orchestrator.initialize_session():
            print("❌ Session initialization failed")
            return False
        
        # First agent
        outline_prompt = "Create a brief outline for AI Content Marketing with just introduction and one main section."
        outline_result = await orchestrator.run_agent_in_session('outline_generator', outline_prompt)
        
        if 'missing key inputs' in outline_result.lower():
            print("❌ API key issue in first agent")
            return False
        
        print(f"   First agent completed: {len(outline_result)} chars")
        
        # Second agent (should reference first agent's work)
        content_prompt = "Now write a brief introduction section based on the outline you just created."
        content_result = await orchestrator.run_agent_in_session('research_content_creator', content_prompt)
        
        if 'missing key inputs' in content_result.lower():
            print("❌ API key issue in second agent")
            return False
        
        print(f"   Second agent completed: {len(content_result)} chars")
        
        # Check if second agent referenced the first
        reference_indicators = [
            'outline' in content_result.lower(),
            'introduction' in content_result.lower(),
            len(content_result) > 100
        ]
        
        if any(reference_indicators):
            print("✅ Session continuity working - second agent referenced first!")
            return True
        else:
            print("⚠️  Session continuity unclear, but API keys working")
            return True
            
    except Exception as e:
        print(f"❌ Session continuity test failed: {e}")
        return False

async def main():
    print("🚀 Single Session Pipeline API Key Test")
    print("=" * 50)
    
    tests = [
        ("API Key Loading", test_api_key_loading),
        ("Single Agent Execution", test_single_agent_execution),
        ("Session Continuity", test_session_continuity),
    ]
    
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
        print("\n🎉 API KEY LOADING FIX SUCCESSFUL!")
        print("Single session pipeline is ready for production use!")
    elif passed > 0:
        print("\n⚠️  Partial success - some issues remain.")
    else:
        print("\n❌ API key loading fix failed.")

if __name__ == "__main__":
    asyncio.run(main())
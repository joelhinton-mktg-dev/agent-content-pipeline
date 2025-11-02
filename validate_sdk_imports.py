#!/usr/bin/env python3
"""
Validate that all SDK pipeline imports work correctly
"""

def test_module_imports():
    """Test imports at module level"""
    try:
        from pipeline_orchestrator_sdk import SDKPipelineOrchestrator
        print("✅ Module import successful")
        return True
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False

def test_adk_imports():
    """Test ADK imports that are used in the pipeline"""
    try:
        import sys
        sys.path.append('/home/joel/ai-content-pipeline')
        
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        
        # Test that the types we need exist
        assert hasattr(types, 'Content'), "types.Content not found"
        assert hasattr(types, 'Part'), "types.Part not found"
        
        print("✅ All ADK imports successful")
        print(f"   - Runner: {Runner}")
        print(f"   - InMemorySessionService: {InMemorySessionService}")
        print(f"   - types.Content: {types.Content}")
        print(f"   - types.Part: {types.Part}")
        return True
        
    except Exception as e:
        print(f"❌ ADK imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_imports():
    """Test that agent imports work in the process context"""
    try:
        import sys
        sys.path.append('/home/joel/ai-content-pipeline')
        
        from outline_generator.agent import root_agent as outline_agent
        from research_content_creator.agent import root_agent as content_agent
        from seo_optimizer.agent import root_agent as seo_agent
        from publishing_coordinator.agent import root_agent as publish_agent
        
        print("✅ All agent imports successful")
        print(f"   - outline_generator: {outline_agent.name}")
        print(f"   - research_content_creator: {content_agent.name}")
        print(f"   - seo_optimizer: {seo_agent.name}")
        print(f"   - publishing_coordinator: {publish_agent.name}")
        return True
        
    except Exception as e:
        print(f"❌ Agent imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_instantiation():
    """Test that the orchestrator can be instantiated"""
    try:
        from pipeline_orchestrator_sdk import SDKPipelineOrchestrator
        orchestrator = SDKPipelineOrchestrator()
        
        print("✅ Orchestrator instantiation successful")
        print(f"   - Temp dir: {orchestrator.temp_dir}")
        print(f"   - Workflow data: {orchestrator.workflow_data}")
        
        # Clean up
        orchestrator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 SDK Pipeline Import Validation")
    print("=" * 40)
    
    tests = [
        ("Module Import", test_module_imports),
        ("ADK Imports", test_adk_imports),
        ("Agent Imports", test_agent_imports),
        ("Orchestrator Instantiation", test_instantiation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*40}")
    print("VALIDATION SUMMARY:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 All imports working correctly!")
        print("SDK pipeline is ready for use.")
    else:
        print("⚠️  Some import issues detected.")
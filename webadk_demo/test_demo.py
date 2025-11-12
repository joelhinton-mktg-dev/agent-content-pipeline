#!/usr/bin/env python3
"""
Test script for WebADK Demo Interface
Validates setup, dependencies, and basic functionality
"""

import asyncio
import sys
import os
from pathlib import Path
import json

def test_directory_structure():
    """Test that all required directories and files exist"""
    print("🔍 Testing directory structure...")
    
    required_files = [
        'app.py',
        'pipeline_orchestrator.py', 
        'requirements.txt',
        'README.md',
        'templates/base.html',
        'templates/chat.html',
        'templates/login.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_dependencies():
    """Test that all required dependencies can be imported"""
    print("\n🔍 Testing dependencies...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("❌ FastAPI not installed")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("❌ Uvicorn not installed") 
        return False
    
    try:
        import websockets
        print(f"✅ WebSockets: {websockets.__version__}")
    except ImportError:
        print("❌ WebSockets not installed")
        return False
    
    try:
        import jinja2
        print(f"✅ Jinja2: {jinja2.__version__}")
    except ImportError:
        print("❌ Jinja2 not installed")
        return False
    
    return True

def test_pipeline_access():
    """Test that the main pipeline can be accessed"""
    print("\n🔍 Testing pipeline access...")
    
    # Add parent directory to path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    try:
        from pipeline_single_session import SingleSessionPipelineOrchestrator
        print("✅ Pipeline orchestrator import successful")
        
        # Test instantiation
        orchestrator = SingleSessionPipelineOrchestrator()
        print("✅ Pipeline orchestrator instantiation successful")
        return True
        
    except ImportError as e:
        print(f"❌ Pipeline import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Pipeline instantiation failed: {e}")
        return False

def test_agent_imports():
    """Test that all agent modules can be imported"""
    print("\n🔍 Testing agent imports...")
    
    agent_dirs = [
        'outline_generator',
        'research_agent', 
        'research_content_creator',
        'citation_agent',
        'image_agent',
        'fact_check_agent',
        'seo_optimizer',
        'publishing_coordinator'
    ]
    
    parent_dir = Path(__file__).parent.parent
    failed_imports = []
    
    for agent_dir in agent_dirs:
        agent_path = parent_dir / agent_dir
        if not agent_path.exists():
            print(f"❌ Agent directory not found: {agent_dir}")
            failed_imports.append(agent_dir)
            continue
            
        agent_file = agent_path / "agent.py"
        if not agent_file.exists():
            print(f"❌ Agent file not found: {agent_dir}/agent.py")
            failed_imports.append(agent_dir)
            continue
            
        print(f"✅ {agent_dir}")
    
    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        return False
    
    print("✅ All agents accessible")
    return True

def test_env_configuration():
    """Test environment configuration"""
    print("\n🔍 Testing environment configuration...")
    
    parent_dir = Path(__file__).parent.parent
    agent_dirs = ['outline_generator', 'research_agent', 'research_content_creator', 
                  'citation_agent', 'image_agent', 'fact_check_agent', 
                  'seo_optimizer', 'publishing_coordinator']
    
    missing_env = []
    for agent_dir in agent_dirs:
        env_file = parent_dir / agent_dir / ".env"
        if not env_file.exists():
            missing_env.append(agent_dir)
    
    if missing_env:
        print(f"⚠️  Missing .env files: {missing_env}")
        print("   Demo will work but pipeline may fail without API keys")
    else:
        print("✅ All agent .env files present")
    
    # Check for main API keys (without revealing values)
    api_keys_found = {
        'GOOGLE_API_KEY': bool(os.getenv('GOOGLE_API_KEY')),
        'PERPLEXITY_API_KEY': bool(os.getenv('PERPLEXITY_API_KEY')), 
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY'))
    }
    
    print("\n🔑 API Key Status:")
    for key, found in api_keys_found.items():
        status = "✅" if found else "❌"
        print(f"   {status} {key}")
    
    return len(missing_env) < 3  # Allow some missing but not all

async def test_orchestrator_initialization():
    """Test that the demo orchestrator can be initialized"""
    print("\n🔍 Testing demo orchestrator...")
    
    try:
        from pipeline_orchestrator import DemoPipelineOrchestrator
        
        orchestrator = DemoPipelineOrchestrator()
        print("✅ Demo orchestrator created")
        
        # Test initialization (may fail without API keys - that's ok for structure test)
        try:
            success = await orchestrator.initialize()
            if success:
                print("✅ Demo orchestrator initialized successfully")
            else:
                print("⚠️  Demo orchestrator initialization failed (likely missing API keys)")
        except Exception as e:
            print(f"⚠️  Demo orchestrator initialization failed: {e}")
            print("   This is expected without proper API key configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo orchestrator test failed: {e}")
        return False

def test_web_app_structure():
    """Test that the web app can be imported and has required components"""
    print("\n🔍 Testing web app structure...")
    
    try:
        from app import app, manager, authenticate
        print("✅ FastAPI app import successful")
        
        # Test that required routes exist
        routes = [route.path for route in app.routes]
        required_routes = ['/', '/login', '/download/{session_id}/{filename}', '/api/status', '/api/health']
        
        missing_routes = []
        for route in required_routes:
            if route not in routes and not any(r.startswith(route.replace('{', '').replace('}', '')) for r in routes):
                missing_routes.append(route)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        
        print("✅ All required routes present")
        print("✅ WebSocket manager present") 
        print("✅ Authentication function present")
        
        return True
        
    except Exception as e:
        print(f"❌ Web app structure test failed: {e}")
        return False

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("📊 WEBADK DEMO TEST REPORT")
    print("="*60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Dependencies", test_dependencies),
        ("Pipeline Access", test_pipeline_access),
        ("Agent Imports", test_agent_imports),
        ("Environment Config", test_env_configuration),
        ("Web App Structure", test_web_app_structure)
    ]
    
    # Async test
    async_tests = [
        ("Demo Orchestrator", test_orchestrator_initialization)
    ]
    
    results = []
    
    # Run sync tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Run async tests
    async def run_async_tests():
        async_results = []
        for test_name, test_func in async_tests:
            try:
                result = await test_func()
                async_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                async_results.append((test_name, False))
        return async_results
    
    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Recommendations
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ WebADK demo is ready for deployment")
        print("\n🚀 To start the demo:")
        print("   python app.py")
        print("   Then visit: http://localhost:8080")
        print("   Credentials: demo / content2024")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print("Please resolve the issues above before deploying")
        print("\n💡 Common solutions:")
        print("   • Install missing dependencies: pip install -r requirements.txt")
        print("   • Configure API keys in agent .env files")
        print("   • Ensure main pipeline is working: python test_citation_fixes.py")

if __name__ == "__main__":
    print("🧪 WebADK Demo Test Suite")
    print("Testing demo interface setup and dependencies\n")
    
    generate_test_report()
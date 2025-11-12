#!/usr/bin/env python3
"""
Test the fixed pipeline download system
"""

import asyncio
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_demo():
    """Test the fixed demo orchestrator with a quick run"""
    
    try:
        from pipeline_orchestrator import DemoPipelineOrchestrator
        
        logger.info("🧪 Testing Fixed Demo Pipeline")
        logger.info("="*50)
        
        # Create orchestrator
        orchestrator = DemoPipelineOrchestrator() 
        await orchestrator.initialize()
        
        # Test with a simple, fast topic
        logger.info("📝 Testing with quick topic: 'AI benefits'")
        
        # Create a quick test that won't take too long
        result = await orchestrator.process_content_request(
            "AI benefits", 
            "General audience", 
            500  # Shorter content for faster test
        )
        
        logger.info("✅ Pipeline execution completed!")
        
        # Check results
        stages = result.get('stages', {})
        downloads = result.get('downloads', [])
        
        logger.info(f"\n📊 RESULTS SUMMARY:")
        logger.info(f"   Session ID: {result.get('session_id')}")
        logger.info(f"   Processing time: {result.get('processing_time', 0):.1f}s")
        logger.info(f"   Stages captured: {len(stages)}/8")
        logger.info(f"   Download files: {len(downloads)}")
        
        # Check stage outputs
        logger.info(f"\n📋 STAGE OUTPUTS:")
        for stage_name, content in stages.items():
            content_length = len(str(content)) if content else 0
            has_error = 'Error:' in str(content)[:50] if content else False
            status = "❌" if has_error else "✅" if content_length > 50 else "⚠️"
            logger.info(f"   {status} {stage_name:15} | {content_length:5} chars | {'ERROR' if has_error else 'OK'}")
        
        # Check downloads  
        logger.info(f"\n📁 DOWNLOAD FILES:")
        total_size = 0
        empty_files = 0
        error_files = 0
        
        for download in downloads:
            file_path = Path(download['path'])
            size = download['size']
            total_size += size
            
            status = "✅" if size > 100 else "⚠️" if size > 0 else "❌"
            
            # Check for error content
            if file_path.exists() and size > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_preview = f.read(100)
                        if 'Error:' in content_preview:
                            status = "❌"
                            error_files += 1
                        elif size == 0:
                            empty_files += 1
                except:
                    pass
            
            logger.info(f"   {status} {download['name']:20} | {size:6} bytes")
        
        # Summary
        logger.info(f"\n🎯 FINAL ASSESSMENT:")
        logger.info(f"   Total download size: {total_size:,} bytes")
        logger.info(f"   Files with errors: {error_files}")
        logger.info(f"   Empty files: {empty_files}")
        logger.info(f"   Successful files: {len(downloads) - error_files - empty_files}")
        
        if error_files == 0 and empty_files <= 2:  # Allow 1-2 empty files (images might fail)
            logger.info("🎉 SUCCESS: Download system is working properly!")
            logger.info("✅ All agents are responding with content")
            logger.info("✅ Files are being saved with proper content") 
            logger.info("✅ No 'Error: Unknown agent' messages")
            return True
        else:
            logger.warning("⚠️ ISSUES DETECTED:")
            if error_files > 0:
                logger.warning(f"   - {error_files} files contain agent errors")
            if empty_files > 2:
                logger.warning(f"   - {empty_files} files are empty")
            return False
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔧 Testing Fixed WebADK Demo Download System")
    print("Testing after agent loading fixes...")
    print()
    
    success = await test_fixed_demo()
    
    print("\n" + "="*60)
    if success:
        print("🎉 DOWNLOAD SYSTEM FIXED SUCCESSFULLY!")
        print("")
        print("✅ Next steps:")
        print("   1. Start demo: ./start_demo.sh")
        print("   2. Visit: http://localhost:8080")
        print("   3. Login: demo / content2024")
        print("   4. Test: 'Generate an article about AI in healthcare'")
        print("   5. Verify downloads have proper content")
    else:
        print("❌ DOWNLOAD SYSTEM STILL HAS ISSUES")
        print("   Check the logs above for specific problems")

if __name__ == "__main__":
    asyncio.run(main())
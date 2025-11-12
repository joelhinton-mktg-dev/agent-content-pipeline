#!/usr/bin/env python3
"""
Test the file saving logic specifically
"""

import json
from pathlib import Path
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_file_saving():
    """Test the file saving logic with sample data"""
    
    # Sample stage results (similar to what the pipeline returns)
    sample_results = {
        'stages': {
            'outline': "# Sample Outline\n\n1. Introduction\n2. Main Content\n3. Conclusion",
            'research': {'stats': ['78% adoption rate'], 'quotes': ['AI is transformative']},
            'content': "This is a sample article about AI in healthcare...",
            'citations': "1. Source One (2024)\n2. Source Two (2024)", 
            'images': None,  # Test None handling
            'fact_check': "",  # Test empty string
            'seo': "Meta description: AI healthcare...",
            'publish': "WordPress ready content..."
        }
    }
    
    # Create test downloads directory
    downloads_base = Path(__file__).parent / "downloads" / "test_session"
    downloads_base.mkdir(parents=True, exist_ok=True)
    
    # Test the file saving logic
    downloads = []
    
    logger.info("Testing file saving logic...")
    
    for stage_name, content in sample_results['stages'].items():
        logger.info(f"Processing {stage_name}: type={type(content)}, content_preview={str(content)[:50]}...")
        
        file_path = downloads_base / f"{stage_name}.txt"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if content is None:
                    f.write(f"# {stage_name.title()} Stage\n\nNo content generated for this stage.\n")
                elif isinstance(content, dict):
                    f.write(f"# {stage_name.title()} Stage - Structured Data\n\n")
                    f.write(json.dumps(content, indent=2, ensure_ascii=False))
                elif isinstance(content, str) and content.strip():
                    f.write(f"# {stage_name.title()} Stage\n\n")
                    f.write(content.strip())
                else:
                    f.write(f"# {stage_name.title()} Stage\n\n")
                    if hasattr(content, '__dict__'):
                        f.write(json.dumps(vars(content), indent=2, default=str, ensure_ascii=False))
                    else:
                        content_str = str(content).strip()
                        if content_str and content_str != 'None':
                            f.write(content_str)
                        else:
                            f.write("No content available for this stage.")
            
            # Get actual file size
            actual_size = file_path.stat().st_size if file_path.exists() else 0
            logger.info(f"Saved {stage_name}.txt: {actual_size} bytes")
            
            downloads.append({
                'name': f"{stage_name}.txt",
                'path': str(file_path),
                'size': actual_size
            })
            
            # Read back and verify
            if actual_size > 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                    logger.info(f"  Verified content length: {len(saved_content)} chars")
            else:
                logger.warning(f"  File {stage_name}.txt is empty!")
                
        except Exception as e:
            logger.error(f"Error saving {stage_name}.txt: {e}")
    
    # Summary
    logger.info(f"\n=== FILE SAVING TEST SUMMARY ===")
    logger.info(f"Total files created: {len(downloads)}")
    
    empty_files = [d for d in downloads if d['size'] == 0]
    non_empty_files = [d for d in downloads if d['size'] > 0]
    
    logger.info(f"Files with content: {len(non_empty_files)}")
    logger.info(f"Empty files: {len(empty_files)}")
    
    if empty_files:
        logger.warning(f"Empty files detected: {[f['name'] for f in empty_files]}")
    
    for d in downloads:
        status = "✅" if d['size'] > 0 else "❌"
        logger.info(f"  {status} {d['name']}: {d['size']} bytes")
    
    # Test reading files
    logger.info("\n=== TESTING FILE CONTENT ===")
    for d in downloads:
        file_path = Path(d['path'])
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"{d['name']}: {len(content)} chars - {content[:100]}...")

if __name__ == "__main__":
    test_file_saving()
#!/usr/bin/env python3
"""
Enhanced Multi-Agent Content Pipeline Web Interface
With improved prompts for detailed output
"""

from flask import Flask, render_template, request, jsonify, session
import subprocess
import uuid
import json
from pathlib import Path
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class EnhancedPipelineManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'stage': 'outline',
            'data': {},
            'created': time.time()
        }
        return session_id
    
    def get_enhanced_prompt(self, stage, user_input, context=None):
        """Create detailed prompts optimized for each agent"""
        
        prompts = {
            'outline': f"""Create a comprehensive, detailed SEO-optimized outline for "{user_input}".

REQUIREMENTS:
- Target word count: 2500-3500 words
- Include primary and secondary keywords
- Detailed section breakdowns with word counts
- Specific image placement recommendations with descriptions
- FAQ section for featured snippets
- Competitor analysis insights
- Internal linking opportunities

Make this outline extremely detailed and actionable for content creation.""",

            'content': f"""Using this detailed outline, write comprehensive, well-researched content with current data:

OUTLINE:
{context}

REQUIREMENTS:
- Write full sections with proper depth and detail
- Include current statistics and data
- Add specific examples and case studies
- Integrate image placeholders naturally
- Use proper heading structure (H1, H2, H3)
- Include internal linking suggestions
- Write compelling introductions and conclusions
- Ensure content exceeds competitor quality

Provide complete, publication-ready content sections.""",

            'seo': f"""Conduct comprehensive SEO/AEO/GEO optimization analysis for this content:

CONTENT:
{context}

ANALYSIS REQUIREMENTS:
- Complete technical SEO audit
- Schema markup recommendations with code
- Meta tag optimization (multiple variations)
- Featured snippet optimization
- Voice search optimization
- Image SEO recommendations
- Internal linking strategy
- Core Web Vitals improvements
- FAQ section for People Also Ask
- Specific actionable recommendations

Provide detailed, implementable SEO recommendations.""",

            'publish': f"""Create a complete WordPress publication package with all elements:

CONTENT:
{context.get('content', '')}

SEO RECOMMENDATIONS:
{context.get('seo', '')}

PACKAGE REQUIREMENTS:
- WordPress-formatted HTML with proper blocks
- Complete meta tags and descriptions
- Schema markup code (Article + FAQ)
- Image optimization checklist with alt text
- Internal linking implementation
- Open Graph and Twitter card tags
- Publication quality checklist
- All technical elements ready for implementation

Provide a comprehensive, ready-to-publish package."""
        }
        
        return prompts.get(stage, user_input)
    
    def run_agent_enhanced(self, agent_name, prompt):
        """Run ADK agent with enhanced error handling and output processing"""
        try:
            # Write prompt to temp file for better handling
            temp_file = f"/tmp/agent_prompt_{agent_name}_{int(time.time())}.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            # Run with file input and extended timeout
            cmd = f"cat {temp_file} | timeout 180 adk run {agent_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
            return self.clean_output_enhanced(result.stdout)
            
        except Exception as e:
            return f"Error running {agent_name}: {e}"
    
    def clean_output_enhanced(self, raw_output):
        """Enhanced output cleaning to extract agent responses"""
        lines = raw_output.split('\n')
        cleaned_lines = []
        
        # Skip system messages and extract actual agent output
        skip_patterns = [
            'Log setup complete',
            'To access latest log',
            'Running agent',
            'type exit to exit',
            '[user]:',
            'outline_generator',
	    'research_content_creator',
	    'seo_optimizer',
            'publishing_coordinator',
        ]
        
        capturing = False
        for line in lines:
            # Start capturing after the agent name appears
            if any(agent in line for agent in ['outline_generator', 'research_content_creator', 'seo_optimizer', 'publishing_coordinator']):
                capturing = True
                continue
            
            if capturing and not any(skip in line for skip in skip_patterns):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # If result is too short, return more of the raw output
        if len(result) < 200:
            return raw_output
            
        return result

pipeline_manager = EnhancedPipelineManager()

@app.route('/')
def home():
    session_id = pipeline_manager.create_session()
    session['pipeline_id'] = session_id
    return render_template('pipeline_enhanced.html', session_id=session_id)

@app.route('/run_stage', methods=['POST'])
def run_stage():
    data = request.json
    stage = data.get('stage')
    user_input = data.get('prompt')
    context = data.get('context', {})
    
    agent_map = {
        'outline': 'outline_generator',
        'content': 'research_content_creator',
        'seo': 'seo_optimizer',
        'publish': 'publishing_coordinator'
    }
    
    if stage in agent_map:
        # Generate enhanced prompt
        if stage == 'content':
            enhanced_prompt = pipeline_manager.get_enhanced_prompt(stage, user_input, context.get('outline'))
        elif stage == 'seo':
            enhanced_prompt = pipeline_manager.get_enhanced_prompt(stage, user_input, context.get('content'))
        elif stage == 'publish':
            enhanced_prompt = pipeline_manager.get_enhanced_prompt(stage, user_input, context)
        else:
            enhanced_prompt = pipeline_manager.get_enhanced_prompt(stage, user_input)
        
        result = pipeline_manager.run_agent_enhanced(agent_map[stage], enhanced_prompt)
        return jsonify({'success': True, 'result': result})
    
    return jsonify({'success': False, 'error': 'Invalid stage'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

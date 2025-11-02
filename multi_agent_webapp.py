#!/usr/bin/env python3
"""
Multi-Agent Content Pipeline Web Interface
Provides a guided workflow through all 4 agents
"""

from flask import Flask, render_template, request, jsonify, session
import subprocess
import uuid
from pathlib import Path
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class PipelineManager:
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
    
    def run_agent(self, agent_name, prompt):
        """Run ADK agent and return result"""
        try:
            cmd = f"echo '{prompt}' | adk run {agent_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return self.clean_output(result.stdout)
        except Exception as e:
            return f"Error: {e}"
    
    def clean_output(self, raw_output):
        """Clean up ADK CLI output"""
        lines = raw_output.split('\n')
        cleaned_lines = []
        for line in lines:
            if not any(skip in line for skip in ['Log setup', '[user]:', 'Running agent', 'type exit']):
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines).strip()

pipeline_manager = PipelineManager()

@app.route('/')
def home():
    session_id = pipeline_manager.create_session()
    session['pipeline_id'] = session_id
    return render_template('pipeline.html', session_id=session_id)

@app.route('/run_stage', methods=['POST'])
def run_stage():
    data = request.json
    stage = data.get('stage')
    prompt = data.get('prompt')
    
    agent_map = {
        'outline': 'outline_generator',
        'content': 'research_content_creator',
        'seo': 'seo_optimizer',
        'publish': 'publishing_coordinator'
    }
    
    if stage in agent_map:
        result = pipeline_manager.run_agent(agent_map[stage], prompt)
        return jsonify({'success': True, 'result': result})
    
    return jsonify({'success': False, 'error': 'Invalid stage'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

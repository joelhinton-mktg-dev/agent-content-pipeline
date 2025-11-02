#!/usr/bin/env python3
"""
Web interface for the automated agent pipeline
"""

from flask import Flask, render_template, request, jsonify, session
import asyncio
import json
from pipeline_orchestrator import ContentPipelineOrchestrator

app = Flask(__name__)
app.secret_key = 'automated-pipeline-secret'

@app.route('/')
def home():
    return render_template('automated_pipeline.html')

@app.route('/run_pipeline', methods=['POST'])
async def run_pipeline():
    data = request.json
    topic = data.get('topic')
    include_images = data.get('include_images', True)
    
    orchestrator = ContentPipelineOrchestrator()
    
    try:
        results = await orchestrator.run_pipeline(topic, include_images)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

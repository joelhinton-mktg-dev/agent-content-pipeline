#!/usr/bin/env python3
"""
WebADK Demo Application - Interactive Chat Interface for AI Content Pipeline
Features authentication, real-time progress updates, and download functionality
"""

import asyncio
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import uvicorn

from pipeline_orchestrator import demo_orchestrator, generate_content

# Initialize FastAPI app
app = FastAPI(
    title="AI Content Pipeline Demo",
    description="Interactive chat interface for the 8-stage AI content creation pipeline",
    version="2.1.0"
)

# Authentication
security = HTTPBasic()
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "content2024"  # Change this in production!

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple authentication for demo access"""
    is_correct_username = secrets.compare_digest(credentials.username, DEMO_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, DEMO_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Static files and templates
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"
downloads_dir = Path(__file__).parent / "downloads"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_sessions: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_sessions[user_id] = websocket
        print(f"User {user_id} connected")

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        print(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_sessions:
            websocket = self.user_sessions[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except:
                # Connection might be closed
                pass

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                pass

manager = ConnectionManager()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(authenticate)):
    """Main chat interface"""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "username": username,
        "title": "AI Content Pipeline Demo"
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/generate")
async def api_generate_content(
    topic: str = Form(...),
    audience: str = Form("General audience"),
    length: int = Form(1500),
    username: str = Depends(authenticate)
):
    """API endpoint to generate content"""
    try:
        # Initialize orchestrator if needed
        if not demo_orchestrator.session_id:
            await demo_orchestrator.initialize()
        
        # Generate content
        result = await demo_orchestrator.process_content_request(topic, audience, length)
        
        return JSONResponse(content={
            "success": True,
            "session_id": result["session_id"],
            "summary": result.get("summary", {}),
            "downloads": result.get("downloads", []),
            "processing_time": result.get("processing_time", 0)
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat and progress updates"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "generate_content":
                # Start content generation
                topic = message_data["topic"]
                audience = message_data.get("audience", "General audience") 
                length = message_data.get("length", 1500)
                
                # Send acknowledgment
                await manager.send_personal_message({
                    "type": "generation_started",
                    "message": f"🚀 Starting content generation for '{topic}'...",
                    "topic": topic,
                    "timestamp": datetime.now().isoformat()
                }, user_id)
                
                try:
                    # Initialize orchestrator
                    if not demo_orchestrator.session_id:
                        await demo_orchestrator.initialize()
                    
                    # Import the orchestrator class directly
                    from pipeline_orchestrator import DemoPipelineOrchestrator
                    
                    # Create a custom orchestrator for this session with progress callbacks
                    class ProgressTrackingOrchestrator(DemoPipelineOrchestrator):
                        async def _update_stage(self, stage_num: int, status_message: str):
                            await super()._update_stage(stage_num, status_message)
                            # Send progress update
                            await manager.send_personal_message({
                                "type": "progress_update",
                                "stage": stage_num,
                                "total_stages": self.total_stages,
                                "progress": self.get_progress_percentage(),
                                "status": status_message,
                                "stage_name": self.get_current_stage_name(),
                                "timestamp": datetime.now().isoformat()
                            }, user_id)
                    
                    # Start generation with progress tracking
                    progress_orchestrator = ProgressTrackingOrchestrator()
                    await progress_orchestrator.initialize()
                    result = await progress_orchestrator.process_content_request(topic, audience, length)
                    
                    # Send completion message
                    await manager.send_personal_message({
                        "type": "generation_complete",
                        "message": "✅ Content generation complete!",
                        "result": {
                            "session_id": result["session_id"],
                            "summary": result.get("summary", {}),
                            "downloads": result.get("downloads", []),
                            "processing_time": result.get("processing_time", 0)
                        },
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
                    
                except Exception as e:
                    await manager.send_personal_message({
                        "type": "generation_error",
                        "message": f"❌ Error during content generation: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
            
            elif message_data["type"] == "chat_message":
                # Handle general chat messages
                user_message = message_data["message"]
                
                # Simple response logic - in production, integrate with your chat agent
                if "generate" in user_message.lower() and "article" in user_message.lower():
                    await manager.send_personal_message({
                        "type": "bot_message",
                        "message": "I'd be happy to generate an article for you! Please specify:\n- Topic: What should the article be about?\n- Audience: Who is the target audience?\n- Length: How many words? (1500-5000)\n\nFor example: 'Generate an article about AI in healthcare for medical professionals, 2000 words'",
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
                else:
                    await manager.send_personal_message({
                        "type": "bot_message", 
                        "message": "Hello! I'm your AI content pipeline assistant. I can generate comprehensive articles with research, citations, images, and SEO optimization.\n\nJust say something like: 'Generate an article about [topic]' to get started!",
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str, username: str = Depends(authenticate)):
    """Download generated content files"""
    try:
        file_path = downloads_dir / session_id / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def api_status(username: str = Depends(authenticate)):
    """API status endpoint"""
    return {
        "status": "online",
        "version": "2.1.0",
        "features": [
            "8-stage content pipeline",
            "Real-time research (Perplexity)",
            "Professional citations",
            "AI image generation (DALL-E 3)",
            "Fact verification",
            "SEO optimization"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Run the demo server
    print("🚀 Starting AI Content Pipeline Demo")
    print(f"📝 Demo credentials: {DEMO_USERNAME} / {DEMO_PASSWORD}")
    print("🌐 Access at: http://localhost:8080")
    print("💡 Use WebSocket at: ws://localhost:8080/ws/user123")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
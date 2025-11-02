#!/bin/bash

# AI Content Pipeline API Launch Script
# Production-ready startup script with error handling and logging

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/api"
LOG_DIR="$API_DIR/logs"
PID_FILE="$API_DIR/api.pid"
LOG_FILE="$LOG_DIR/startup.log"

# API configuration
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
API_WORKERS="${API_WORKERS:-1}"
RELOAD_FLAG="${RELOAD:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Success message
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Warning message  
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Info message
info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    info_msg "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "$SCRIPT_DIR/pipeline_single_session.py" ]; then
        error_exit "pipeline_single_session.py not found. Make sure you're in the ai-content-pipeline directory."
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is required but not installed"
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.9"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        error_exit "Python 3.9+ required. Found: $PYTHON_VERSION"
    fi
    
    success_msg "Python $PYTHON_VERSION detected"
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        warning_msg "No virtual environment detected. Consider activating one:"
        echo "  source .venv/bin/activate"
    else
        success_msg "Virtual environment active: $VIRTUAL_ENV"
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$API_DIR/results"
    
    log "Prerequisites check completed"
}

# Install dependencies
install_dependencies() {
    info_msg "Installing API dependencies..."
    
    if [ ! -f "$API_DIR/requirements.txt" ]; then
        error_exit "requirements.txt not found in api directory"
    fi
    
    # Install requirements
    if ! pip install -r "$API_DIR/requirements.txt" >> "$LOG_FILE" 2>&1; then
        error_exit "Failed to install dependencies. Check $LOG_FILE for details."
    fi
    
    # Verify critical packages
    if ! python3 -c "import fastapi, uvicorn, slowapi, pydantic" 2>/dev/null; then
        error_exit "Critical packages not properly installed"
    fi
    
    success_msg "Dependencies installed successfully"
    log "Dependencies installation completed"
}

# Check API key configuration
check_api_keys() {
    info_msg "Checking API key configuration..."
    
    # Check for .env files in agent directories
    ENV_COUNT=0
    for agent_dir in outline_generator research_content_creator seo_optimizer publishing_coordinator; do
        if [ -f "$SCRIPT_DIR/$agent_dir/.env" ]; then
            ENV_COUNT=$((ENV_COUNT + 1))
            
            # Check if .env file has content
            if [ -s "$SCRIPT_DIR/$agent_dir/.env" ]; then
                success_msg "API key configured for $agent_dir"
            else
                warning_msg "Empty .env file in $agent_dir"
            fi
        else
            warning_msg "No .env file found in $agent_dir"
        fi
    done
    
    if [ $ENV_COUNT -eq 0 ]; then
        error_exit "No API keys configured. Please set up .env files in agent directories."
    elif [ $ENV_COUNT -lt 4 ]; then
        warning_msg "Not all agents have API keys configured ($ENV_COUNT/4)"
    else
        success_msg "All agents have API key configuration"
    fi
    
    log "API key configuration check completed"
}

# Kill existing API process
kill_existing() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            info_msg "Stopping existing API process (PID: $PID)..."
            kill "$PID"
            sleep 2
            
            # Force kill if still running
            if ps -p "$PID" > /dev/null 2>&1; then
                warning_msg "Force killing process $PID"
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
}

# Start API server
start_api() {
    info_msg "Starting AI Content Pipeline API..."
    
    cd "$SCRIPT_DIR" || error_exit "Failed to change to script directory"
    
    # Set PYTHONPATH to include current directory
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # Build uvicorn command
    UVICORN_CMD="uvicorn api.main:app --host $API_HOST --port $API_PORT"
    
    # Add reload flag for development
    if [ "$RELOAD_FLAG" = "true" ]; then
        UVICORN_CMD="$UVICORN_CMD --reload"
        info_msg "Development mode: Auto-reload enabled"
    fi
    
    # Add workers for production
    if [ "$API_WORKERS" -gt 1 ]; then
        UVICORN_CMD="$UVICORN_CMD --workers $API_WORKERS"
        info_msg "Production mode: $API_WORKERS workers"
    fi
    
    # Start the server
    log "Starting API with command: $UVICORN_CMD"
    
    if [ "$RELOAD_FLAG" = "true" ]; then
        # Development mode - run in foreground
        info_msg "Starting in development mode (foreground)..."
        echo ""
        success_msg "API starting at http://$API_HOST:$API_PORT"
        success_msg "Documentation available at http://$API_HOST:$API_PORT/docs"
        echo ""
        info_msg "Press Ctrl+C to stop the server"
        echo ""
        
        exec $UVICORN_CMD
    else
        # Production mode - run in background
        info_msg "Starting in production mode (background)..."
        
        nohup $UVICORN_CMD > "$LOG_DIR/uvicorn.log" 2>&1 &
        API_PID=$!
        echo $API_PID > "$PID_FILE"
        
        # Wait a moment and check if process started successfully
        sleep 3
        if ps -p $API_PID > /dev/null 2>&1; then
            success_msg "API started successfully (PID: $API_PID)"
            success_msg "API available at http://$API_HOST:$API_PORT"
            success_msg "Documentation at http://$API_HOST:$API_PORT/docs"
            success_msg "Logs: $LOG_DIR/uvicorn.log"
        else
            error_exit "Failed to start API. Check $LOG_DIR/uvicorn.log for details."
        fi
    fi
}

# Health check
health_check() {
    info_msg "Performing health check..."
    
    # Wait for server to start
    sleep 2
    
    # Test health endpoint
    if command -v curl &> /dev/null; then
        HEALTH_URL="http://$API_HOST:$API_PORT/health"
        
        # Retry health check up to 5 times
        for i in {1..5}; do
            if curl -s "$HEALTH_URL" > /dev/null 2>&1; then
                success_msg "Health check passed"
                return 0
            fi
            
            if [ $i -lt 5 ]; then
                info_msg "Health check attempt $i failed, retrying..."
                sleep 2
            fi
        done
        
        warning_msg "Health check failed. API may still be starting up."
    else
        warning_msg "curl not available for health check"
    fi
}

# Print usage information
print_usage() {
    echo "AI Content Pipeline API Launch Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --production     Start in production mode (background, no reload)"
    echo "  --port PORT      Set API port (default: 8000)"
    echo "  --host HOST      Set API host (default: 0.0.0.0)"
    echo "  --workers N      Set number of workers (default: 1)"
    echo "  --stop           Stop running API server"
    echo "  --status         Check API server status"
    echo "  --logs           Show recent logs"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Start in development mode"
    echo "  $0 --production --workers 4  # Start in production with 4 workers"
    echo "  $0 --port 9000              # Start on port 9000"
    echo "  $0 --stop                   # Stop the API server"
    echo ""
}

# Show status
show_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            success_msg "API is running (PID: $PID)"
            
            # Show process info
            echo "Process details:"
            ps -p "$PID" -o pid,ppid,pcpu,pmem,etime,cmd
            
            # Test health endpoint if curl is available
            if command -v curl &> /dev/null; then
                echo ""
                info_msg "Testing health endpoint..."
                curl -s "http://$API_HOST:$API_PORT/health" | python3 -m json.tool 2>/dev/null || echo "Health endpoint not responding"
            fi
        else
            warning_msg "PID file exists but process not running"
            rm -f "$PID_FILE"
        fi
    else
        info_msg "API is not running"
    fi
}

# Show logs
show_logs() {
    if [ -f "$LOG_DIR/uvicorn.log" ]; then
        info_msg "Recent API logs:"
        tail -20 "$LOG_DIR/uvicorn.log"
    else
        warning_msg "No log file found"
    fi
}

# Main execution
main() {
    echo "🚀 AI Content Pipeline API Launcher"
    echo "=================================="
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                RELOAD_FLAG="false"
                shift
                ;;
            --port)
                API_PORT="$2"
                shift 2
                ;;
            --host)
                API_HOST="$2"
                shift 2
                ;;
            --workers)
                API_WORKERS="$2"
                shift 2
                ;;
            --stop)
                kill_existing
                success_msg "API stopped"
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --logs)
                show_logs
                exit 0
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1. Use --help for usage information."
                ;;
        esac
    done
    
    # Run startup sequence
    log "=== API Startup Sequence Started ==="
    
    check_prerequisites
    install_dependencies
    check_api_keys
    kill_existing
    start_api
    
    # Only run health check in production mode
    if [ "$RELOAD_FLAG" != "true" ]; then
        health_check
        log "=== API Startup Sequence Completed ==="
    fi
}

# Handle Ctrl+C gracefully
trap 'echo ""; info_msg "Shutting down..."; kill_existing; exit 0' INT

# Run main function
main "$@"
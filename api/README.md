# AI Content Pipeline API

Production-ready FastAPI wrapper for the AI Content Pipeline, providing RESTful access to multi-agent content generation with authentication, rate limiting, and async job processing.

## 🚀 Quick Start

### Installation
```bash
# Navigate to API directory
cd /home/joel/ai-content-pipeline/api

# Install dependencies
pip install -r requirements.txt

# Start the API server
./run_api.sh
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 🔐 Authentication

All API endpoints require authentication using Bearer tokens (API keys).

### Demo API Keys
- **Demo Key**: `demo-key-001` (10 requests/hour)
- **Production Key**: `prod-key-001` (100 requests/hour)

### Usage
```bash
# Include in Authorization header
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/health
```

## 📊 Rate Limits

| API Key Level | Requests/Hour | Use Case |
|---------------|---------------|----------|
| Demo | 10 | Testing, evaluation |
| Production | 100 | Production usage |

Rate limits reset every hour. Exceeded limits return `429 Too Many Requests`.

## 🛠️ API Endpoints

### Health Check
```bash
GET /health
```

Check API status and metrics.

**Example:**
```bash
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600.5,
  "active_jobs": 2,
  "total_jobs_processed": 15
}
```

### Generate Content
```bash
POST /generate-content
```

Start content generation job.

**Request Body:**
```json
{
  "topic": "AI Marketing Automation",
  "keywords": ["artificial intelligence", "marketing", "automation"],
  "include_images": true,
  "format": "wordpress"
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer demo-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI Marketing Automation",
    "keywords": ["ai", "marketing", "automation"],
    "include_images": true,
    "format": "wordpress"
  }' \
  http://localhost:8000/generate-content
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Content generation started. Use /status/{job_id} to check progress.",
  "estimated_time": "2-5 minutes",
  "created_at": "2024-11-02T10:30:00Z"
}
```

### Check Job Status
```bash
GET /status/{job_id}
```

Monitor job progress.

**Example:**
```bash
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": 75,
  "current_stage": "seo_optimization",
  "created_at": "2024-11-02T10:30:00Z",
  "updated_at": "2024-11-02T10:33:00Z",
  "estimated_completion": "2024-11-02T10:35:00Z",
  "error_message": null
}
```

### Get Results
```bash
GET /results/{job_id}
```

Retrieve completed job results.

**Example:**
```bash
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/results/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "outline": "# AI Marketing Automation Outline\n\n## 1. Introduction...",
  "content": "# AI Marketing Automation Guide\n\nArtificial intelligence...",
  "seo": "## SEO Analysis\n\n### Title Tag Optimization...",
  "publish": "## WordPress Publication Package\n\n### HTML Content...",
  "total_chars": 75420,
  "quality_score": 95.5,
  "processing_time": 245.2,
  "created_at": "2024-11-02T10:30:00Z",
  "completed_at": "2024-11-02T10:34:05Z"
}
```

### List Jobs (Debug)
```bash
GET /jobs
```

List all jobs (for debugging and monitoring).

**Example:**
```bash
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/jobs
```

## 📋 Request Schemas

### ContentRequest
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | ✅ | Content topic (3-200 chars) |
| `keywords` | array | ❌ | Target keywords (max 10) |
| `include_images` | boolean | ❌ | Include image placeholders (default: true) |
| `format` | string | ❌ | Output format: `wordpress`, `markdown`, `json` (default: wordpress) |

### Response Schemas

#### Job Status Values
- `queued` - Job waiting to start
- `processing` - Job currently running
- `completed` - Job finished successfully
- `failed` - Job failed with error

#### Processing Stages
- `queued` - Initial state
- `initializing` - Setting up pipeline
- `session_initialization` - Creating ADK session
- `generating_outline` - Stage 1: Outline generation
- `creating_content` - Stage 2: Content creation
- `seo_optimization` - Stage 3: SEO analysis
- `creating_publication_package` - Stage 4: Publication formatting
- `completed` - All stages finished
- `failed` - Error occurred

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/joel/ai-content-pipeline/api/api.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=3600

# Job Management
RESULTS_RETENTION_HOURS=24
MAX_CONCURRENT_JOBS=5
```

### API Keys Management
Edit `api/main.py` to modify API keys:
```python
api_keys = {
    "your-api-key": {"name": "Your App", "requests_used": 0, "max_requests": 100}
}
```

## 🧪 Testing

### Basic Health Check
```bash
curl -H "Authorization: Bearer demo-key-001" \
     http://localhost:8000/health
```

### Complete Workflow Test
```bash
# 1. Start content generation
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer demo-key-001" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test Topic", "format": "markdown"}' \
  http://localhost:8000/generate-content)

# 2. Extract job ID
JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 3. Monitor progress
while true; do
  STATUS=$(curl -s -H "Authorization: Bearer demo-key-001" \
    http://localhost:8000/status/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 10
done

# 4. Get results (if completed)
if [ "$STATUS" = "completed" ]; then
  curl -H "Authorization: Bearer demo-key-001" \
    http://localhost:8000/results/$JOB_ID | jq '.total_chars'
fi
```

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test concurrent requests
ab -n 10 -c 2 \
   -H "Authorization: Bearer demo-key-001" \
   http://localhost:8000/health
```

## 🚨 Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created (job started)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (job not found)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-11-02T10:30:00Z"
}
```

### Common Errors

#### Invalid API Key
```bash
curl -H "Authorization: Bearer invalid-key" \
     http://localhost:8000/health
```
```json
{
  "detail": "Invalid API key"
}
```

#### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Max 10 requests per hour."
}
```

#### Job Not Found
```json
{
  "detail": "Job not found"
}
```

#### Job Not Completed
```json
{
  "detail": "Job not completed. Current status: processing"
}
```

## 📈 Monitoring

### Logs
```bash
# View API logs
tail -f /home/joel/ai-content-pipeline/api/api.log

# Filter by log level
grep "ERROR" /home/joel/ai-content-pipeline/api/api.log

# Monitor specific job
grep "job_123e4567" /home/joel/ai-content-pipeline/api/api.log
```

### Metrics
- **Active Jobs**: Current jobs in `queued` or `processing` state
- **Total Jobs Processed**: Lifetime job counter
- **API Uptime**: Time since server start
- **Rate Limit Usage**: Requests used per API key

### Health Monitoring
```bash
# Simple health check script
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
API_KEY="demo-key-001"

STATUS=$(curl -s -H "Authorization: Bearer $API_KEY" $HEALTH_URL | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
  echo "API is healthy"
  exit 0
else
  echo "API is unhealthy"
  exit 1
fi
```

## 🔄 Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install gunicorn
pip install gunicorn

# Start with multiple workers
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/api-access.log \
  --error-logfile /var/log/api-error.log
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "api.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service
```ini
[Unit]
Description=AI Content Pipeline API
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/home/joel/ai-content-pipeline
ExecStart=/usr/local/bin/gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🔒 Security Considerations

### API Key Security
- Never expose API keys in client-side code
- Use environment variables for API key storage
- Implement key rotation policies
- Monitor API key usage for suspicious activity

### Network Security
- Use HTTPS in production
- Implement IP whitelisting if needed
- Configure firewall rules
- Regular security updates

### Input Validation
- All inputs are validated using Pydantic models
- SQL injection prevention (when using databases)
- XSS protection for any web interfaces
- File upload restrictions

## 📚 SDK Examples

### Python SDK Example
```python
import httpx
import json
import time

class ContentPipelineClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    async def generate_content(self, topic: str, **kwargs):
        """Generate content and wait for completion"""
        
        # Start job
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate-content",
                headers=self.headers,
                json={"topic": topic, **kwargs}
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data["job_id"]
        
        # Poll for completion
        while True:
            async with httpx.AsyncClient() as client:
                status_response = await client.get(
                    f"{self.base_url}/status/{job_id}",
                    headers=self.headers
                )
                status_data = status_response.json()
                
                if status_data["status"] == "completed":
                    break
                elif status_data["status"] == "failed":
                    raise Exception(f"Job failed: {status_data.get('error_message')}")
                
                await asyncio.sleep(10)
        
        # Get results
        async with httpx.AsyncClient() as client:
            results_response = await client.get(
                f"{self.base_url}/results/{job_id}",
                headers=self.headers
            )
            return results_response.json()

# Usage
client = ContentPipelineClient("http://localhost:8000", "demo-key-001")
result = await client.generate_content("AI Marketing Trends")
print(f"Generated {result['total_chars']} characters")
```

---

**API Status**: Production Ready ✅  
**Version**: 1.0.0  
**Documentation**: Auto-generated at `/docs` endpoint  
**Support**: Monitor logs and health endpoint for troubleshooting
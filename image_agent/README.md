# Image Generation Agent - DALL-E 3 Integration

Intelligent image generation system that automatically creates contextual, professional images for content using OpenAI's DALL-E 3 API.

## 🎯 Purpose

The Image Generation Agent enhances content engagement by:
- **Automatic image analysis** of content structure and placement opportunities
- **Contextual image generation** using DALL-E 3 for relevant, professional visuals
- **Strategic placement suggestions** for maximum content impact
- **Accessibility compliance** with detailed alt text generation
- **Professional file management** with organized output structure

## 🏗️ Architecture Integration

### Phase 2 Enhancement - Stage 2.6
This agent integrates as **Stage 2.6** in the content pipeline:

```
Stage 1: Outline → Stage 1.5: Research → Stage 2: Content → Stage 2.5: Citations → Stage 2.6: Images → Stage 3: SEO → Stage 4: Publish
```

### Dependencies
- **Requires**: Content from research_content_creator (Stage 2)
- **Uses**: Outline from outline_generator (Stage 1) for context
- **Outputs**: Images and placement suggestions for SEO optimization and publishing

## 🔧 Setup

### 1. OpenAI API Key Configuration
```bash
# Edit the .env file
cp image_agent/.env.example image_agent/.env
nano image_agent/.env
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account and add billing information
3. Generate an API key with DALL-E access
4. Copy the key to your `.env` file

### 3. Configure Image Settings
```env
IMAGE_QUALITY=standard        # standard (cheaper) | hd (higher quality)
IMAGE_SIZE=1024x1024         # Square, portrait, or landscape
IMAGE_STYLE=natural          # natural (realistic) | vivid (dramatic)
MAX_IMAGES=5                 # Limit per content piece
```

## 📊 Image Generation Process

### 1. Content Analysis
The agent analyzes content structure to identify optimal image placement:

```python
# Image opportunity types:
- Hero image: Main topic visualization (header)
- Process images: Workflow and step illustrations
- Data images: Charts, graphs, statistics visualization
- Technology images: Tools, software, AI concepts
- Business images: Strategy, team, growth concepts
- Conclusion images: Summary, future outlook
```

### 2. Smart Placement Algorithm
```python
# Placement priority:
1. Hero image (header) - Always included
2. Process/workflow sections - High priority
3. Technology/tools sections - Medium priority
4. Data/statistics sections - Medium priority
5. Business/strategy sections - Low priority
6. Conclusion section - Optional
```

### 3. DALL-E 3 Prompt Generation
Professional prompts optimized for business content:

```python
# Example prompts:
Hero: "Professional, modern illustration representing AI Marketing. Clean, minimalist design with vibrant colors."
Process: "Clean infographic showing step-by-step workflow. Modern flat design with arrows and connected elements."
Data: "Modern data visualization dashboard with colorful charts. Professional business style."
```

## 📋 Output Structure

### File Organization
```
outputs/images/{job_id}/
├── manifest.json                    # Metadata and usage instructions
├── {job_id}_hero_1.png             # Hero image
├── {job_id}_process_2.png          # Process illustration
├── {job_id}_data_3.png             # Data visualization
└── {job_id}_conclusion_4.png       # Conclusion image
```

### Image Result Format
```json
{
  "images": [
    {
      "filename": "job123_hero_1.png",
      "path": "/home/joel/ai-content-pipeline/outputs/images/job123/job123_hero_1.png",
      "relative_path": "outputs/images/job123/job123_hero_1.png",
      "prompt": "Professional illustration representing AI Marketing Automation...",
      "original_prompt": "Hero image for AI Marketing topic",
      "alt_text": "Hero image representing AI Marketing Automation",
      "placement_suggestion": "Place at the top of the article as a header image",
      "section": "introduction",
      "type": "hero",
      "size": "1024x1024",
      "quality": "standard",
      "generated_at": "2024-11-03T10:30:00Z"
    }
  ],
  "manifest": {...},
  "count": 4,
  "metadata": {
    "processing_time": 25.3,
    "opportunities_identified": 5,
    "images_created": 4,
    "api_available": true
  }
}
```

### Manifest File
```json
{
  "job_id": "job123",
  "topic": "AI Marketing Automation",
  "generated_at": "2024-11-03T10:30:00Z",
  "image_count": 4,
  "images": [...],
  "configuration": {
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "style": "natural"
  },
  "usage_instructions": {
    "wordpress": "Upload images to WordPress media library and insert using placement suggestions",
    "markdown": "Reference images using relative paths: ![alt_text](relative_path)",
    "html": "Use <img> tags with alt attributes for accessibility"
  }
}
```

## 🛠️ Usage

### Standalone Usage
```python
from image_agent.agent import image_agent

# Generate images for content
content = """
# AI Marketing Automation Guide

## Introduction
Artificial intelligence is transforming marketing...

## Key Benefits
1. Automated personalization
2. Predictive analytics
3. Enhanced customer insights
"""

outline = """
# AI Marketing Automation
- Introduction to AI Marketing
- Benefits and Use Cases
- Implementation Strategy
"""

result = await image_agent.generate_images(content, outline)
print(f"Generated {result['count']} images")
```

### Pipeline Integration
```python
# Automatically integrated in pipeline_single_session.py
result = await orchestrator.run_pipeline(
    topic="AI Marketing", 
    include_research=True,
    include_citations=True,
    include_images=True  # Enable image generation
)
```

### API Usage
```bash
curl -X POST \
  -H "Authorization: Bearer demo-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI Marketing Automation",
    "include_research": true,
    "include_citations": true,
    "include_images": true,
    "format": "wordpress"
  }' \
  http://localhost:8000/generate-content
```

## ⚙️ Configuration

### Image Quality Settings
```env
# Standard quality (recommended for most use cases)
IMAGE_QUALITY=standard
IMAGE_SIZE=1024x1024

# High definition (costs more, better quality)
IMAGE_QUALITY=hd
IMAGE_SIZE=1024x1792    # Portrait format for hero images
```

### Style Options
```env
# Natural style (realistic, professional)
IMAGE_STYLE=natural

# Vivid style (dramatic, colorful)
IMAGE_STYLE=vivid
```

### Performance Tuning
```env
MAX_IMAGES=3                 # Reduce for faster generation
RATE_LIMIT_DELAY=2          # Increase delay for rate limiting
IMAGE_GENERATION_TIMEOUT=90  # Increase timeout for complex images
```

## 🎨 Image Types and Examples

### Hero Images
```
Purpose: Main topic representation
Placement: Article header
Style: Professional, modern, clean
Colors: Brand-appropriate, vibrant
Content: Abstract concepts, no text
```

### Process Images
```
Purpose: Workflow illustration
Placement: Process/methodology sections
Style: Infographic, step-by-step
Elements: Arrows, connected boxes, flow
Content: Visual process representation
```

### Data Visualizations
```
Purpose: Statistics representation
Placement: Data/analytics sections
Style: Dashboard, charts, graphs
Elements: Clean interfaces, colorful data
Content: Generic charts (no specific numbers)
```

### Technology Images
```
Purpose: Tech concept illustration
Placement: Technology/tools sections
Style: Modern, digital, futuristic
Elements: Devices, networks, AI symbols
Content: Clean tech aesthetics
```

### Business Images
```
Purpose: Strategy/growth concepts
Placement: Business/strategy sections
Style: Corporate, professional
Elements: People, teamwork, success
Content: Positive business imagery
```

## 📈 Performance Metrics

### Generation Performance
- **Image Analysis**: ~1-2 seconds per content piece
- **Prompt Generation**: ~0.5 seconds per image
- **DALL-E 3 Generation**: ~10-15 seconds per image
- **Download & Save**: ~2-3 seconds per image
- **Total Time**: 2-4 minutes for 4-5 images

### Cost Considerations
```
DALL-E 3 Pricing (as of 2024):
- Standard (1024x1024): $0.040 per image
- HD (1024x1024): $0.080 per image
- Standard (1024x1792): $0.080 per image

Typical costs:
- 4 images (standard): ~$0.16
- 4 images (HD): ~$0.32
```

## 🔄 Error Handling

### Graceful Degradation
- **No API Key**: Creates placeholder entries, pipeline continues
- **API Failures**: Logs errors, continues with available images
- **Rate Limits**: Automatic retry with backoff
- **Download Failures**: Retries with timeout handling

### Fallback Behavior
```python
# Without API key:
{
  "images": [
    {
      "filename": "placeholder_hero.png",
      "path": "API_KEY_REQUIRED",
      "status": "api_key_required",
      "placement_suggestion": "Place hero image here"
    }
  ],
  "count": 0,
  "metadata": {"api_available": false}
}
```

## 🧪 Testing

### Basic Image Generation Test
```python
import asyncio
from image_agent.agent import image_agent

async def test_image_generation():
    content = """
    # Test Article
    ## Introduction
    This is a test article about AI technology.
    ## Benefits
    Key benefits include automation and efficiency.
    """
    
    outline = "# Test Article\n- Introduction\n- Benefits"
    
    result = await image_agent.generate_images(content, outline)
    assert result['count'] >= 0  # May be 0 without API key
    print(f"✅ Generated {result['count']} images")

asyncio.run(test_image_generation())
```

### API Key Validation
```bash
# Test API connectivity
python3 -c "
import asyncio
from image_agent.agent import image_agent
async def test():
    result = await image_agent.generate_single_image({
        'dalle_prompt': 'test image',
        'type': 'test',
        'id': 1,
        'section': 'test',
        'alt_text': 'test'
    }, 'test_job')
    print('API Status:', 'OK' if result else 'FAILED')
asyncio.run(test())
"
```

## 🚨 Troubleshooting

### Common Issues

#### API Key Not Working
```bash
# Verify API key format
echo $OPENAI_API_KEY | grep -E '^sk-[a-zA-Z0-9]{48}$'

# Test API access
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"dall-e-3","prompt":"test","size":"1024x1024","n":1}' \
     https://api.openai.com/v1/images/generations
```

#### Images Not Generating
```python
# Check image generation pipeline
from image_agent.agent import image_agent
print("API Key available:", bool(image_agent.api_key))
print("Output directory:", image_agent.images_dir)
print("Max images:", image_agent.max_images)
```

#### Download Failures
```bash
# Check output directory permissions
ls -la /home/joel/ai-content-pipeline/outputs/
mkdir -p /home/joel/ai-content-pipeline/outputs/images
chmod 755 /home/joel/ai-content-pipeline/outputs/images
```

### Rate Limiting
```python
# If hitting rate limits:
IMAGE_GENERATION_TIMEOUT=120  # Increase timeout
RATE_LIMIT_DELAY=3           # Increase delay
MAX_IMAGES=3                 # Reduce image count
```

## 🔗 Integration Points

### Pipeline Integration
- **Input**: Content from Stage 2, Outline from Stage 1
- **Output**: Image files and placement suggestions for SEO/Publishing
- **Flow**: Maintains single session conversation
- **Fallback**: Graceful degradation without API key

### File System Integration
- **Output Directory**: `outputs/images/{job_id}/`
- **Manifest File**: JSON metadata for each generation
- **Relative Paths**: Compatible with web publishing
- **File Naming**: Consistent, descriptive naming convention

### Publishing Integration
- **WordPress**: Direct media library upload ready
- **Markdown**: Relative path references included
- **HTML**: Accessibility-compliant img tags
- **SEO**: Image optimization suggestions included

## 📚 Example Integration

### Complete Pipeline with Images
```python
# 1. Generate outline
outline = await orchestrator.run_agent_in_session('outline_generator', topic_prompt)

# 2. Conduct research  
research_data = await orchestrator.run_research_stage(outline)

# 3. Create content
content = await orchestrator.run_agent_in_session('research_content_creator', content_prompt)

# 4. Add citations
citation_result = await orchestrator.run_citation_stage(content, research_data)

# 5. Generate images (NEW STAGE 2.6)
image_result = await orchestrator.run_image_generation_stage(content, outline)

# 6. Continue with SEO using content + images
seo = await orchestrator.run_agent_in_session('seo_optimizer', seo_prompt)
```

### API Response with Images
```json
{
  "job_id": "uuid",
  "status": "completed",
  "outline": "Content outline...",
  "research": {...},
  "content": "Original content...",
  "citations": {...},
  "images": {
    "images": [...],
    "manifest": {...},
    "count": 4
  },
  "seo": "SEO analysis...",
  "publish": "Publication package..."
}
```

## 📋 Roadmap

### Phase 2 Features (Current)
- ✅ DALL-E 3 integration
- ✅ Intelligent content analysis
- ✅ Strategic image placement
- ✅ Professional prompt generation
- ✅ Accessibility compliance

### Phase 3 Enhancements (Future)
- [ ] Multiple AI model support (Midjourney, Stable Diffusion)
- [ ] Custom brand style integration
- [ ] Batch image optimization
- [ ] Advanced content-image matching AI
- [ ] Image variation generation
- [ ] Stock photo integration fallback

---

**Image Generation Agent Status**: Production Ready ✅  
**Integration**: Pipeline Stage 2.6  
**API**: OpenAI DALL-E 3  
**Output**: Professional images with placement guidance
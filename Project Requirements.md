# Meeting Whiteboard Scribe - Product Requirements Document

## 📋 Project Overview

A intelligent web application that transforms whiteboard photos into structured digital content, leveraging Doubao 1.6 Flash API for OCR and content analysis, automatically generating various output formats for meeting documentation.

## 🎯 Core Features

### Primary Functions
- **Intelligent Image Processing**: Upload whiteboard photos with automatic text/graphics/table recognition
- **Multi-format Export**: Generate Markdown, PPT (PPTX), and mind map formats
- **Content Intelligence**: Automatic content clustering, to-do extraction, and meeting summary
- **Real-time Processing**: Streaming response with progress indicators
- **Collaboration Features**: Share links, team workspace, version history
- **Multi-language Support**: Chinese/English OCR and interface

### Technical Architecture
- **Backend**: Flask 3.0+ + Python 3.9+
- **Frontend**: React 18+ or Vue 3+ (for complex interactions) / Native HTML5+CSS3+ES6
- **AI Integration**: Doubao 1.6 Flash API (Vision + Text capabilities)
- **Image Processing**: OpenCV + Pillow for preprocessing
- **Storage**: PostgreSQL/MySQL for metadata + S3/MinIO for images
- **Cache**: Redis for session and processing queue
- **Deployment**: Docker + Kubernetes ready

## 🏗️ Project Structure

```
whiteboard_scribe/
├── app.py                      # Flask main application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker orchestration
│
├── api/
│   ├── __init__.py
│   ├── auth.py               # Authentication endpoints
│   ├── upload.py              # Image upload handling
│   ├── process.py             # Whiteboard processing endpoints
│   ├── export.py              # Export functionality endpoints
│   └── workspace.py           # Workspace management
│
├── services/
│   ├── __init__.py
│   ├── doubao_service.py      # Doubao API integration
│   ├── image_processor.py     # Image preprocessing
│   ├── content_analyzer.py    # Content structure analysis
│   ├── export_service.py      # Export format generators
│   └── storage_service.py     # File storage handling
│
├── models/
│   ├── __init__.py
│   ├── project.py             # Project/Session model
│   ├── whiteboard.py          # Whiteboard data model
│   ├── export.py              # Export history model
│   └── user.py                # User model (optional)
│
├── utils/
│   ├── __init__.py
│   ├── image_utils.py         # Image manipulation utilities
│   ├── text_utils.py          # Text processing utilities
│   ├── validators.py          # Input validation
│   └── formatters.py          # Output formatting helpers
│
├── templates/
│   ├── index.html             # Main application page
│   ├── preview.html           # Result preview page
│   └── share.html             # Shared content page
│
├── static/
│   ├── css/
│   │   ├── main.css           # Main stylesheet
│   │   ├── components.css     # Component styles
│   │   └── themes.css         # Theme definitions
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   ├── upload.js          # Upload handling
│   │   ├── editor.js          # Result editor
│   │   ├── export.js          # Export functionality
│   │   └── preview.js         # Preview components
│   └── assets/
│       ├── icons/             # UI icons
│       └── images/            # Static images
│
├── exports/
│   ├── templates/
│   │   ├── markdown.md        # Markdown template
│   │   ├── pptx_template.pptx # PowerPoint template
│   │   └── mindmap.json       # Mind map template
│   └── temp/                  # Temporary export files
│
├── tests/
│   ├── test_doubao.py         # Doubao API tests
│   ├── test_processing.py     # Processing tests
│   └── test_export.py         # Export tests
│
└── docs/
    ├── README.md              # Project documentation
    ├── API.md                 # API documentation
    ├── DOUBAO_INTEGRATION.md  # Doubao API guide
    └── DEPLOYMENT.md          # Deployment guide
```

## 🔧 Detailed Functional Requirements

### 1. Image Upload & Processing

#### Upload Module (`api/upload.py`)
```python
# Key endpoints:
POST /api/upload           # Single image upload
POST /api/upload/batch     # Multiple images upload
GET  /api/upload/status    # Check processing status
```

**Features:**
- Support formats: JPG, PNG, HEIC, WebP
- Max file size: 10MB per image
- Image preprocessing: Auto-rotation, contrast enhancement, noise reduction
- Progress tracking via WebSocket/SSE
- Batch upload support (up to 5 images)

#### Image Preprocessing (`services/image_processor.py`)
```python
class ImageProcessor:
    def enhance_whiteboard(image):
        """
        - Perspective correction
        - Brightness/contrast adjustment
        - Shadow removal
        - Sharpening
        - Binarization for text areas
        """
    
    def segment_regions(image):
        """
        - Text region detection
        - Diagram/graphics detection
        - Table structure detection
        - Handwriting vs printed text classification
        """
```

### 2. Doubao API Integration

#### Configuration (`config.py`)
```python
DOUBAO_CONFIG = {
    'api_key': os.getenv('DOUBAO_API_KEY'),
    'endpoint': 'https://ark.cn-beijing.volces.com/api/v3',
    'model': 'doubao-seed-1-6-flash-250715',  # Doubao 1.6 Flash endpoint ID
    'max_tokens': 4096,
    'temperature': 0.3,
    'timeout': 30,
    'retry_attempts': 3
}
```

#### Doubao Service (`services/doubao_service.py`)
```python
class DoubaoService:
    async def analyze_whiteboard(self, image_base64):
        """
        Call Doubao Vision API for whiteboard analysis
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this whiteboard image and extract:
                        1. All text content (maintain original structure)
                        2. Identify tables and their data
                        3. Describe diagrams and flowcharts
                        4. Detect action items (marked with *, -, TODO, etc.)
                        5. Group related content into sections
                        6. Identify key topics and themes
                        
                        Output in structured JSON format:
                        {
                            "title": "suggested title",
                            "sections": [...],
                            "tables": [...],
                            "diagrams": [...],
                            "action_items": [...],
                            "key_points": [...],
                            "raw_text": "..."
                        }"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }],
            "stream": True,
            "temperature": 0.3
        }
        
        # Stream response handling
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                async for line in response.content:
                    yield self.parse_sse_response(line)
    
    async def enhance_content(self, extracted_data):
        """
        Second pass to enhance and structure content
        """
        # Call Doubao text API to:
        # - Fix OCR errors
        # - Add formatting
        # - Generate summaries
        # - Create mind map structure
```

### 3. Content Analysis & Structuring

#### Content Analyzer (`services/content_analyzer.py`)
```python
class ContentAnalyzer:
    def cluster_content(self, sections):
        """Group related content using semantic similarity"""
        
    def extract_todos(self, text):
        """Extract and prioritize action items"""
        patterns = [
            r'(?:TODO|To-?do|ACTION|Action):\s*(.+)',
            r'[-*]\s*\[?\s*\]?\s*(.+)',
            r'(?:\d+\.|\w\))\s*(.+)'
        ]
        
    def generate_hierarchy(self, content):
        """Create hierarchical structure for mind maps"""
        
    def identify_key_concepts(self, text):
        """Extract main topics and keywords"""
```

### 4. Export Generation

#### Export Service (`services/export_service.py`)
```python
class ExportService:
    def to_markdown(self, data):
        """
        Generate clean Markdown with:
        - Proper headings hierarchy
        - Tables in MD format
        - Task lists
        - Mermaid diagrams for flowcharts
        """
        
    def to_pptx(self, data):
        """
        Create PowerPoint with:
        - Title slide
        - Content slides per section
        - Table slides
        - Diagram placeholders
        - Action items slide
        """
        
    def to_mindmap(self, data):
        """
        Generate mind map in:
        - XMind format
        - FreeMind format
        - JSON structure for web rendering
        """
        
    def to_notion(self, data):
        """Export to Notion-compatible format"""
        
    def to_confluence(self, data):
        """Export to Confluence wiki format"""
```

### 5. Frontend Implementation

#### Main Interface (`templates/index.html`)
```html
<!-- Key Components -->
<div id="app">
    <!-- Upload Area -->
    <div class="upload-zone" 
         ondrop="handleDrop(event)" 
         ondragover="handleDragOver(event)">
        <input type="file" accept="image/*" multiple />
        <div class="upload-prompt">
            <i class="icon-camera"></i>
            <p>Drag & drop whiteboard photos or click to browse</p>
            <button class="capture-btn">Take Photo</button>
        </div>
    </div>
    
    <!-- Processing Status -->
    <div class="processing-status" v-if="processing">
        <div class="progress-steps">
            <div class="step" :class="{active: currentStep >= 1}">
                <i class="icon-upload"></i> Uploading
            </div>
            <div class="step" :class="{active: currentStep >= 2}">
                <i class="icon-enhance"></i> Enhancing
            </div>
            <div class="step" :class="{active: currentStep >= 3}">
                <i class="icon-ai"></i> Analyzing
            </div>
            <div class="step" :class="{active: currentStep >= 4}">
                <i class="icon-structure"></i> Structuring
            </div>
        </div>
    </div>
    
    <!-- Results Panel -->
    <div class="results-panel" v-if="results">
        <!-- Side-by-side view -->
        <div class="split-view">
            <div class="original-view">
                <img :src="originalImage" />
                <div class="regions-overlay">
                    <!-- Highlight detected regions -->
                </div>
            </div>
            <div class="extracted-view">
                <div class="content-editor">
                    <!-- Editable extracted content -->
                </div>
            </div>
        </div>
        
        <!-- Export Options -->
        <div class="export-bar">
            <button @click="exportAs('markdown')">
                <i class="icon-markdown"></i> Markdown
            </button>
            <button @click="exportAs('pptx')">
                <i class="icon-powerpoint"></i> PowerPoint
            </button>
            <button @click="exportAs('mindmap')">
                <i class="icon-mindmap"></i> Mind Map
            </button>
            <button @click="shareResults()">
                <i class="icon-share"></i> Share
            </button>
        </div>
    </div>
</div>
```

#### JavaScript Core (`static/js/app.js`)
```javascript
class WhiteboardScribe {
    constructor() {
        this.ws = null;
        this.currentProject = null;
    }
    
    async uploadImage(file) {
        // Show preview
        const preview = await this.generatePreview(file);
        
        // Upload with progress
        const formData = new FormData();
        formData.append('image', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            onUploadProgress: (progress) => {
                this.updateProgress('upload', progress);
            }
        });
        
        // Start SSE for processing updates
        this.connectSSE(response.headers.get('X-Task-ID'));
    }
    
    connectSSE(taskId) {
        const eventSource = new EventSource(`/api/process/stream/${taskId}`);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateResults(data);
        };
    }
    
    async exportAs(format) {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                project_id: this.currentProject,
                format: format,
                options: this.getExportOptions()
            })
        });
        
        // Download file
        const blob = await response.blob();
        this.downloadFile(blob, `whiteboard_${Date.now()}.${format}`);
    }
}
```

## 🎨 UI/UX Design Requirements

### Visual Design
- **Design System**: Material Design 3 or custom design system
- **Color Palette**:
  - Primary: #6366F1 (Indigo)
  - Secondary: #8B5CF6 (Purple)
  - Success: #10B981 (Green)
  - Background: #F9FAFB (Light) / #111827 (Dark)
- **Typography**: Inter, system-ui fallback
- **Icons**: Heroicons or Tabler Icons
- **Animations**: Framer Motion or CSS animations

### Interaction Patterns
- **Drag & Drop**: Visual feedback during drag
- **Real-time Updates**: WebSocket/SSE for live progress
- **Inline Editing**: Click to edit extracted content
- **Keyboard Shortcuts**: 
  - Cmd/Ctrl + V: Paste image
  - Cmd/Ctrl + E: Export
  - Cmd/Ctrl + S: Save
- **Mobile Support**: Camera integration, touch gestures

## 🔐 Security & Performance

### Security Measures
- API key encryption and rotation
- Image sanitization before processing
- Rate limiting (10 requests/minute per IP)
- CORS configuration
- Input validation (file type, size)
- XSS protection for rendered content
- Secure file storage with signed URLs

### Performance Optimization
- Image compression before upload
- Lazy loading for result previews
- CDN for static assets
- Response caching for repeated exports
- Background job queue for processing
- Database indexing for quick retrieval
- Progressive image loading

## 📊 API Endpoints

### Core APIs
```
POST   /api/upload                 # Upload whiteboard image
GET    /api/process/status/{id}    # Get processing status
GET    /api/process/stream/{id}    # SSE endpoint for live updates
POST   /api/analyze                # Trigger Doubao analysis
PUT    /api/content/{id}           # Update extracted content
POST   /api/export                 # Generate export file
GET    /api/export/{id}/download   # Download exported file
POST   /api/share                  # Create shareable link
GET    /api/projects               # List all projects
DELETE /api/projects/{id}          # Delete project
```

### Doubao API Calls
```python
# Vision Analysis Request
POST https://ark.cn-beijing.volces.com/api/v3/chat/completions
{
    "model": "doubao-seed-1-6-flash-250715",
    "messages": [
        {
            "role": "system",
            "content": "You are a meeting whiteboard analyzer..."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract and structure..."},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]
        }
    ],
    "stream": true,
    "temperature": 0.3,
    "max_tokens": 4096
}

# Text Enhancement Request
POST https://ark.cn-beijing.volces.com/api/v3/chat/completions
{
    "model": "doubao-seed-1-6-flash-250715",
    "messages": [
        {
            "role": "system",
            "content": "Format and enhance meeting notes..."
        },
        {
            "role": "user",
            "content": "Extracted content: ..."
        }
    ],
    "temperature": 0.5
}
```

## 🚀 Deployment Configuration

### Docker Setup
```dockerfile
# Multi-stage build
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Variables
```env
# Doubao API Configuration
DOUBAO_API_KEY=your_api_key_here
DOUBAO_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_ID=ep-20241106104627-8x2b4

# Application Settings
FLASK_ENV=production
SECRET_KEY=your_secret_key
MAX_CONTENT_LENGTH=10485760  # 10MB
UPLOAD_FOLDER=/app/uploads

# Database
DATABASE_URL=postgresql://user:pass@localhost/whiteboard_db
REDIS_URL=redis://localhost:6379

# Storage
STORAGE_TYPE=s3  # or 'local'
S3_BUCKET=whiteboard-images
S3_REGION=us-east-1
```

## 📈 Metrics & Monitoring

### Key Metrics
- Upload success rate
- Processing time per image
- Doubao API response time
- Export generation time
- User engagement metrics
- Error rates by type

### Logging
- Application logs (INFO, WARNING, ERROR)
- API call logs
- Performance metrics
- User activity tracking
- Error stack traces

## 🧪 Testing Strategy

### Test Coverage
- Unit tests for each service
- Integration tests for API endpoints
- E2E tests for critical user flows
- Performance tests for image processing
- API mock tests for Doubao integration

### Test Cases
```python
# Example test for Doubao service
def test_doubao_whiteboard_analysis():
    service = DoubaoService()
    test_image = load_test_image('whiteboard_sample.jpg')
    result = await service.analyze_whiteboard(test_image)
    
    assert 'sections' in result
    assert 'action_items' in result
    assert len(result['sections']) > 0
```

## 📚 Documentation Requirements

### User Documentation
- Quick start guide
- Feature tutorials with GIFs
- Export format specifications
- API integration guide
- Troubleshooting FAQ

### Developer Documentation
- API reference with examples
- Doubao integration details
- Architecture diagrams
- Contributing guidelines
- Code style guide

## 🎯 Success Criteria

1. **Accuracy**: >95% text recognition accuracy
2. **Speed**: <10 seconds for average whiteboard processing
3. **Reliability**: 99.9% uptime
4. **User Satisfaction**: >4.5/5 rating
5. **Export Quality**: Professional-grade outputs
6. **Mobile Experience**: Fully functional on mobile devices

## 🔄 Future Enhancements

- Real-time collaboration features
- Video recording with timestamp sync
- Integration with calendar apps
- AI-powered meeting insights
- Multi-board session support
- Handwriting style preservation
- Custom export templates
- API for third-party integrations
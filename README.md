# Meeting Whiteboard Scribe

Transform your whiteboard photos into structured digital content using AI-powered analysis with Doubao 1.6 Flash API.

## 🚀 Features

- **AI-Powered Analysis**: Extract text, tables, diagrams, and action items from whiteboard photos
- **Multiple Export Formats**: Generate Markdown, PowerPoint, Mind Maps, Notion, and Confluence exports
- **Real-time Processing**: Live progress updates during analysis
- **Smart Content Structure**: Automatic organization of content into sections, action items, and key points
- **Easy Sharing**: Generate shareable links for collaboration
- **Multi-language Support**: Chinese and English OCR capabilities
- **Responsive Design**: Works on desktop and mobile devices

## 🛠 Technology Stack

- **Backend**: Flask 3.0+, Python 3.9+
- **Frontend**: HTML5, CSS3, ES6 JavaScript
- **AI Integration**: Doubao 1.6 Flash API
- **Image Processing**: OpenCV, Pillow
- **Database**: PostgreSQL/SQLite
- **Cache**: Redis
- **Export Generation**: python-pptx, markdown, custom formats
- **Deployment**: Docker, Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose
- Doubao API key from ByteDance

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd whiteboardsystem
```

### 2. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
DOUBAO_API_KEY=your_doubao_api_key_here
DOUBAO_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_ID=doubao-seed-1-6-flash-250715
SECRET_KEY=your_secret_key_here
```

### 3. Start with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the application
- Open http://localhost:5000 in your browser
- Upload whiteboard photos and start analyzing!

## 🔧 Development Setup

### Local Development (without Docker)

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up database**:
```bash
# For SQLite (default)
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# For PostgreSQL
export DATABASE_URL=postgresql://user:password@localhost/whiteboard_db
```

3. **Run the application**:
```bash
python app.py
```

### API Testing

Test the API endpoints:

```bash
# Health check
curl http://localhost:5000/health

# Upload image
curl -X POST -F "image=@whiteboard.jpg" http://localhost:5000/api/upload

# Get project info
curl http://localhost:5000/api/projects/{project_id}
```

## 📚 API Documentation

### Core Endpoints

- `POST /api/upload` - Upload whiteboard images
- `POST /api/analyze` - Trigger AI analysis
- `GET /api/process/stream/{task_id}` - Real-time processing updates
- `POST /api/export` - Generate exports
- `GET /api/projects` - List projects
- `POST /api/share` - Create shareable links

### Export Formats

- **Markdown**: Clean markdown with tables and task lists
- **PowerPoint**: Professional presentation slides
- **Mind Map**: JSON/XMind/FreeMind formats
- **Notion**: Notion-compatible format
- **Confluence**: Wiki markup format

## 🔐 Security Features

- API key encryption and secure storage
- Image sanitization and validation
- Rate limiting (configurable)
- CORS protection
- Input validation and XSS protection
- Secure file upload handling

## 🎯 Usage Examples

### 1. Basic Upload and Analysis
```javascript
// Upload image
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
});

// Analyze whiteboard
const analysis = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ whiteboard_id: whiteboardId })
});
```

### 2. Export to Different Formats
```javascript
// Export as Markdown
const exportResponse = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        project_id: projectId,
        format: 'markdown',
        options: { include_images: true }
    })
});
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
```bash
# Set production environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:password@host:port/dbname
```

2. **Docker Production**:
```bash
# Use production docker-compose
docker-compose -f docker-compose.yml up -d
```

3. **With Nginx**:
```bash
# Include nginx service
docker-compose up -d web db redis nginx
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOUBAO_API_KEY` | Doubao API key | Required |
| `DOUBAO_ENDPOINT` | API endpoint URL | https://ark.cn-beijing.volces.com/api/v3 |
| `DOUBAO_MODEL_ID` | Model identifier | doubao-seed-1-6-flash-250715 |
| `DATABASE_URL` | Database connection | sqlite:///whiteboard_scribe.db |
| `REDIS_URL` | Redis connection | redis://localhost:6379 |
| `SECRET_KEY` | Flask secret key | Random generated |
| `STORAGE_TYPE` | Storage backend | local |
| `MAX_CONTENT_LENGTH` | Max upload size | 16MB |

## 🧪 Testing

Run tests:
```bash
# Unit tests
python -m pytest tests/

# API tests
python -m pytest tests/test_api.py

# Integration tests
python -m pytest tests/test_integration.py
```

## 📊 Monitoring

Monitor the application:

```bash
# Check container health
docker-compose ps

# View logs
docker-compose logs -f web

# Monitor resource usage
docker stats
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ByteDance Doubao AI for powerful vision and text analysis
- OpenCV community for image processing capabilities
- Flask community for the excellent web framework
- All contributors and users of this project

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the API documentation at `/api/docs` (when running)

---

Made with ❤️ for better meeting documentation
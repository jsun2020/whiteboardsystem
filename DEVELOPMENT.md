# Development Setup Guide

## Getting Started

### Prerequisites
- Python 3.8+ 
- Git
- Virtual environment (recommended)

### Initial Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd whiteboardsystem

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy `.env.example` to `.env`
2. Configure your API keys and database settings
3. Set up upload directories (will be created automatically)

### Running the Application
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Recent Fixes Applied

### SQLAlchemy Circular Import (Fixed)
- Created separate `database.py` module
- Updated all imports to use the new database module

### PNG File Support (Fixed) 
- Added automatic PNG to JPEG conversion for API compatibility
- Modified Doubao service to handle different image formats

### Image Display Issues (Fixed)
- Added `/api/whiteboard/image/<id>` endpoint
- Fixed image serving in the analysis results section

## Project Structure
```
whiteboardsystem/
├── api/                    # API endpoints
├── models/                 # Database models
├── services/               # Business logic services
├── static/                 # CSS, JS, images
├── templates/              # HTML templates
├── utils/                  # Utility functions
├── uploads/                # Uploaded files (gitignored)
├── exports/                # Export files (gitignored)
├── app.py                  # Main Flask application
├── database.py             # Database configuration
└── config.py              # Application configuration
```

## Git Workflow
- Main branch: `master`
- Feature branches: `feature/feature-name`
- Commit messages should be descriptive
- All major features should include tests

## Deployment
See `docker-compose.yml` for containerized deployment options.
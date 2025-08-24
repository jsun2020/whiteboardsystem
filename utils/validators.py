import os
from PIL import Image
from werkzeug.datastructures import FileStorage
from config import Config

def validate_image_file(file: FileStorage) -> dict:
    """
    Validate uploaded image file
    Returns dict with 'valid' boolean and 'error' message if invalid
    """
    try:
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > Config.MAX_CONTENT_LENGTH:
            return {
                'valid': False,
                'error': f'File too large. Maximum size is {Config.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB'
            }
        
        if file_size == 0:
            return {
                'valid': False,
                'error': 'Empty file'
            }
        
        # Check file extension
        filename = file.filename.lower()
        if not filename or '.' not in filename:
            return {
                'valid': False,
                'error': 'Invalid filename'
            }
        
        extension = filename.rsplit('.', 1)[1]
        if extension not in Config.ALLOWED_EXTENSIONS:
            return {
                'valid': False,
                'error': f'Invalid file type. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }
        
        # Validate image content
        try:
            # Read first few bytes to check magic number
            file_header = file.read(1024)
            file.seek(0)
            
            # Check if it's actually an image
            image_signatures = {
                b'\xff\xd8\xff': 'jpeg',
                b'\x89\x50\x4e\x47': 'png',
                b'\x47\x49\x46': 'gif',
                b'\x52\x49\x46\x46': 'webp',
                b'\x42\x4d': 'bmp'
            }
            
            is_valid_image = False
            for signature in image_signatures:
                if file_header.startswith(signature):
                    is_valid_image = True
                    break
            
            if not is_valid_image:
                return {
                    'valid': False,
                    'error': 'File is not a valid image'
                }
            
            # Try to open with PIL to verify it's a valid image
            try:
                img = Image.open(file)
                img.verify()
                file.seek(0)  # Reset after verification
            except Exception:
                return {
                    'valid': False,
                    'error': 'Corrupted image file'
                }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'File validation error: {str(e)}'
            }
        
        return {
            'valid': True,
            'error': None
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation failed: {str(e)}'
        }

def validate_project_data(data: dict) -> dict:
    """
    Validate project creation/update data
    """
    errors = []
    
    # Validate title
    title = data.get('title', '').strip()
    if title and len(title) > 200:
        errors.append('Title must be less than 200 characters')
    
    # Validate description
    description = data.get('description', '').strip()
    if description and len(description) > 1000:
        errors.append('Description must be less than 1000 characters')
    
    # Validate status
    status = data.get('status', '')
    valid_statuses = ['draft', 'processing', 'completed', 'error']
    if status and status not in valid_statuses:
        errors.append(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_export_options(export_type: str, options: dict) -> dict:
    """
    Validate export options based on export type
    """
    errors = []
    
    if export_type == 'markdown':
        # Validate markdown options
        if 'table_format' in options:
            if options['table_format'] not in ['github', 'grid']:
                errors.append('Invalid table format for markdown')
    
    elif export_type == 'pptx':
        # Validate PowerPoint options
        if 'template' in options:
            if options['template'] not in ['default', 'minimal', 'corporate']:
                errors.append('Invalid PowerPoint template')
        
        if 'slides_per_section' in options:
            try:
                slides_per_section = int(options['slides_per_section'])
                if slides_per_section < 1 or slides_per_section > 5:
                    errors.append('Slides per section must be between 1 and 5')
            except (ValueError, TypeError):
                errors.append('Slides per section must be a valid number')
    
    elif export_type == 'mindmap':
        # Validate mind map options
        if 'format' in options:
            if options['format'] not in ['json', 'xmind', 'freemind']:
                errors.append('Invalid mind map format')
        
        if 'max_depth' in options:
            try:
                max_depth = int(options['max_depth'])
                if max_depth < 1 or max_depth > 10:
                    errors.append('Max depth must be between 1 and 10')
            except (ValueError, TypeError):
                errors.append('Max depth must be a valid number')
    
    elif export_type == 'notion':
        # Validate Notion options
        if 'page_title' in options:
            if len(options['page_title']) > 100:
                errors.append('Page title must be less than 100 characters')
    
    elif export_type == 'confluence':
        # Validate Confluence options
        if 'space_key' in options:
            space_key = options['space_key']
            if space_key and (len(space_key) > 20 or not space_key.isalnum()):
                errors.append('Space key must be alphanumeric and less than 20 characters')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    """
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename

def validate_content_data(data: dict) -> dict:
    """
    Validate structured content data
    """
    errors = []
    
    # Check required fields
    if not isinstance(data, dict):
        errors.append('Content must be a valid JSON object')
        return {'valid': False, 'errors': errors}
    
    # Validate sections
    if 'sections' in data:
        if not isinstance(data['sections'], list):
            errors.append('Sections must be an array')
        else:
            for i, section in enumerate(data['sections']):
                if not isinstance(section, dict):
                    errors.append(f'Section {i} must be an object')
                elif 'heading' not in section and 'content' not in section:
                    errors.append(f'Section {i} must have either heading or content')
    
    # Validate action items
    if 'action_items' in data:
        if not isinstance(data['action_items'], list):
            errors.append('Action items must be an array')
        else:
            for i, item in enumerate(data['action_items']):
                if not isinstance(item, dict):
                    errors.append(f'Action item {i} must be an object')
                elif 'task' not in item:
                    errors.append(f'Action item {i} must have a task')
    
    # Validate tables
    if 'tables' in data:
        if not isinstance(data['tables'], list):
            errors.append('Tables must be an array')
        else:
            for i, table in enumerate(data['tables']):
                if not isinstance(table, dict):
                    errors.append(f'Table {i} must be an object')
                elif 'headers' in table and not isinstance(table['headers'], list):
                    errors.append(f'Table {i} headers must be an array')
                elif 'rows' in table and not isinstance(table['rows'], list):
                    errors.append(f'Table {i} rows must be an array')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
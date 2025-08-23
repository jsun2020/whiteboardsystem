import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image, ExifTags
import mimetypes
from models.project import Project
from models.whiteboard import Whiteboard
from models.user import User
from database import db
from services.storage_service import StorageService
from services.image_processor import ImageProcessor
from utils.validators import validate_image_file
from api.auth import login_required

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
@login_required
def upload_image():
    try:
        # Check user's service eligibility
        user = request.current_user
        if not user.can_use_service():
            return jsonify({
                'error': 'Usage limit exceeded. Please upgrade your plan or add your API key in Settings.',
                'usage_info': {
                    'free_uses_remaining': max(0, 10 - user.free_uses_count),
                    'subscription_type': user.subscription_type,
                    'has_custom_api': bool(user.custom_api_key)
                }
            }), 403
        
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get or create project
        project_id = request.form.get('project_id')
        if not project_id:
            project = Project()
            project.user_id = user.id  # Associate project with current user
            db.session.add(project)
            db.session.commit()
            project_id = project.id
            # Increment project usage
            user.increment_usage('projects')
        else:
            project = Project.query.get_or_404(project_id)
            # Verify project belongs to current user
            if project.user_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Validate file
        validation_result = validate_image_file(file)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Get file info
        file_size = len(file.read())
        file.seek(0)  # Reset file pointer
        mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
        
        # Initialize storage service
        storage_service = StorageService()
        
        # Save original file
        original_path = storage_service.save_file(file, unique_filename, 'original')
        
        # Create whiteboard record
        whiteboard = Whiteboard(
            project_id=project_id,
            filename=filename,
            original_path=original_path,
            file_size=file_size,
            mime_type=mime_type,
            processing_status='uploaded'
        )
        
        # Increment image usage
        user.increment_usage('images')
        
        db.session.add(whiteboard)
        db.session.commit()
        
        # Trigger image processing (async)
        from services.doubao_service import DoubaoService
        doubao_service = DoubaoService()
        
        # Start processing in background
        try:
            # For demo purposes, we'll process synchronously
            # In production, use Celery or similar for async processing
            image_processor = ImageProcessor()
            
            # Process image
            whiteboard.update_processing_status('processing', 25)
            processed_image_path = image_processor.enhance_whiteboard(original_path)
            
            if processed_image_path:
                whiteboard.processed_path = processed_image_path
                whiteboard.update_processing_status('processing', 50)
            
            # This would normally be async - for demo we'll just mark as ready for analysis
            whiteboard.update_processing_status('processing', 75, None)
            
        except Exception as e:
            whiteboard.update_processing_status('error', 0, str(e))
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'whiteboard_id': whiteboard.id,
            'message': 'Image uploaded successfully',
            'task_id': whiteboard.id  # For status checking
        }), 201
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload/batch', methods=['POST'])
@login_required
def upload_batch():
    try:
        # Check user's service eligibility
        user = request.current_user
        if not user.can_use_service():
            return jsonify({
                'error': 'Usage limit exceeded. Please upgrade your plan or add your API key in Settings.',
                'usage_info': {
                    'free_uses_remaining': max(0, 10 - user.free_uses_count),
                    'subscription_type': user.subscription_type,
                    'has_custom_api': bool(user.custom_api_key)
                }
            }), 403
        
        files = request.files.getlist('images')
        if not files:
            return jsonify({'error': 'No images provided'}), 400
        
        if len(files) > 5:
            return jsonify({'error': 'Maximum 5 images allowed per batch'}), 400
        
        # Get or create project
        project_id = request.form.get('project_id')
        if not project_id:
            project = Project()
            project.user_id = user.id  # Associate project with current user
            db.session.add(project)
            db.session.commit()
            project_id = project.id
            # Increment project usage
            user.increment_usage('projects')
        else:
            project = Project.query.get_or_404(project_id)
            # Verify project belongs to current user
            if project.user_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        
        results = []
        for file in files:
            if file.filename == '':
                continue
                
            # Process each file (similar to single upload)
            validation_result = validate_image_file(file)
            if not validation_result['valid']:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': validation_result['error']
                })
                continue
            
            try:
                # Similar processing as single upload
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                file_size = len(file.read())
                file.seek(0)
                mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
                
                storage_service = StorageService()
                original_path = storage_service.save_file(file, unique_filename, 'original')
                
                whiteboard = Whiteboard(
                    project_id=project_id,
                    filename=filename,
                    original_path=original_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    processing_status='uploaded'
                )
                
                # Increment image usage for each successful upload
                user.increment_usage('images')
                
                db.session.add(whiteboard)
                db.session.commit()
                
                results.append({
                    'filename': filename,
                    'whiteboard_id': whiteboard.id,
                    'success': True
                })
                
            except Exception as e:
                current_app.logger.error(f'Error processing file {file.filename}: {str(e)}', exc_info=True)
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'results': results,
            'uploaded_count': len([r for r in results if r['success']])
        })
        
    except Exception as e:
        current_app.logger.error(f'Upload batch error: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload/status/<task_id>', methods=['GET'])
def upload_status(task_id):
    try:
        whiteboard = Whiteboard.query.get_or_404(task_id)
        return jsonify({
            'task_id': task_id,
            'status': whiteboard.processing_status,
            'progress': whiteboard.processing_progress,
            'error': whiteboard.error_message,
            'whiteboard': whiteboard.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
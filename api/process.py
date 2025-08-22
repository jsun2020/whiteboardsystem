import asyncio
import json
from flask import Blueprint, request, jsonify, Response, current_app
from models.whiteboard import Whiteboard
from models.project import Project
from models.user import User
from database import db
from services.doubao_service import DoubaoService
from services.content_analyzer import ContentAnalyzer
from services.image_processor import ImageProcessor
from api.auth import login_required

process_bp = Blueprint('process', __name__)

@process_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_whiteboard():
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
        
        data = request.get_json()
        whiteboard_id = data.get('whiteboard_id')
        
        if not whiteboard_id:
            return jsonify({'error': 'Whiteboard ID required'}), 400
        
        whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
        
        # Verify whiteboard belongs to current user
        if whiteboard.user_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if whiteboard.processing_status == 'processing':
            return jsonify({'error': 'Already processing'}), 409
        
        # Start analysis
        whiteboard.update_processing_status('processing', 0)
        
        try:
            # Initialize services
            doubao_service = DoubaoService()
            content_analyzer = ContentAnalyzer()
            
            # Step 1: Call Doubao API for image analysis
            whiteboard.update_processing_status('processing', 25)
            
            # Read the image file and convert to base64
            with open(whiteboard.processed_path or whiteboard.original_path, 'rb') as img_file:
                import base64
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Analyze with Doubao - pass the correct MIME type
            analysis_result = asyncio.run(doubao_service.analyze_whiteboard(image_base64, whiteboard.mime_type))
            
            whiteboard.update_processing_status('processing', 50)
            
            # Step 2: Structure and enhance content
            structured_content = content_analyzer.structure_content(analysis_result)
            
            whiteboard.update_processing_status('processing', 75)
            
            # Step 3: Save results
            whiteboard.raw_text = analysis_result.get('raw_text', '')
            whiteboard.set_structured_content(structured_content)
            whiteboard.confidence_score = analysis_result.get('confidence', 0.85)
            
            whiteboard.update_processing_status('completed', 100)
            
            # Update project title if not set
            project = Project.query.get(whiteboard.project_id)
            if not project.title and structured_content.get('title'):
                project.title = structured_content['title']
                project.status = 'completed'
                db.session.commit()
            
            return jsonify({
                'success': True,
                'whiteboard_id': whiteboard_id,
                'structured_content': structured_content,
                'raw_text': whiteboard.raw_text,
                'confidence_score': whiteboard.confidence_score
            })
            
        except Exception as e:
            whiteboard.update_processing_status('error', 0, str(e))
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@process_bp.route('/process/stream/<task_id>')
def process_stream(task_id):
    def generate():
        whiteboard = Whiteboard.query.get(task_id)
        if not whiteboard:
            yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
            return
        
        # Simulate streaming progress updates
        import time
        
        last_progress = 0
        while whiteboard.processing_status == 'processing':
            db.session.refresh(whiteboard)
            
            if whiteboard.processing_progress != last_progress:
                data = {
                    'status': whiteboard.processing_status,
                    'progress': whiteboard.processing_progress,
                    'message': get_progress_message(whiteboard.processing_progress)
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_progress = whiteboard.processing_progress
            
            if whiteboard.processing_status in ['completed', 'error']:
                break
                
            time.sleep(1)
        
        # Send final status
        final_data = {
            'status': whiteboard.processing_status,
            'progress': whiteboard.processing_progress,
            'error': whiteboard.error_message,
            'whiteboard': whiteboard.to_dict()
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache'})

def get_progress_message(progress):
    if progress < 25:
        return "Preparing image for analysis..."
    elif progress < 50:
        return "Analyzing whiteboard content..."
    elif progress < 75:
        return "Extracting text and structures..."
    elif progress < 100:
        return "Finalizing results..."
    else:
        return "Analysis complete!"

@process_bp.route('/enhance', methods=['POST'])
def enhance_content():
    try:
        data = request.get_json()
        whiteboard_id = data.get('whiteboard_id')
        enhanced_content = data.get('content')
        
        if not whiteboard_id or not enhanced_content:
            return jsonify({'error': 'Whiteboard ID and content required'}), 400
        
        whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
        
        # Update with enhanced content
        whiteboard.set_structured_content(enhanced_content)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Content updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@process_bp.route('/content/<whiteboard_id>', methods=['GET'])
def get_content(whiteboard_id):
    try:
        whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
        
        return jsonify({
            'whiteboard_id': whiteboard_id,
            'status': whiteboard.processing_status,
            'raw_text': whiteboard.raw_text,
            'structured_content': whiteboard.get_structured_content(),
            'confidence_score': whiteboard.confidence_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@process_bp.route('/content/<whiteboard_id>', methods=['PUT'])
def update_content(whiteboard_id):
    try:
        data = request.get_json()
        whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
        
        # Update fields if provided
        if 'raw_text' in data:
            whiteboard.raw_text = data['raw_text']
        
        if 'structured_content' in data:
            whiteboard.set_structured_content(data['structured_content'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Content updated successfully',
            'whiteboard': whiteboard.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
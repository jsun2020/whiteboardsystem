import os
from flask import Blueprint, request, jsonify, send_file, current_app
from models.project import Project
from models.export import Export
from database import db
from services.export_service import ExportService
import json

export_bp = Blueprint('export', __name__)

@export_bp.route('/export', methods=['POST'])
def generate_export():
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        export_format = data.get('format')
        options = data.get('options', {})
        
        if not project_id or not export_format:
            return jsonify({'error': 'Project ID and format required'}), 400
        
        if export_format not in ['markdown', 'pptx', 'mindmap', 'notion', 'confluence']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        project = Project.query.get_or_404(project_id)
        
        # Check if project has content
        if not project.whiteboards or not any(wb.processing_status == 'completed' for wb in project.whiteboards):
            return jsonify({'error': 'No processed whiteboards found in project'}), 400
        
        # Initialize export service
        export_service = ExportService()
        
        try:
            # Generate export
            if export_format == 'markdown':
                file_path, filename = export_service.to_markdown(project, options)
            elif export_format == 'pptx':
                file_path, filename = export_service.to_pptx(project, options)
            elif export_format == 'mindmap':
                file_path, filename = export_service.to_mindmap(project, options)
            elif export_format == 'notion':
                file_path, filename = export_service.to_notion(project, options)
            elif export_format == 'confluence':
                file_path, filename = export_service.to_confluence(project, options)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create export record
            export = Export(
                project_id=project_id,
                export_type=export_format,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                export_options=json.dumps(options),
                status='completed'
            )
            export.mark_completed()
            
            db.session.add(export)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'export_id': export.id,
                'filename': filename,
                'download_url': f'/api/export/{export.id}/download',
                'file_size': file_size
            })
            
        except Exception as e:
            return jsonify({'error': f'Export generation failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/export/<export_id>/download', methods=['GET'])
def download_export(export_id):
    try:
        export = Export.query.get_or_404(export_id)
        
        if export.status != 'completed':
            return jsonify({'error': 'Export not ready'}), 400
        
        if not os.path.exists(export.file_path):
            return jsonify({'error': 'Export file not found'}), 404
        
        # Track download
        export.mark_downloaded()
        
        return send_file(
            export.file_path,
            as_attachment=True,
            download_name=export.filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/export/<export_id>', methods=['GET'])
def get_export_info(export_id):
    try:
        export = Export.query.get_or_404(export_id)
        return jsonify(export.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/exports/<project_id>', methods=['GET'])
def get_project_exports(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        exports = Export.query.filter_by(project_id=project_id).order_by(Export.created_at.desc()).all()
        
        return jsonify({
            'project_id': project_id,
            'exports': [export.to_dict() for export in exports]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/export/formats', methods=['GET'])
def get_export_formats():
    return jsonify({
        'formats': [
            {
                'id': 'markdown',
                'name': 'Markdown',
                'description': 'Clean markdown with tables and task lists',
                'extension': 'md',
                'options': [
                    {'key': 'include_images', 'type': 'boolean', 'default': True},
                    {'key': 'include_diagrams', 'type': 'boolean', 'default': True},
                    {'key': 'table_format', 'type': 'select', 'options': ['github', 'grid'], 'default': 'github'}
                ]
            },
            {
                'id': 'pptx',
                'name': 'PowerPoint',
                'description': 'Professional presentation slides',
                'extension': 'pptx',
                'options': [
                    {'key': 'template', 'type': 'select', 'options': ['default', 'minimal', 'corporate'], 'default': 'default'},
                    {'key': 'slides_per_section', 'type': 'number', 'default': 1},
                    {'key': 'include_notes', 'type': 'boolean', 'default': True}
                ]
            },
            {
                'id': 'mindmap',
                'name': 'Mind Map',
                'description': 'Interactive mind map visualization',
                'extension': 'json',
                'options': [
                    {'key': 'format', 'type': 'select', 'options': ['json', 'xmind', 'freemind'], 'default': 'json'},
                    {'key': 'max_depth', 'type': 'number', 'default': 5},
                    {'key': 'include_colors', 'type': 'boolean', 'default': True}
                ]
            },
            {
                'id': 'notion',
                'name': 'Notion',
                'description': 'Notion-compatible format',
                'extension': 'md',
                'options': [
                    {'key': 'page_title', 'type': 'string', 'default': ''},
                    {'key': 'include_properties', 'type': 'boolean', 'default': True}
                ]
            },
            {
                'id': 'confluence',
                'name': 'Confluence',
                'description': 'Confluence wiki format',
                'extension': 'txt',
                'options': [
                    {'key': 'space_key', 'type': 'string', 'default': ''},
                    {'key': 'include_macros', 'type': 'boolean', 'default': True}
                ]
            }
        ]
    })

@export_bp.route('/export/<export_id>', methods=['DELETE'])
def delete_export(export_id):
    try:
        export = Export.query.get_or_404(export_id)
        
        # Delete file if exists
        if os.path.exists(export.file_path):
            os.remove(export.file_path)
        
        # Delete record
        db.session.delete(export)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Export deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
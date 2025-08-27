// Preview page functionality
class PreviewApp {
    constructor(projectId) {
        this.projectId = projectId;
        this.project = null;
        this.authManager = new AuthManager();
    }

    static async init(projectId) {
        const app = new PreviewApp(projectId);
        await app.initialize();
        return app;
    }

    async initialize() {
        console.log('Preview app initialized for project:', this.projectId);
        
        // Wait for auth manager to initialize
        await this.authManager.init();
        
        // Load project data
        await this.loadProject();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    async loadProject() {
        try {
            console.log('Loading project data...');
            
            // Check if user is authenticated
            if (!this.authManager.isAuthenticated()) {
                console.error('User not authenticated');
                this.showError('Please log in to view this project');
                return;
            }

            const response = await fetch(`/api/projects/${this.projectId}`, {
                headers: this.authManager.getAuthHeaders()
            });

            console.log('Project API response:', response.status, response.statusText);

            if (response.ok) {
                this.project = await response.json();
                console.log('Project loaded:', this.project);
                this.displayProject();
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Project load error:', response.status, errorData);
                
                if (response.status === 401) {
                    this.showError('Please log in to view this project');
                } else if (response.status === 403) {
                    this.showError('You do not have permission to view this project');
                } else if (response.status === 404) {
                    this.showError('Project not found');
                } else {
                    this.showError('Failed to load project data');
                }
            }
        } catch (error) {
            console.error('Error loading project:', error);
            this.showError('Network error. Please try again.');
        }
    }

    displayProject() {
        if (!this.project) return;

        // Update project title
        const titleElement = document.getElementById('projectTitle');
        if (titleElement) {
            titleElement.textContent = this.project.title || 'Untitled Project';
        }

        // Update project date
        const dateElement = document.getElementById('projectDate');
        if (dateElement && this.project.updated_at) {
            const date = new Date(this.project.updated_at);
            dateElement.textContent = date.toLocaleDateString();
        }

        // Update whiteboard count
        const countElement = document.getElementById('whiteboardCount');
        if (countElement) {
            const count = this.project.whiteboards ? this.project.whiteboards.length : 0;
            countElement.textContent = `${count} whiteboard${count !== 1 ? 's' : ''}`;
        }

        // Display whiteboards
        this.displayWhiteboards();

        // Display exports
        this.displayExports();
    }

    displayWhiteboards() {
        const container = document.getElementById('whiteboardsContainer');
        if (!container || !this.project.whiteboards) return;

        container.innerHTML = '';

        if (this.project.whiteboards.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-images"></i>
                    <p>No whiteboards found</p>
                </div>
            `;
            return;
        }

        this.project.whiteboards.forEach(whiteboard => {
            const whiteboardCard = document.createElement('div');
            whiteboardCard.className = 'whiteboard-card';
            
            const status = whiteboard.processing_status || 'pending';
            const statusIcon = {
                'pending': 'fas fa-clock',
                'processing': 'fas fa-spinner fa-spin',
                'completed': 'fas fa-check-circle',
                'error': 'fas fa-exclamation-circle'
            }[status] || 'fas fa-question-circle';

            whiteboardCard.innerHTML = `
                <div class="whiteboard-preview">
                    <img src="/api/whiteboard/image/${whiteboard.id}" 
                         alt="Whiteboard" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="whiteboard-placeholder" style="display: none;">
                        <i class="fas fa-image"></i>
                        <span>Image not available</span>
                    </div>
                </div>
                <div class="whiteboard-info">
                    <h4>${whiteboard.filename || 'Unnamed'}</h4>
                    <div class="whiteboard-meta">
                        <span class="status ${status}">
                            <i class="${statusIcon}"></i>
                            ${status.charAt(0).toUpperCase() + status.slice(1)}
                        </span>
                        ${whiteboard.confidence_score ? `<span class="confidence">${Math.round(whiteboard.confidence_score * 100)}% confidence</span>` : ''}
                    </div>
                    ${whiteboard.processing_status === 'completed' && whiteboard.structured_content ? 
                        `<button class="btn btn-sm btn-primary" onclick="previewApp.viewWhiteboardContent('${whiteboard.id}')">
                            <i class="fas fa-eye"></i> View Content
                        </button>` : ''
                    }
                </div>
            `;

            container.appendChild(whiteboardCard);
        });
    }

    displayExports() {
        const container = document.getElementById('exportsContainer');
        if (!container || !this.project.exports) return;

        container.innerHTML = '';

        if (this.project.exports.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-export"></i>
                    <p>No exports generated</p>
                    <button class="btn btn-primary" onclick="previewApp.createExport()">
                        <i class="fas fa-plus"></i> Create Export
                    </button>
                </div>
            `;
            return;
        }

        this.project.exports.forEach(exportItem => {
            const exportCard = document.createElement('div');
            exportCard.className = 'export-card';
            
            const formatIcon = {
                'markdown': 'fab fa-markdown',
                'pptx': 'fas fa-file-powerpoint',
                'json': 'fas fa-code',
                'notion': 'fab fa-notion',
                'confluence': 'fas fa-confluence'
            }[exportItem.format] || 'fas fa-file';

            exportCard.innerHTML = `
                <div class="export-info">
                    <div class="export-icon">
                        <i class="${formatIcon}"></i>
                    </div>
                    <div class="export-details">
                        <h4>${exportItem.format.toUpperCase()}</h4>
                        <p>Created: ${new Date(exportItem.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
                <div class="export-actions">
                    <button class="btn btn-sm btn-outline" onclick="previewApp.downloadExport('${exportItem.id}')">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>
            `;

            container.appendChild(exportCard);
        });
    }

    viewWhiteboardContent(whiteboardId) {
        const whiteboard = this.project.whiteboards.find(wb => wb.id === whiteboardId);
        if (!whiteboard) return;

        // Show content in a modal
        const content = whiteboard.structured_content || {};
        let modalContent = '<div class="whiteboard-content">';
        
        if (content.sections && content.sections.length > 0) {
            modalContent += '<h3>Sections</h3>';
            content.sections.forEach(section => {
                modalContent += `<div class="content-section">
                    <h4>${section.heading || 'Untitled Section'}</h4>
                    <p>${section.content || ''}</p>
                </div>`;
            });
        }

        if (content.action_items && content.action_items.length > 0) {
            modalContent += '<h3>Action Items</h3><ul>';
            content.action_items.forEach(item => {
                modalContent += `<li>${item.task || item}</li>`;
            });
            modalContent += '</ul>';
        }

        modalContent += '</div>';

        this.showModal('Whiteboard Content', modalContent);
    }

    createExport() {
        // Redirect to main page with export modal
        window.location.href = '/?export=' + this.projectId;
    }

    downloadExport(exportId) {
        const url = `/api/export/download/${exportId}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    showError(message) {
        const container = document.querySelector('.preview-container');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h2>Error</h2>
                    <p>${message}</p>
                    <div class="error-actions">
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            <i class="fas fa-refresh"></i> Retry
                        </button>
                        <button class="btn btn-outline" onclick="window.location.href='/'">
                            <i class="fas fa-home"></i> Go Home
                        </button>
                    </div>
                </div>
            `;
        }
    }

    showModal(title, content) {
        // Create or update modal
        let modal = document.getElementById('previewModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'previewModal';
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <h3 id="previewModalTitle"></h3>
                        <button class="btn btn-ghost btn-sm" onclick="previewApp.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body" id="previewModalBody"></div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        document.getElementById('previewModalTitle').textContent = title;
        document.getElementById('previewModalBody').innerHTML = content;
        modal.style.display = 'flex';
    }

    closeModal() {
        const modal = document.getElementById('previewModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    setupEventListeners() {
        // Add any additional event listeners here
    }
}

// Global functions
function goHome() {
    window.location.href = '/';
}

function toggleTheme() {
    document.body.classList.toggle('theme-dark');
    document.body.classList.toggle('theme-light');
    
    const icon = document.querySelector('.theme-toggle-icon');
    if (document.body.classList.contains('theme-dark')) {
        icon.className = 'fas fa-sun theme-toggle-icon';
        localStorage.setItem('theme', 'dark');
    } else {
        icon.className = 'fas fa-moon theme-toggle-icon';
        localStorage.setItem('theme', 'light');
    }
}

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = `theme-${savedTheme} preview-page`;
    
    const icon = document.querySelector('.theme-toggle-icon');
    if (savedTheme === 'dark') {
        icon.className = 'fas fa-sun theme-toggle-icon';
    }
});

// Global variable to store the app instance
let previewApp = null;
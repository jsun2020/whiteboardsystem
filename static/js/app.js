// Main application class
class WhiteboardScribe {
    constructor() {
        this.currentProject = null;
        this.currentWhiteboards = [];
        this.eventSource = null;
        this.uploadQueue = [];
        this.isProcessing = false;
    }

    static init() {
        if (!window.app) {
            window.app = new WhiteboardScribe();
            window.app.initialize();
        }
    }

    initialize() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.restoreTheme();
        this.initializeI18n();
    }

    initializeI18n() {
        // Listen for language change events
        document.addEventListener('languageChanged', (event) => {
            // Update dynamic content that may not have been translated by the i18n system
            this.updateDynamicContent();
        });
    }

    updateDynamicContent() {
        // Update any dynamically generated content with current language
        // This method can be called when language changes
        if (window.i18n) {
            // Update progress text if processing
            const progressText = document.getElementById('progressText');
            if (progressText && progressText.textContent.includes('Preparing')) {
                progressText.textContent = window.i18n.t('processing.preparing');
            }
        }
    }

    setupEventListeners() {
        // File input change
        document.getElementById('fileInput')?.addEventListener('change', (e) => {
            requireAuth(() => {
                this.handleFileSelect(e);
            });
        });

        // Upload zone click protection
        document.getElementById('uploadZone')?.addEventListener('click', (e) => {
            // Check if user is authenticated before allowing file selection
            if (!window.authManager.isAuthenticated()) {
                e.preventDefault();
                e.stopPropagation();
                showLoginModal();
                return false;
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'v':
                        this.handlePaste(e);
                        break;
                    case 'e':
                        e.preventDefault();
                        this.showExportModal();
                        break;
                    case 's':
                        e.preventDefault();
                        this.saveProject();
                        break;
                }
            }
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    async handleFileSelect(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        // Validate files
        const validFiles = [];
        for (const file of files) {
            if (this.validateFile(file)) {
                validFiles.push(file);
            }
        }

        if (validFiles.length === 0) {
            showToast('No valid image files selected', 'error');
            return;
        }

        if (validFiles.length > 5) {
            showToast('Maximum 5 images allowed per batch', 'warning');
            validFiles.splice(5);
        }

        await this.uploadFiles(validFiles);
    }

    validateFile(file) {
        // Check file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            showToast(`File ${file.name} is too large. Maximum size is 10MB.`, 'error');
            return false;
        }

        // Check file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heic'];
        if (!allowedTypes.includes(file.type)) {
            showToast(`File ${file.name} has unsupported format.`, 'error');
            return false;
        }

        return true;
    }

    async uploadFiles(files) {
        try {
            this.showProcessingSection();
            this.updateProgress(0, 'Preparing upload...');

            const formData = new FormData();
            files.forEach(file => formData.append('images', file));

            // Add project ID if exists
            if (this.currentProject) {
                formData.append('project_id', this.currentProject.id);
            }

            const response = await fetch('/api/upload/batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Upload failed');
            }

            this.currentProject = { id: result.project_id };
            this.currentWhiteboards = result.results.filter(r => r.success);

            showToast(`Successfully uploaded ${result.uploaded_count} images`, 'success');

            // Start processing
            await this.startProcessing();

        } catch (error) {
            console.error('Upload failed:', error);
            showToast(error.message || 'Upload failed', 'error');
            this.hideProcessingSection();
        }
    }

    async startProcessing() {
        this.isProcessing = true;
        this.updateProgress(25, 'Analyzing whiteboards...');

        try {
            // Process each whiteboard
            for (let i = 0; i < this.currentWhiteboards.length; i++) {
                const whiteboard = this.currentWhiteboards[i];
                const progress = 25 + (i / this.currentWhiteboards.length) * 50;
                
                this.updateProgress(progress, `Analyzing whiteboard ${i + 1}...`);

                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ whiteboard_id: whiteboard.whiteboard_id })
                });

                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || 'Analysis failed');
                }

                // Update whiteboard with results
                whiteboard.structured_content = result.structured_content;
                whiteboard.confidence_score = result.confidence_score;
            }

            this.updateProgress(100, 'Analysis complete!');
            
            // Show results after a brief delay
            setTimeout(() => {
                this.showResults();
            }, 1000);

        } catch (error) {
            console.error('Processing failed:', error);
            showToast(error.message || 'Processing failed', 'error');
            this.hideProcessingSection();
        }
    }

    showProcessingSection() {
        hideElement('welcomeSection');
        showElement('processingSection');
    }

    hideProcessingSection() {
        showElement('welcomeSection');
        hideElement('processingSection');
        this.isProcessing = false;
    }

    updateProgress(percent, message) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressPercent = document.getElementById('progressPercent');

        if (progressFill) progressFill.style.width = `${percent}%`;
        if (progressText) progressText.textContent = message;
        if (progressPercent) progressPercent.textContent = `${Math.round(percent)}%`;

        // Update step indicators
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            const stepProgress = (index + 1) * 25;
            if (percent >= stepProgress) {
                step.classList.add('active');
                step.classList.add('completed');
            } else if (percent >= stepProgress - 25) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }

    showResults() {
        hideElement('processingSection');
        showElement('resultsSection');

        // Update results header
        this.updateResultsHeader();
        
        // Load content into panels
        this.loadResultsContent();
        
        // Default to structured view
        this.switchTab('structured');
    }

    updateResultsHeader() {
        let sectionsCount = 0;
        let actionItemsCount = 0;
        let tablesCount = 0;
        let totalConfidence = 0;

        this.currentWhiteboards.forEach(wb => {
            if (wb.structured_content) {
                sectionsCount += wb.structured_content.sections?.length || 0;
                actionItemsCount += wb.structured_content.action_items?.length || 0;
                tablesCount += wb.structured_content.tables?.length || 0;
                totalConfidence += wb.confidence_score || 0;
            }
        });

        const avgConfidence = this.currentWhiteboards.length > 0 
            ? Math.round(totalConfidence / this.currentWhiteboards.length * 100) 
            : 0;

        document.getElementById('sectionsCount').textContent = `${sectionsCount} sections`;
        document.getElementById('actionItemsCount').textContent = `${actionItemsCount} action items`;
        document.getElementById('tablesCount').textContent = `${tablesCount} tables`;
        document.getElementById('confidenceScore').textContent = `${avgConfidence}% confidence`;
    }

    loadResultsContent() {
        // Load images carousel
        const imagesCarousel = document.getElementById('imagesCarousel');
        if (imagesCarousel) {
            imagesCarousel.innerHTML = '';
            this.currentWhiteboards.forEach((wb, index) => {
                const imageCard = document.createElement('div');
                imageCard.className = 'image-card';
                imageCard.innerHTML = `
                    <img src="/api/whiteboard/image/${wb.whiteboard_id}" alt="Whiteboard ${index + 1}">
                    <div class="image-info">
                        <span>Whiteboard ${index + 1}</span>
                        <span class="confidence">${Math.round((wb.confidence_score || 0) * 100)}%</span>
                    </div>
                `;
                imagesCarousel.appendChild(imageCard);
            });
        }

        // Load structured content by default
        this.loadStructuredContent();
    }

    loadStructuredContent() {
        const contentPanel = document.getElementById('contentPanel');
        if (!contentPanel) return;

        let html = '';
        this.currentWhiteboards.forEach((wb, index) => {
            if (wb.structured_content) {
                const content = wb.structured_content;
                
                if (this.currentWhiteboards.length > 1) {
                    html += `<div class="whiteboard-section"><h2>Whiteboard ${index + 1}</h2>`;
                }

                // Title
                if (content.title) {
                    html += `<h1>${content.title}</h1>`;
                }

                // Sections
                if (content.sections) {
                    content.sections.forEach(section => {
                        html += `
                            <div class="content-section">
                                <h3>${section.heading || 'Section'}</h3>
                                ${section.content ? `<div class="section-content">${section.content}</div>` : ''}
                            </div>
                        `;
                    });
                }

                // Action Items
                if (content.action_items && content.action_items.length > 0) {
                    html += '<div class="action-items-section"><h3>Action Items</h3><ul class="action-items-list">';
                    content.action_items.forEach(item => {
                        const priorityClass = item.priority || 'medium';
                        const assignee = item.assignee ? ` (@${item.assignee})` : '';
                        html += `<li class="action-item ${priorityClass}">
                            <span class="priority-indicator"></span>
                            ${item.task}${assignee}
                        </li>`;
                    });
                    html += '</ul></div>';
                }

                // Key Points
                if (content.key_points && content.key_points.length > 0) {
                    html += '<div class="key-points-section"><h3>Key Points</h3><ul class="key-points-list">';
                    content.key_points.forEach(point => {
                        html += `<li>${point}</li>`;
                    });
                    html += '</ul></div>';
                }

                // Tables
                if (content.tables && content.tables.length > 0) {
                    content.tables.forEach(table => {
                        html += `<div class="table-section">
                            <h3>${table.title || 'Table'}</h3>
                            <div class="table-container">
                                <table>`;
                        
                        if (table.headers) {
                            html += '<thead><tr>';
                            table.headers.forEach(header => {
                                html += `<th>${header}</th>`;
                            });
                            html += '</tr></thead>';
                        }

                        if (table.rows) {
                            html += '<tbody>';
                            table.rows.forEach(row => {
                                html += '<tr>';
                                row.forEach(cell => {
                                    html += `<td>${cell}</td>`;
                                });
                                html += '</tr>';
                            });
                            html += '</tbody>';
                        }

                        html += '</table></div></div>';
                    });
                }

                if (this.currentWhiteboards.length > 1) {
                    html += '</div>';
                }
            }
        });

        contentPanel.innerHTML = html;
    }

    switchTab(tabName) {
        // Remove active from all tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active to clicked tab
        event.target.classList.add('active');

        // Load appropriate content
        switch(tabName) {
            case 'structured':
                this.loadStructuredContent();
                break;
            case 'raw':
                this.loadRawContent();
                break;
            case 'json':
                this.loadJsonContent();
                break;
        }
    }

    loadRawContent() {
        const contentPanel = document.getElementById('contentPanel');
        let text = '';
        
        this.currentWhiteboards.forEach((wb, index) => {
            if (wb.structured_content && wb.structured_content.raw_text) {
                if (this.currentWhiteboards.length > 1) {
                    text += `\n=== Whiteboard ${index + 1} ===\n\n`;
                }
                text += wb.structured_content.raw_text + '\n\n';
            }
        });

        contentPanel.innerHTML = `<pre class="raw-text">${text}</pre>`;
    }

    loadJsonContent() {
        const contentPanel = document.getElementById('contentPanel');
        const jsonData = this.currentWhiteboards.map(wb => wb.structured_content).filter(c => c);
        contentPanel.innerHTML = `<pre class="json-content">${JSON.stringify(jsonData, null, 2)}</pre>`;
    }

    async saveProject() {
        if (!this.currentProject) return;

        try {
            const title = prompt('Enter project title:', 'Whiteboard Analysis');
            if (!title) return;

            const response = await fetch(`/api/projects/${this.currentProject.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, status: 'completed' })
            });

            if (response.ok) {
                showToast('Project saved successfully', 'success');
                this.currentProject.title = title;
                document.getElementById('projectTitle').textContent = title;
            } else {
                throw new Error('Failed to save project');
            }
        } catch (error) {
            showToast('Failed to save project', 'error');
        }
    }

    async shareResults() {
        if (!this.currentProject) return;

        try {
            const response = await fetch('/api/share', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: this.currentProject.id })
            });

            const result = await response.json();
            
            if (response.ok) {
                const shareUrl = `${window.location.origin}/share/${result.share_token}`;
                
                // Show share modal
                this.showModal('Share Results', `
                    <div class="share-content">
                        <p>Your whiteboard analysis has been shared. Anyone with this link can view the results:</p>
                        <div class="share-url-container">
                            <input type="text" value="${shareUrl}" readonly id="shareUrl">
                            <button class="btn btn-primary" onclick="copyShareUrl()">
                                <i class="fas fa-copy"></i> Copy
                            </button>
                        </div>
                        <p class="share-note">
                            <i class="fas fa-info-circle"></i>
                            This link will remain active until you delete the project.
                        </p>
                    </div>
                `);
            } else {
                throw new Error(result.error || 'Failed to create share link');
            }
        } catch (error) {
            showToast('Failed to create share link', 'error');
        }
    }

    cancelProcessing() {
        if (this.isProcessing) {
            this.isProcessing = false;
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            this.hideProcessingSection();
            showToast('Processing cancelled', 'info');
        }
    }

    handlePaste(e) {
        const items = e.clipboardData?.items;
        if (!items) return;

        const files = [];
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                files.push(item.getAsFile());
            }
        }

        if (files.length > 0) {
            e.preventDefault();
            this.uploadFiles(files);
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data.stats);
                this.updateRecentProjects(data.recent_projects);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    updateDashboardStats(stats) {
        document.getElementById('totalProjects').textContent = stats.total_projects || 0;
        document.getElementById('totalWhiteboards').textContent = stats.total_whiteboards || 0;
        document.getElementById('totalExports').textContent = stats.total_exports || 0;
        document.getElementById('processingRate').textContent = Math.round(stats.processing_rate || 0) + '%';
    }

    updateRecentProjects(projects) {
        const container = document.getElementById('recentProjectsList');
        if (!container || !projects) return;

        container.innerHTML = '';
        projects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card';
            projectCard.innerHTML = `
                <div class="project-info">
                    <h4>${project.title || 'Untitled Project'}</h4>
                    <p>${formatDate(project.updated_at)}</p>
                </div>
                <div class="project-stats">
                    <span>${project.whiteboard_count} whiteboards</span>
                </div>
            `;
            projectCard.addEventListener('click', () => {
                window.location.href = `/preview/${project.id}`;
            });
            container.appendChild(projectCard);
        });
    }

    showModal(title, content, footer = '') {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = content;
        document.getElementById('modalFooter').innerHTML = footer;
        showElement('modalOverlay');
    }

    closeModal() {
        hideElement('modalOverlay');
    }

    restoreTheme() {
        const savedTheme = localStorage.getItem('whiteboardTheme') || 'light';
        document.body.className = `theme-${savedTheme}`;
        
        const icon = document.querySelector('.theme-toggle-icon');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    setTheme(theme) {
        document.body.className = `theme-${theme}`;
        localStorage.setItem('whiteboardTheme', theme);
        
        const icon = document.querySelector('.theme-toggle-icon');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// Global functions for UI interactions
// Authentication check helper
function requireAuth(callback) {
    if (!window.authManager.isAuthenticated()) {
        showLoginModal();
        return false;
    }
    return callback();
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const uploadZone = document.getElementById('uploadZone');
    uploadZone.classList.remove('drag-over');
    
    requireAuth(() => {
        const files = Array.from(e.dataTransfer.files);
        const imageFiles = files.filter(f => f.type.startsWith('image/'));
        
        if (imageFiles.length > 0) {
            window.app.uploadFiles(imageFiles);
        }
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('uploadZone').classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('uploadZone').classList.remove('drag-over');
}

function handleFileSelect(e) {
    requireAuth(() => {
        window.app.handleFileSelect(e);
    });
}

function captureFromCamera() {
    requireAuth(() => {
        // For now, just trigger file input with camera capture
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'camera';
        input.onchange = (e) => window.app.handleFileSelect(e);
        input.click();
    });
}

function loadDemo() {
    requireAuth(() => {
        showToast('Demo feature coming soon!', 'info');
        // TODO: Implement demo functionality
    });
}

function createNewProject() {
    requireAuth(() => {
        // Reset current project and show welcome section for new upload
        window.app.currentProject = null;
        window.app.currentWhiteboards = [];
        
        // Show welcome section (upload area)
        hideElement('dashboardSection');
        hideElement('resultsSection');
        hideElement('processingSection');
        showElement('welcomeSection');
        
        // Scroll to top
        window.scrollTo(0, 0);
    });
}

function browseFiles() {
    requireAuth(() => {
        document.getElementById('fileInput').click();
    });
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    window.app.setTheme(newTheme);
}

function showDashboard() {
    requireAuth(() => {
        hideElement('welcomeSection');
        hideElement('processingSection');
        hideElement('resultsSection');
        showElement('dashboardSection');
        window.app.loadDashboardData();
    });
}

function hideDashboard() {
    hideElement('dashboardSection');
    showElement('welcomeSection');
}

function switchTab(tabName) {
    window.app.switchTab(tabName);
}

function cancelProcessing() {
    window.app.cancelProcessing();
}

function copyShareUrl() {
    const input = document.getElementById('shareUrl');
    input.select();
    document.execCommand('copy');
    showToast('Share URL copied to clipboard', 'success');
}

function toggleEditMode() {
    showToast('Edit mode coming soon!', 'info');
}

function copyContent() {
    const contentPanel = document.getElementById('contentPanel');
    const text = contentPanel.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Content copied to clipboard', 'success');
    });
}

function toggleRegionOverlay() {
    showToast('Region overlay coming soon!', 'info');
}

function zoomImage() {
    showToast('Image zoom coming soon!', 'info');
}

function saveProject() {
    window.app.saveProject();
}

function shareResults() {
    window.app.shareResults();
}

function closeModal() {
    window.app.closeModal();
}

// Utility functions
function showElement(id) {
    const element = document.getElementById(id);
    if (element) element.style.display = 'block';
}

function hideElement(id) {
    const element = document.getElementById(id);
    if (element) element.style.display = 'none';
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}
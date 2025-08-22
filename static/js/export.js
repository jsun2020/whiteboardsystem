// Export functionality
class ExportManager {
    constructor() {
        this.exportQueue = [];
        this.isExporting = false;
    }

    async exportAs(format, projectId = null, options = {}) {
        if (!projectId && !window.app?.currentProject) {
            showToast('No project to export', 'error');
            return;
        }

        const pid = projectId || window.app.currentProject.id;
        
        try {
            this.showExportLoading(format);
            
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...window.authManager.getAuthHeaders()
                },
                body: JSON.stringify({
                    project_id: pid,
                    format: format,
                    options: options
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Export failed');
            }

            // Download the file
            await this.downloadExport(result.export_id, result.filename);
            
            showToast(`${format.toUpperCase()} export completed successfully`, 'success');

        } catch (error) {
            console.error('Export failed:', error);
            showToast(error.message || 'Export failed', 'error');
        } finally {
            this.hideExportLoading();
        }
    }

    async downloadExport(exportId, filename) {
        try {
            const response = await fetch(`/api/export/${exportId}/download`, {
                headers: window.authManager.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error('Download failed');
            }

            const blob = await response.blob();
            this.downloadBlob(blob, filename);

        } catch (error) {
            throw new Error(`Download failed: ${error.message}`);
        }
    }

    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showExportLoading(format) {
        const btn = document.querySelector(`[onclick*="exportAs('${format}')"]`);
        if (btn) {
            btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Exporting...`;
            btn.disabled = true;
        }
        
        showElement('loadingOverlay');
    }

    hideExportLoading() {
        // Reset all export buttons
        const exportButtons = document.querySelectorAll('[onclick*="exportAs"]');
        exportButtons.forEach(btn => {
            btn.disabled = false;
            // Restore original content based on format
            const format = btn.onclick.toString().match(/exportAs\('(\w+)'\)/)?.[1];
            if (format) {
                btn.innerHTML = this.getButtonContent(format);
            }
        });

        hideElement('loadingOverlay');
    }

    getButtonContent(format) {
        const contents = {
            markdown: '<i class="fab fa-markdown"></i><span>Markdown</span>',
            pptx: '<i class="fas fa-file-powerpoint"></i><span>PowerPoint</span>',
            mindmap: '<i class="fas fa-project-diagram"></i><span>Mind Map</span>',
            notion: '<i class="fas fa-sticky-note"></i><span>Notion</span>',
            confluence: '<i class="fas fa-confluence"></i><span>Confluence</span>'
        };
        return contents[format] || `<span>${format}</span>`;
    }

    async showExportOptions(format) {
        try {
            const response = await fetch('/api/export/formats', {
                headers: window.authManager.getAuthHeaders()
            });
            const data = await response.json();
            
            const formatInfo = data.formats.find(f => f.id === format);
            if (!formatInfo) {
                this.exportAs(format);
                return;
            }

            const modalContent = this.generateOptionsForm(formatInfo);
            
            window.app.showModal(
                `Export Options - ${formatInfo.name}`,
                modalContent,
                `<button class="btn btn-outline" onclick="closeModal()">Cancel</button>
                 <button class="btn btn-primary" onclick="submitExportOptions('${format}')">Export</button>`
            );

        } catch (error) {
            console.error('Failed to load export options:', error);
            this.exportAs(format); // Fallback to default export
        }
    }

    generateOptionsForm(formatInfo) {
        let html = `
            <div class="export-options-form">
                <p class="format-description">${formatInfo.description}</p>
                <form id="exportOptionsForm">
        `;

        if (formatInfo.options && formatInfo.options.length > 0) {
            formatInfo.options.forEach(option => {
                html += `<div class="form-group">`;
                html += `<label for="${option.key}">${this.formatLabel(option.key)}</label>`;
                
                switch (option.type) {
                    case 'boolean':
                        html += `
                            <div class="checkbox-container">
                                <input type="checkbox" id="${option.key}" name="${option.key}" 
                                       ${option.default ? 'checked' : ''}>
                                <label for="${option.key}" class="checkbox-label">
                                    ${this.getOptionDescription(option.key)}
                                </label>
                            </div>
                        `;
                        break;
                    
                    case 'select':
                        html += `<select id="${option.key}" name="${option.key}">`;
                        option.options.forEach(opt => {
                            const selected = opt === option.default ? 'selected' : '';
                            html += `<option value="${opt}" ${selected}>${this.formatLabel(opt)}</option>`;
                        });
                        html += `</select>`;
                        break;
                    
                    case 'number':
                        html += `
                            <input type="number" id="${option.key}" name="${option.key}" 
                                   value="${option.default || ''}" min="1" max="10">
                        `;
                        break;
                    
                    case 'string':
                        html += `
                            <input type="text" id="${option.key}" name="${option.key}" 
                                   value="${option.default || ''}" placeholder="Enter ${this.formatLabel(option.key).toLowerCase()}">
                        `;
                        break;
                }
                
                html += `</div>`;
            });
        }

        html += `
                </form>
            </div>
        `;

        return html;
    }

    formatLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getOptionDescription(key) {
        const descriptions = {
            include_images: 'Include image references in export',
            include_diagrams: 'Include diagram descriptions',
            include_notes: 'Include speaker notes',
            include_properties: 'Include page properties',
            include_macros: 'Include Confluence macros',
            include_colors: 'Use colors for different sections'
        };
        return descriptions[key] || this.formatLabel(key);
    }

    getFormData() {
        const form = document.getElementById('exportOptionsForm');
        if (!form) return {};

        const formData = new FormData(form);
        const options = {};

        for (let [key, value] of formData.entries()) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input.type === 'checkbox') {
                options[key] = input.checked;
            } else if (input.type === 'number') {
                options[key] = parseInt(value) || 1;
            } else {
                options[key] = value;
            }
        }

        // Handle unchecked checkboxes
        form.querySelectorAll('input[type="checkbox"]:not(:checked)').forEach(input => {
            options[input.name] = false;
        });

        return options;
    }

    async batchExport(projectId, formats) {
        const results = [];
        
        for (const format of formats) {
            try {
                await this.exportAs(format, projectId);
                results.push({ format, success: true });
            } catch (error) {
                results.push({ format, success: false, error: error.message });
            }
        }

        return results;
    }

    async getProjectExports(projectId) {
        try {
            const response = await fetch(`/api/exports/${projectId}`, {
                headers: window.authManager.getAuthHeaders()
            });
            if (response.ok) {
                return await response.json();
            }
            return { exports: [] };
        } catch (error) {
            console.error('Failed to load exports:', error);
            return { exports: [] };
        }
    }

    async deleteExport(exportId) {
        try {
            const response = await fetch(`/api/export/${exportId}`, {
                method: 'DELETE',
                headers: window.authManager.getAuthHeaders()
            });

            if (response.ok) {
                showToast('Export deleted successfully', 'success');
                return true;
            } else {
                throw new Error('Failed to delete export');
            }
        } catch (error) {
            showToast(error.message || 'Failed to delete export', 'error');
            return false;
        }
    }
}

// Global export manager instance
window.exportManager = new ExportManager();

// Authentication check helper for exports
function requireAuthForExport(callback) {
    if (!window.authManager.isAuthenticated()) {
        showLoginModal();
        return false;
    }
    return callback();
}

// Global functions for export functionality
function exportAs(format, options = {}) {
    requireAuthForExport(() => {
        window.exportManager.exportAs(format, null, options);
    });
}

function exportWithOptions(format) {
    requireAuthForExport(() => {
        window.exportManager.showExportOptions(format);
    });
}

function submitExportOptions(format) {
    requireAuthForExport(() => {
        const options = window.exportManager.getFormData();
        window.exportManager.exportAs(format, null, options);
        closeModal();
    });
}

function exportProject(format, projectId = null) {
    requireAuthForExport(() => {
        window.exportManager.exportAs(format, projectId);
    });
}

function exportShared(format, projectId) {
    requireAuthForExport(() => {
        window.exportManager.exportAs(format, projectId);
    });
}

function exportActionItems() {
    requireAuthForExport(() => {
        if (!window.app?.currentProject) {
            showToast('No project data available', 'error');
            return;
        }

    // Create CSV content for action items
    let csvContent = "Task,Priority,Assignee,Category,Deadline\n";
    
    window.app.currentWhiteboards.forEach(wb => {
        if (wb.structured_content?.action_items) {
            wb.structured_content.action_items.forEach(item => {
                const task = `"${(item.task || '').replace(/"/g, '""')}"`;
                const priority = item.priority || 'medium';
                const assignee = item.assignee || '';
                const category = item.category || '';
                const deadline = item.deadline || '';
                
                csvContent += `${task},${priority},${assignee},${category},${deadline}\n`;
            });
        }
    });

        // Create and download CSV file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const filename = `action-items-${new Date().toISOString().split('T')[0]}.csv`;
        window.exportManager.downloadBlob(blob, filename);
        
        showToast('Action items exported to CSV', 'success');
    });
}

function generateNewExport() {
    const formats = ['markdown', 'pptx', 'mindmap', 'notion', 'confluence'];
    const format = prompt('Enter export format (markdown, pptx, mindmap, notion, confluence):');
    
    if (formats.includes(format)) {
        exportProject(format);
    } else if (format) {
        showToast('Invalid format. Please choose: markdown, pptx, mindmap, notion, or confluence', 'error');
    }
}

function downloadContent() {
    if (!window.app?.currentWhiteboards) {
        showToast('No content to download', 'error');
        return;
    }

    // Create simple text export
    let textContent = '';
    window.app.currentWhiteboards.forEach((wb, index) => {
        if (wb.structured_content) {
            if (window.app.currentWhiteboards.length > 1) {
                textContent += `=== Whiteboard ${index + 1} ===\n\n`;
            }
            
            if (wb.structured_content.title) {
                textContent += wb.structured_content.title + '\n\n';
            }
            
            if (wb.structured_content.raw_text) {
                textContent += wb.structured_content.raw_text + '\n\n';
            }
        }
    });

    const blob = new Blob([textContent], { type: 'text/plain' });
    const filename = `whiteboard-content-${new Date().toISOString().split('T')[0]}.txt`;
    window.exportManager.downloadBlob(blob, filename);
    
    showToast('Content downloaded as text file', 'success');
}
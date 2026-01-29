/**
 * Multiple File Upload Component
 * Provides consistent multiple file upload functionality across all forms
 */

// Prevent redeclaration
if (typeof MultipleFileUpload === 'undefined') {
    class MultipleFileUpload {
    constructor(options = {}) {
        this.containerId = options.containerId || 'file-upload-container';
        this.inputName = options.inputName || 'files';
        this.acceptedTypes = options.acceptedTypes || '.pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx';
        this.maxSize = options.maxSize || 50 * 1024 * 1024; // 50MB
        this.maxFiles = options.maxFiles || 10;
        this.allowedExtensions = options.allowedExtensions || ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'];
        this.required = options.required || false;
        this.label = options.label || 'Upload Files';
        this.helpText = options.helpText || 'Upload multiple files (PDF, JPG, PNG, DOC, DOCX, XLS, XLSX - Max 50MB each)';
        this.metadataProvider = null; // Optional hook to attach structured metadata per file
        this.container = null;
        
        this.allSelectedFiles = [];
        this.init();
    }
    
    init() {
        this.createContainer();
        this.bindEvents();
    }
    
    createContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID '${this.containerId}' not found`);
            return;
        }
        this.container = container;
        
        container.innerHTML = `
            <div class="form-group">
                <label>${this.label}${this.required ? ' <span class="required-star">*</span>' : ''}</label>
                <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                    <button type="button" id="add-files-btn-${this.containerId}" class="btn btn-primary" style="white-space: nowrap;">
                        <i class="fas fa-plus"></i> Add Files
                    </button>
                </div>
                <small>${this.helpText}</small>
                <div id="file-preview-${this.containerId}" style="margin-top: 10px;"></div>
                
                <!-- Hidden file input for actual file selection -->
                <input type="file" name="${this.inputName}" id="file-input-${this.containerId}" 
                       accept="${this.acceptedTypes}" multiple style="display: none;">
            </div>
        `;
    }
    
    bindEvents() {
        const button = document.getElementById(`add-files-btn-${this.containerId}`);
        const fileInput = document.getElementById(`file-input-${this.containerId}`);
        
        if (button && fileInput) {
            button.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
                // Reset the input value so the same file can be selected again
                e.target.value = '';
            });
        }
    }
    
    handleFileSelection(files) {
        const newFiles = Array.from(files);
        
        // Check if adding these files would exceed the maximum
        if (this.allSelectedFiles.length + newFiles.length > this.maxFiles) {
            alert(`Maximum ${this.maxFiles} files allowed. You currently have ${this.allSelectedFiles.length} files selected.`);
            return;
        }
        
        // Validate each file and collect valid ones
        const validFiles = [];
        const validationErrors = [];
        
        for (const file of newFiles) {
            if (this.validateFile(file)) {
                validFiles.push(file);
            } else {
                // Collect validation errors but continue processing other files
                const fileExtension = file.name.split('.').pop().toLowerCase();
                if (file.size > this.maxSize) {
                    validationErrors.push(`File "${file.name}" is too large. Maximum size is ${(this.maxSize / 1024 / 1024).toFixed(0)}MB.`);
                } else if (!this.allowedExtensions.includes(fileExtension)) {
                    validationErrors.push(`Invalid file type for "${file.name}". Allowed types: ${this.allowedExtensions.join(', ').toUpperCase()}`);
                }
            }
        }
        
        // Show validation errors if any
        if (validationErrors.length > 0) {
            for (const error of validationErrors) {
                alert(error);
            }
        }
        
        // Add valid files to the list
        if (validFiles.length > 0) {
            this.allSelectedFiles.push(...validFiles);
            this.updateFilePreview();
        }
    }

    // Allow consumers to attach a metadata provider that returns any serializable structure
    setMetadataProvider(fn) {
        if (typeof fn === 'function') {
            this.metadataProvider = fn;
        }
    }

    dispatchChangeEvent() {
        if (!this.container) return;
        const event = new CustomEvent('multipleFileUpload:changed', {
            detail: {
                containerId: this.containerId,
                files: [...this.allSelectedFiles],
            },
        });
        this.container.dispatchEvent(event);
    }
    
    validateFile(file) {
        // Check file size
        if (file.size > this.maxSize) {
            alert(`File "${file.name}" is too large. Maximum size is ${(this.maxSize / 1024 / 1024).toFixed(0)}MB.`);
            return false;
        }
        
        // Check file extension
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!this.allowedExtensions.includes(fileExtension)) {
            alert(`Invalid file type for "${file.name}". Allowed types: ${this.allowedExtensions.join(', ').toUpperCase()}`);
            return false;
        }
        
        return true;
    }
    
    updateFilePreview() {
        const preview = document.getElementById(`file-preview-${this.containerId}`);
        const button = document.getElementById(`add-files-btn-${this.containerId}`);
        
        if (!preview || !button) return;
        
        if (this.allSelectedFiles.length > 0) {
            // Update button text
            button.innerHTML = `<i class="fas fa-plus"></i> Add More Files (${this.allSelectedFiles.length}/${this.maxFiles})`;
            button.className = 'btn btn-success';
            
            // Create file list
            const fileList = document.createElement('div');
            fileList.style.cssText = 'background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; max-height: 200px; overflow-y: auto;';
            
            const header = document.createElement('div');
            header.style.cssText = 'font-weight: bold; margin-bottom: 8px; color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;';
            header.textContent = `Selected Files (${this.allSelectedFiles.length})`;
            fileList.appendChild(header);
            
            this.allSelectedFiles.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px; background: white; border-radius: 4px; margin-bottom: 5px; border: 1px solid #c3e6cb;';
                
                const fileInfo = document.createElement('div');
                fileInfo.style.cssText = 'display: flex; align-items: center; color: #333; font-size: 14px;';
                
                // Add file type icon
                const fileIcon = document.createElement('i');
                const extension = file.name.split('.').pop().toLowerCase();
                if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
                    fileIcon.className = 'fas fa-image';
                    fileIcon.style.cssText = 'color: #17a2b8; margin-right: 8px;';
                } else if (extension === 'pdf') {
                    fileIcon.className = 'fas fa-file-pdf';
                    fileIcon.style.cssText = 'color: #dc3545; margin-right: 8px;';
                } else if (['doc', 'docx'].includes(extension)) {
                    fileIcon.className = 'fas fa-file-word';
                    fileIcon.style.cssText = 'color: #007bff; margin-right: 8px;';
                } else if (['xls', 'xlsx'].includes(extension)) {
                    fileIcon.className = 'fas fa-file-excel';
                    fileIcon.style.cssText = 'color: #28a745; margin-right: 8px;';
                } else {
                    fileIcon.className = 'fas fa-file';
                    fileIcon.style.cssText = 'color: #6c757d; margin-right: 8px;';
                }
                
                const fileName = document.createElement('span');
                fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                
                fileInfo.appendChild(fileIcon);
                fileInfo.appendChild(fileName);
                
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                removeBtn.style.cssText = 'background: #dc3545; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 10px; display: flex; align-items: center; justify-content: center;';
                removeBtn.onclick = () => {
                    this.removeFile(index);
                };
                
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(removeBtn);
                fileList.appendChild(fileItem);
            });
            
            preview.innerHTML = '';
            preview.appendChild(fileList);
        } else {
            // Reset button when no files are selected
            button.innerHTML = '<i class="fas fa-plus"></i> Add Files';
            button.className = 'btn btn-primary';
            preview.innerHTML = '';
        }

        this.dispatchChangeEvent();
    }
    
    removeFile(indexToRemove) {
        this.allSelectedFiles.splice(indexToRemove, 1);
        this.updateFilePreview();
    }
    
    getFiles() {
        return this.allSelectedFiles;
    }
    
    clearFiles() {
        this.allSelectedFiles = [];
        this.updateFilePreview();
    }
    
    // Method to integrate with form submission
    prepareFormData(formData) {
        // Clear existing files from FormData
        formData.delete(this.inputName);
        
        // Add all selected files to FormData
        this.allSelectedFiles.forEach((file) => {
            formData.append(this.inputName, file);
        });

        // Attach optional metadata payload if provided
        if (typeof this.metadataProvider === 'function') {
            try {
                const metadata = this.metadataProvider(this.allSelectedFiles);
                if (metadata !== undefined) {
                    formData.set(`${this.inputName}_metadata`, JSON.stringify(metadata));
                }
            } catch (err) {
                console.warn('Could not attach upload metadata:', err);
            }
        }
        
        return formData;
    }
    }

    // Utility function to create a multiple file upload component
    function createMultipleFileUpload(options) {
        return new MultipleFileUpload(options);
    }

    // Auto-initialize components with data attributes
    document.addEventListener('DOMContentLoaded', function() {
        const containers = document.querySelectorAll('[data-multiple-file-upload]');
        containers.forEach(container => {
            const options = {
                containerId: container.id,
                inputName: container.dataset.inputName || 'files',
                acceptedTypes: container.dataset.acceptedTypes || '.pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx',
                maxSize: parseInt(container.dataset.maxSize) || 50 * 1024 * 1024,
                maxFiles: parseInt(container.dataset.maxFiles) || 10,
                required: container.dataset.required === 'true',
                label: container.dataset.label || 'Upload Files',
                helpText: container.dataset.helpText || 'Upload multiple files (PDF, JPG, PNG, DOC, DOCX, XLS, XLSX - Max 50MB each)'
            };
            
            const component = new MultipleFileUpload(options);
            // Store the component on the container for easy access
            container.uploadComponent = component;
        });
    });
}

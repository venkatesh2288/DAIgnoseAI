// Upload functionality for DAIgnoseAI

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileType = document.getElementById('fileType');
    const submitBtn = document.getElementById('submitBtn');
    const uploadForm = document.getElementById('uploadForm');
    const uploadProgress = document.getElementById('uploadProgress');

    // Drag and drop functionality
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Form submission handler
    uploadForm.addEventListener('submit', function(e) {
        if (!fileInput.files.length) {
            e.preventDefault();
            showToast('Please select a file to upload', 'warning');
            return;
        }

        // Show progress
        if (uploadProgress) {
            uploadProgress.style.display = 'block';
        }
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
        
        // Let the form submit normally - don't prevent default
    });

    function handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'text/plain', 'image/png', 'image/jpeg', 'image/gif', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const allowedExtensions = ['pdf', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'docx'];
        
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            showToast('Invalid file type. Please upload PDF, TXT, DOCX, or image files.', 'error');
            resetFileInput();
            return;
        }

        // Validate file size (16MB max)
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            showToast('File too large. Maximum size is 16MB.', 'error');
            resetFileInput();
            return;
        }

        // Display file info
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileType.textContent = file.type || 'Unknown';
        
        fileInfo.style.display = 'block';
        submitBtn.disabled = false;

        // Update upload area appearance
        updateUploadAreaWithFile(file);
    }

    function updateUploadAreaWithFile(file) {
        const uploadContent = uploadArea.querySelector('.upload-content');
        const icon = getFileIcon(file.name);
        
        uploadContent.innerHTML = `
            <i class="${icon} fa-3x text-success mb-3"></i>
            <h5 class="text-success">File Selected</h5>
            <p class="text-muted">${file.name}</p>
            <p class="small text-muted">Click to select a different file</p>
        `;
    }

    function getFileIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'pdf': 'fas fa-file-pdf',
            'txt': 'fas fa-file-alt',
            'docx': 'fas fa-file-word',
            'png': 'fas fa-file-image',
            'jpg': 'fas fa-file-image',
            'jpeg': 'fas fa-file-image',
            'gif': 'fas fa-file-image'
        };
        return iconMap[extension] || 'fas fa-file';
    }

    function resetFileInput() {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        submitBtn.disabled = true;
        
        // Reset upload area
        const uploadContent = uploadArea.querySelector('.upload-content');
        uploadContent.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-primary mb-3"></i>
            <h5 class="text-primary">Drag & Drop your file here</h5>
            <p class="text-muted">or click to browse</p>
            <button type="button" class="btn btn-outline-primary" onclick="document.getElementById('file').click()">
                <i class="fas fa-folder-open me-2"></i>Choose File
            </button>
        `;
    }

    function simulateProgress() {
        const progressBar = uploadProgress.querySelector('.progress-bar');
        let progress = 0;
        
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(interval);
            }
            progressBar.style.width = progress + '%';
        }, 300);
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function showToast(message, type = 'info') {
        // Use the global toast function if available
        if (window.DiagnAIzerUtils && window.DiagnAIzerUtils.showToast) {
            window.DiagnAIzerUtils.showToast(message, type);
        } else {
            // Fallback alert
            alert(message);
        }
    }

    // Paste file functionality
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData.items;
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                if (file) {
                    // Create a DataTransfer object to set the files
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                    handleFileSelect(file);
                    showToast('Image pasted from clipboard', 'success');
                }
                break;
            }
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + O to open file dialog
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            fileInput.click();
        }
        
        // Escape to reset
        if (e.key === 'Escape' && fileInput.files.length > 0) {
            resetFileInput();
        }
    });

    // Auto-retry on network error
    let retryCount = 0;
    const maxRetries = 3;

    uploadForm.addEventListener('submit', function(e) {
        // This will run after the initial submit handler
        setTimeout(() => {
            // Check if the form is still being processed
            if (submitBtn.disabled && retryCount < maxRetries) {
                // Implement retry logic if needed
                console.log('Upload in progress...');
            }
        }, 30000); // 30 second timeout
    });

    // File validation preview
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            
            // Show file preview for images
            if (file.type.startsWith('image/')) {
                showImagePreview(file);
            }
        }
    });

    function showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewContainer = document.createElement('div');
            previewContainer.className = 'mt-3 text-center';
            previewContainer.innerHTML = `
                <h6>Image Preview:</h6>
                <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
            `;
            
            // Remove existing preview
            const existingPreview = document.querySelector('.image-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            
            previewContainer.className += ' image-preview';
            fileInfo.appendChild(previewContainer);
        };
        reader.readAsDataURL(file);
    }
});

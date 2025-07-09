document.addEventListener('DOMContentLoaded', function () {
    initializeFAQs();
});

document.getElementById('othersTag').addEventListener('change', function () {
    const customTagsSection = document.getElementById('customTagsSection');
    const customTagsInput = document.getElementById('customTagsInput');

    if (this.checked) {
        customTagsSection.style.display = 'block';
        customTagsInput.focus();
    } else {
        customTagsSection.style.display = 'none';
        customTagsInput.value = '';
        document.getElementById('customTagsHidden').value = '';
    }
});

document.getElementById('editOthersTag').addEventListener('change', function () {
    const customTagsSection = document.getElementById('editCustomTagsSection');
    const customTagsInput = document.getElementById('editCustomTagsInput');

    if (this.checked) {
        customTagsSection.style.display = 'block';
        customTagsInput.focus();
    } else {
        customTagsSection.style.display = 'none';
        customTagsInput.value = '';
        document.getElementById('editCustomTagsHidden').value = '';
    }
});

// Handle custom tags input for Add FAQ
document.getElementById('customTagsInput').addEventListener('input', function () {
    document.getElementById('customTagsHidden').value = this.value;
});

// Handle custom tags input for Edit FAQ
document.getElementById('editCustomTagsInput').addEventListener('input', function () {
    document.getElementById('editCustomTagsHidden').value = this.value;
});

// Reset Others checkbox when modals are closed
$('#addFAQModal').on('hidden.bs.modal', function () {
    document.getElementById('othersTag').checked = false;
    document.getElementById('customTagsSection').style.display = 'none';
    document.getElementById('customTagsInput').value = '';
    document.getElementById('customTagsHidden').value = '';
});

$('#editFAQModal').on('hidden.bs.modal', function () {
    document.getElementById('editOthersTag').checked = false;
    document.getElementById('editCustomTagsSection').style.display = 'none';
    document.getElementById('editCustomTagsInput').value = '';
    document.getElementById('editCustomTagsHidden').value = '';
});

function initializeFAQs() {
    const searchInput = document.getElementById('faq-search-input');
    const searchClearBtn = document.querySelector('.search-clear-btn');
    const topicPills = document.querySelectorAll('.topic-pill');

    // Initialize image upload for both modals
    setupImageUpload('faqImages', 'imagePreviewContainer', 'imageUploadArea');
    setupImageUpload('editFaqImages', 'editImagePreviewContainer', 'editImageUploadArea');

    // Search clear functionality
    if (searchClearBtn) {
        searchClearBtn.addEventListener('click', function () {
            window.location.href = faqsUrl;
        });
    }

    // Topic pill navigation
    topicPills.forEach(pill => {
        pill.addEventListener('click', function () {
            const tag = this.getAttribute('data-tag');
            const currentSearch = getCurrentSearchParam();

            let url = faqsUrl + '?tag=' + tag;
            if (currentSearch) {
                url += '&q=' + encodeURIComponent(currentSearch);
            }

            window.location.href = url;
        });
    });

    // FAQ accordion functionality
    initializeAccordion();

    // FAQ actions
    initializeFAQActions();
}

function initializeAccordion() {
    document.querySelectorAll('[data-toggle="collapse"]').forEach(button => {
        button.addEventListener('click', function () {
            const postedByDiv = this.querySelector('.posted-by');
            const isCurrentlyExpanded = this.getAttribute('aria-expanded') === 'true';
            const faqId = this.getAttribute('data-faq-id');
            recordFAQView(faqId);

            if (postedByDiv) {
                if (isCurrentlyExpanded) {
                    postedByDiv.classList.remove('show');
                } else {
                    setTimeout(() => {
                        postedByDiv.classList.add('show');
                    }, 150);
                }
            }
        });
    });

    document.querySelectorAll('.collapse').forEach(collapse => {
        collapse.addEventListener('shown.bs.collapse', function () {
            const button = document.querySelector(`[data-target="#${this.id}"]`);
            const postedByDiv = button?.querySelector('.posted-by');
            if (postedByDiv) {
                postedByDiv.classList.add('show');
            }
        });

        collapse.addEventListener('hidden.bs.collapse', function () {
            const button = document.querySelector(`[data-target="#${this.id}"]`);
            const postedByDiv = button?.querySelector('.posted-by');
            if (postedByDiv) {
                postedByDiv.classList.remove('show');
            }
        });
    });
}

function initializeFAQActions() {
    // Reaction buttons
    document.querySelectorAll('.reaction-btn').forEach(btn => {
        btn.addEventListener('click', handleReactionClick);
    });

    // Edit buttons
    document.querySelectorAll('.edit-faq-btn').forEach(btn => {
        btn.addEventListener('click', handleEditClick);
    });

    // Delete buttons
    document.querySelectorAll('.delete-faq-btn').forEach(btn => {
        btn.addEventListener('click', handleDeleteClick);
    });

    // Toggle status buttons
    document.querySelectorAll('.toggle-status-btn').forEach(btn => {
        btn.addEventListener('click', handleToggleStatusClick);
    });

    // Image click handlers for immediate viewing - NO LOADING DELAYS
    document.querySelectorAll('.image-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const faqId = this.getAttribute('data-faq-id') || this.closest('.faq-card').dataset.faqId;
            console.log('Clicked image for FAQ:', faqId);

            if (faqId) {
                // Open immediately - no loading states
                openImageCarousel(faqId, 0);
            } else {
                console.error('FAQ ID not found');
            }
        });
    });
}

function recordFAQView(faqId) {
    console.log('Recording view for FAQ:', faqId);
    
    const viewedKey = `faq_viewed_${faqId}`;
    if (sessionStorage.getItem(viewedKey)) {
        console.log('FAQ view already recorded for this session.');
        return;
    }
    
    console.log('Making fetch request to record view');
    
    fetch(`/cmis/faqs/record-view/${faqId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('View recorded successfully:', data);
            sessionStorage.setItem(viewedKey, true);
            updateViewCount(faqId, data.total_views);
        } else {
            console.error('Failed to record view:', data.error);
        }
    })
    .catch(error => {
        console.error('Error recording view:', error);
    });
}

function updateViewCount(faqId, newCount) {
    console.log('Updating view count for FAQ', faqId, 'to', newCount);
    const viewNumberElement = document.querySelector(`.view-number[data-faq-id="${faqId}"]`);
    if (viewNumberElement) {
        viewNumberElement.textContent = newCount;
        
        const viewCountSpan = viewNumberElement.closest('.view-count');
        if (viewCountSpan) {
            const viewText = viewCountSpan.innerHTML;
            if (newCount === 1) {
                viewCountSpan.innerHTML = viewText.replace(/views?/, 'view');
            } else {
                viewCountSpan.innerHTML = viewText.replace(/views?/, 'views');
            }
        }
        
        viewNumberElement.style.transition = 'color 0.3s ease';
        viewNumberElement.style.color = '#007bff';
        setTimeout(() => {
            viewNumberElement.style.color = '';
        }, 1000);
    } else {
        console.log('View number element not found for FAQ', faqId);
    }
}

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
    return csrfToken;
}

document.addEventListener('DOMContentLoaded', function () {
    initializeFAQs();
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('FAQ view tracking initialized');
    const faqAccordion = document.getElementById('faq-accordion');
    
    if (faqAccordion) {
        console.log('FAQ accordion found');
        
        faqAccordion.addEventListener('shown.bs.collapse', function(event) {
            const faqId = event.target.id.replace('faq', '');
            console.log('Accordion expanded for FAQ ID:', faqId);
            recordFAQView(faqId);
        });
        
        const faqToggleButtons = document.querySelectorAll('.faq-toggle-btn');
        console.log('Found FAQ toggle buttons:', faqToggleButtons.length);
        
        faqToggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const faqId = this.getAttribute('data-faq-id');
                console.log('FAQ toggle button clicked for ID:', faqId);
                
                setTimeout(() => {
                    const targetElement = document.getElementById('faq' + faqId);
                    if (targetElement && targetElement.classList.contains('show')) {
                        console.log('FAQ is now expanded, recording view');
                        recordFAQView(faqId);
                    } else {
                        console.log('FAQ is not expanded yet or element not found');
                    }
                }, 100);
            });
        });
    } else {
        console.error('FAQ accordion not found!');
    }
});

document.addEventListener('DOMContentLoaded', function () {
    initializeFAQs();

    // Add FAQ Form Submission with confirmation
    const addFAQForm = document.querySelector('#addFAQModal form');
    if (addFAQForm) {
        addFAQForm.addEventListener('submit', function (e) {
            const question = document.getElementById('question').value.trim();
            const answer = document.getElementById('answer').value.trim();

            if (!question || !answer) {
                e.preventDefault();
                Swal.fire({
                    icon: 'warning',
                    title: 'Missing Information',
                    text: 'Please fill in both question and answer fields.',
                    confirmButtonText: 'OK'
                });
                return;
            }

            // Show loading state
            Swal.fire({
                title: 'Adding FAQ...',
                text: 'Please wait while we save your FAQ.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        });
    }

    // Edit FAQ Form Submission with confirmation
    const editFAQForm = document.getElementById('editFAQForm');
    if (editFAQForm) {
        editFAQForm.addEventListener('submit', function (e) {
            const question = document.getElementById('edit_question').value.trim();
            const answer = document.getElementById('edit_answer').value.trim();

            if (!question || !answer) {
                e.preventDefault();
                Swal.fire({
                    icon: 'warning',
                    title: 'Missing Information',
                    text: 'Please fill in both question and answer fields.',
                    confirmButtonText: 'OK'
                });
                return;
            }

            // Show loading state
            Swal.fire({
                title: 'Updating FAQ...',
                text: 'Please wait while we save your changes.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        });
    }
});

function handleReactionClick() {
    const faqId = this.getAttribute('data-faq-id');

    fetch(toggleReactionUrl.replace('0', faqId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update button appearance
                if (data.reacted) {
                    this.classList.remove('btn-outline-primary');
                    this.classList.add('btn-primary');
                } else {
                    this.classList.remove('btn-primary');
                    this.classList.add('btn-outline-primary');
                }

                // Update reaction count
                this.querySelector('.reaction-count').textContent = data.total_reactions;
                this.setAttribute('data-user-reacted', data.reacted);
                
                // Store anonymous reaction state in session storage
                if (!data.user_authenticated) {
                    const sessionKey = `faq_reaction_${faqId}`;
                    if (data.reacted) {
                        sessionStorage.setItem(sessionKey, 'true');
                    } else {
                        sessionStorage.removeItem(sessionKey);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating reaction', 'error');
        });
}


function checkAnonymousReactions() {
    // Only check for anonymous users
    if (typeof userAuthenticated !== 'undefined' && !userAuthenticated) {
        document.querySelectorAll('.reaction-btn').forEach(button => {
            const faqId = button.getAttribute('data-faq-id');
            const sessionKey = `faq_reaction_${faqId}`;
            
            // Check if user has reacted anonymously
            if (sessionStorage.getItem(sessionKey) === 'true') {
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-primary');
                button.setAttribute('data-user-reacted', 'true');
            }
        });
    }
}

// Add this to your DOMContentLoaded event
document.addEventListener('DOMContentLoaded', function () {
    initializeFAQs();
    checkAnonymousReactions(); // Add this line
});

function handleEditClick() {
    const faqId = this.getAttribute('data-faq-id');

    // Show loading state
    Swal.fire({
        title: 'Loading FAQ data...',
        text: 'Please wait while we fetch the FAQ information.',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Fetch FAQ data
    fetch(getFaqDataUrl.replace('0', faqId))
        .then(response => response.json())
        .then(data => {
            Swal.close(); // Close loading dialog

            if (data.success) {
                populateEditModal(data.data, faqId);
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: 'Error loading FAQ data: ' + (data.error || 'Unknown error'),
                    confirmButtonText: 'OK'
                });
            }
        })
        .catch(error => {
            Swal.close(); // Close loading dialog
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Network Error!',
                text: 'Failed to load FAQ data. Please check your connection and try again.',
                confirmButtonText: 'OK'
            });
        });
}

function populateEditModal(data, faqId) {
  // Set the question in CKEditor with proper HTML decoding
  if (editQuestionEditor) {
    // Decode HTML entities and set the data
    const questionContent = data.question || '';
    editQuestionEditor.setData(questionContent);
  }
  
  // Set the answer in CKEditor with proper HTML decoding
  if (editAnswerEditor) {
    const answerContent = data.answer || '';
    editAnswerEditor.setData(answerContent);
  }
  
  document.getElementById('editFAQForm').action = editFaqUrl.replace('0', faqId);
  
  // Update checkboxes
  document.querySelectorAll('.edit-tag-checkbox').forEach(checkbox => {
    checkbox.checked = data.tag_ids.includes(parseInt(checkbox.value));
  });

  // Handle existing images
  populateExistingImages(data.images);
}

function populateExistingImages(images) {
    const existingImagesContainer = document.getElementById('existingImages');
    existingImagesContainer.innerHTML = '';

    images.forEach(image => {
        const imageDiv = document.createElement('div');
        imageDiv.className = 'existing-image';
        imageDiv.innerHTML = `
            <img src="${image.url}" alt="FAQ Image">
            <button type="button" class="existing-image-remove" onclick="removeExistingImage(this, ${image.id})">
                <i class="fas fa-times"></i>
            </button>
        `;
        existingImagesContainer.appendChild(imageDiv);
    });
}

function handleDeleteClick() {
    const faqId = this.getAttribute('data-faq-id');
    const question = this.getAttribute('data-question');

    Swal.fire({
        title: 'Delete FAQ?',
        html: `Are you sure you want to delete<br><strong>"${question}"</strong><br><br>This action cannot be undone.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '<i class="fas fa-trash"></i> Yes, delete it!',
        cancelButtonText: '<i class="fas fa-times"></i> Cancel',
        reverseButtons: true,
        customClass: {
            confirmButton: 'btn btn-danger',
            cancelButton: 'btn btn-secondary'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting FAQ...',
                text: 'Please wait while we delete the FAQ.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Redirect to delete URL
            window.location.href = deleteFaqUrl.replace('0', faqId);
        }
    });
}

function handleToggleStatusClick() {
    const faqId = this.getAttribute('data-faq-id');
    const currentStatus = this.getAttribute('data-current-status') === 'true';

    // Determine the correct action and message based on current status
    const actionText = currentStatus ? 'hide' : 'show';
    const confirmText = currentStatus ?
        'Are you sure you want to hide this FAQ? It will not be visible to regular users.' :
        'Are you sure you want to show this FAQ? It will be visible to all users.';
    const actionColor = currentStatus ? '#ffc107' : '#28a745';

    Swal.fire({
        title: `${actionText.charAt(0).toUpperCase() + actionText.slice(1)} FAQ?`,
        text: confirmText,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: actionColor,
        cancelButtonColor: '#6c757d',
        confirmButtonText: `<i class="fas fa-${currentStatus ? 'eye-slash' : 'eye'}"></i> Yes, ${actionText} it!`,
        cancelButtonText: '<i class="fas fa-times"></i> Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: `${actionText.charAt(0).toUpperCase() + actionText.slice(1)}ing FAQ...`,
                text: 'Please wait while we update the FAQ status.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Submit the toggle request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = toggleStatusUrl.replace('0', faqId);

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);

            document.body.appendChild(form);
            form.submit();
        }
    });
}

function setupImageUpload(inputId, previewContainerId, uploadAreaId) {
    const fileInput = document.getElementById(inputId);
    const previewContainer = document.getElementById(previewContainerId);
    const uploadArea = document.getElementById(uploadAreaId);

    if (!fileInput || !previewContainer || !uploadArea) return;

    // Remove existing event listeners to prevent duplicates
    fileInput.removeEventListener('change', fileInput._handleFileInputChange);
    uploadArea.removeEventListener('dragover', uploadArea._handleDragOver);
    uploadArea.removeEventListener('dragleave', uploadArea._handleDragLeave);
    uploadArea.removeEventListener('drop', uploadArea._handleDrop);
    uploadArea.removeEventListener('click', uploadArea._handleClick);

    // Create named functions to store references
    function handleFileInputChange(e) {
        if (e.target.files.length > 0) {
            // Clear existing previews to prevent duplication
            previewContainer.innerHTML = '';
            handleFiles(e.target.files, previewContainer);
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Clear existing previews to prevent duplication
            previewContainer.innerHTML = '';
            handleFiles(files, previewContainer);

            // Create a new FileList and assign to input
            const dt = new DataTransfer();
            Array.from(files).forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
        }
    }

    function handleClick(e) {
        if (e.target === uploadArea || e.target.closest('.upload-content')) {
            fileInput.click();
        }
    }

    // Store references to the functions for later removal
    fileInput._handleFileInputChange = handleFileInputChange;
    uploadArea._handleDragOver = handleDragOver;
    uploadArea._handleDragLeave = handleDragLeave;
    uploadArea._handleDrop = handleDrop;
    uploadArea._handleClick = handleClick;

    // Add the event listeners
    fileInput.addEventListener('change', handleFileInputChange);
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', handleClick);
}

function handleFiles(files, previewContainer) {
    // Get existing preview sources to avoid duplicates
    const existingPreviews = Array.from(previewContainer.querySelectorAll('.image-preview img')).map(img => img.src);

    Array.from(files).forEach((file, index) => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                // Check if this image is already in the preview
                if (!existingPreviews.includes(e.target.result)) {
                    createImagePreview(e.target.result, previewContainer, index);
                }
            };
            reader.readAsDataURL(file);
        }
    });
}

function createImagePreview(src, container, index) {
    const previewDiv = document.createElement('div');
    previewDiv.className = 'image-preview';
    previewDiv.innerHTML = `
        <img src="${src}" alt="Preview ${index + 1}">
        <button type="button" class="image-remove" onclick="removeImagePreview(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    container.appendChild(previewDiv);
}

function removeImagePreview(button) {
    const previewContainer = button.closest('.image-preview-container');
    const fileInputId = previewContainer.parentElement.querySelector('.file-input').id;
    const fileInput = document.getElementById(fileInputId);

    // Get the index of the removed preview
    const allPreviews = Array.from(previewContainer.querySelectorAll('.image-preview'));
    const removedIndex = allPreviews.indexOf(button.closest('.image-preview'));

    // Remove the preview
    button.closest('.image-preview').remove();

    // Get remaining previews count
    const remainingPreviews = previewContainer.querySelectorAll('.image-preview').length;

    // If no previews left, clear the file input
    if (remainingPreviews === 0) {
        fileInput.value = '';
    } else {
        // Rebuild the file list without the removed file
        const currentFiles = Array.from(fileInput.files);
        const dt = new DataTransfer();

        currentFiles.forEach((file, index) => {
            if (index !== removedIndex) {
                dt.items.add(file);
            }
        });

        // Update file input with remaining files
        fileInput.files = dt.files;
    }
}

function removeExistingImage(button, imageId) {
    Swal.fire({
        title: 'Remove Image?',
        text: 'Are you sure you want to remove this image?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, remove it!'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.getElementById('editFAQForm');
            const deleteInput = document.createElement('input');
            deleteInput.type = 'hidden';
            deleteInput.name = 'delete_images';
            deleteInput.value = imageId;
            form.appendChild(deleteInput);

            button.closest('.existing-image').remove();
            showToast('Image marked for removal', 'success');
        }
    });
}

function openImageCarousel(faqId, startIndex = 0) {
    console.log('Opening carousel for FAQ:', faqId);

    fetch(getFaqDataUrl.replace('0', faqId))
        .then(response => response.json())
        .then(data => {
            console.log('FAQ data received:', data);

            if (data.success) {
                if (data.data.images && data.data.images.length > 0) {
                    createImageModal(data.data.images, startIndex, data.data.question);
                } else {
                    console.warn('No images found but image was clicked');
                    showToast('No images available for this FAQ', 'warning');
                }
            } else {
                console.error('Error from server:', data.error);
                showToast('Error loading images: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Error loading images:', error);
            showToast('Error loading images', 'error');
        });
}

// Create and show image modal immediately - no delays
function createImageModal(images, startIndex = 0, title = 'FAQ Images') {
    if (images.length === 0) return;

    // Remove any existing modal
    const existingModal = document.getElementById('imageCarouselModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal HTML immediately
    const modalHtml = `
<div class="modal fade show image-carousel-modal" id="imageCarouselModal" tabindex="-1" style="display: block; background: rgba(255,255,255,0.1); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);">
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content bg-transparent border-0">
                    <div class="modal-header border-0 pb-0">

                        <button type="button" class="close text-white" onclick="closeImageModal()" style="font-size: 2rem; opacity: 0.8; background: rgba(0,0,0,0.5); border: none; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body p-0">
                        <div id="faqImageCarousel" class="carousel slide" data-ride="carousel" data-interval="false">
                            <div class="carousel-inner">
                                ${images.map((image, index) => `
                                    <div class="carousel-item ${index === startIndex ? 'active' : ''}">
                                        <div class="d-flex justify-content-center align-items-center" style="height: 70vh;">
                                            <img src="${image.url}" 
                                                 alt="FAQ Image ${index + 1}" 
                                                 class="img-fluid" 
                                                 style="max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 8px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            ${images.length > 1 ? `
                                <a class="carousel-control-prev" href="#faqImageCarousel" role="button" data-slide="prev" style="width: 60px; height: 60px; background: rgba(0,0,0,0.7); border-radius: 50%; top: 50%; left: 20px; transform: translateY(-50%); border: 2px solid rgba(255,255,255,0.3);">
                                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                                </a>
                                <a class="carousel-control-next" href="#faqImageCarousel" role="button" data-slide="next" style="width: 60px; height: 60px; background: rgba(0,0,0,0.7); border-radius: 50%; top: 50%; right: 20px; transform: translateY(-50%); border: 2px solid rgba(255,255,255,0.3);">
                                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                                </a>
                                <ol class="carousel-indicators" style="bottom: 20px;">
                                    ${images.map((_, index) => `
                                        <li data-target="#faqImageCarousel" data-slide-to="${index}" ${index === startIndex ? 'class="active"' : ''} style="width: 12px; height: 12px; border-radius: 50%; margin: 0 6px; background: ${index === startIndex ? 'var(--primary-color, #2c5530)' : 'rgba(255,255,255,0.5)'}; cursor: pointer;"></li>
                                    `).join('')}
                                </ol>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to page immediately
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal immediately
    const modal = document.getElementById('imageCarouselModal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling

    // Initialize Bootstrap carousel
    if (typeof $ !== 'undefined' && $.fn.carousel) {
        $('#faqImageCarousel').carousel({
            interval: false,
            wrap: true,
            keyboard: true
        });

        if (startIndex > 0) {
            $('#faqImageCarousel').carousel(startIndex);
        }
    }

    // Handle keyboard navigation
    document.addEventListener('keydown', handleModalKeypress);

    // Handle click outside to close
    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeImageModal();
        }
    });
}

// Close modal function - make it global and immediate
window.closeImageModal = function () {
    const modal = document.getElementById('imageCarouselModal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = ''; // Restore scrolling
        document.removeEventListener('keydown', handleModalKeypress);
    }
};

// Handle keyboard navigation
function handleModalKeypress(e) {
    const modal = document.getElementById('imageCarouselModal');
    if (!modal) return;

    switch (e.key) {
        case 'Escape':
            closeImageModal();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            if (typeof $ !== 'undefined' && $.fn.carousel) {
                $('#faqImageCarousel').carousel('prev');
            }
            break;
        case 'ArrowRight':
            e.preventDefault();
            if (typeof $ !== 'undefined' && $.fn.carousel) {
                $('#faqImageCarousel').carousel('next');
            }
            break;
    }
}

// Utility functions
function getCurrentSearchParam() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('q') || '';
}

// Simple toast notification function - no loading delays
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    toast.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px; 
        border-radius: 8px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease;
    `;
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span><i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i> ${message}</span>
            <button type="button" class="close ml-2" onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 1.2rem; opacity: 0.7;">
                <span>&times;</span>
            </button>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 3000);
}

function showNotification(message, type = 'info') {
    // Use simple toast instead of SweetAlert for faster display
    showToast(message, type);
}

// Add CSS animation for toast notifications
const toastStyle = document.createElement('style');
toastStyle.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(toastStyle);
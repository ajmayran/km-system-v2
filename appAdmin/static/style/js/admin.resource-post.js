/**
 * Show/hide resource-specific fields based on selected type
 * @param {string} specificFieldsId - The ID of the specific fields to show
 */
function showResourceFields(specificFieldsId) {
    console.log('=== showResourceFields function started ===');
    console.log('Requested fields ID:', specificFieldsId);
    
    try {
        // Map of field IDs to their Django model form names
        const fieldModelMap = {
            'eventsFields': 'Event',
            'information_systemswebsitesFields': 'InformationSystem',
            'mapsFields': 'Map',
            'mediaFields': 'Media',
            'newsFields': 'News',
            'policiesFields': 'Policy',
            'projectsFields': 'Project',
            'publicationsFields': 'Publication',
            'technologiesFields': 'Technology',
            'trainingseminarsFields': 'TrainingSeminar',
            'webinarsFields': 'Webinar',
            'productsFields': 'Product'
        };

        // First, hide all resource-specific fields
        const resourceFields = document.querySelectorAll('.resource-specific-fields');
        console.log(`Found ${resourceFields.length} resource-specific-fields`);
        resourceFields.forEach(field => {
            field.style.display = 'none';
            
            // Disable all required inputs in hidden sections to prevent validation errors
            const requiredInputs = field.querySelectorAll('input[required], select[required], textarea[required]');
            requiredInputs.forEach(input => {
                input.disabled = true;
                // Set a data attribute to remember that this was required
                if (!input.hasAttribute('data-was-required')) {
                    input.setAttribute('data-was-required', 'true');
                }
            });
            
            console.log('Hidden field:', field.id);
        });

        // Handle the special case for maps/map
        let targetElementId = specificFieldsId;
        if (specificFieldsId === 'mapsFields') {
            targetElementId = 'mapFields';
        } else if (!targetElementId.endsWith('Fields')) {
            targetElementId = targetElementId + 'Fields';
        }
        console.log('Looking for element with ID:', targetElementId);
        
        // Find and show the target element
        const targetElement = document.getElementById(targetElementId);
        if (targetElement) {
            targetElement.style.display = 'block';
            console.log('Successfully showing:', targetElementId);
            
            // Enable all inputs that were previously required in the visible section
            const potentiallyRequiredInputs = targetElement.querySelectorAll('input[data-was-required], select[data-was-required], textarea[data-was-required]');
            potentiallyRequiredInputs.forEach(input => {
                input.disabled = false;
            });
            
            // Also enable all other inputs in this section
            const allInputs = targetElement.querySelectorAll('input, select, textarea');
            allInputs.forEach(input => {
                if (!input.hasAttribute('data-was-required')) {
                    input.disabled = false;
                }
            });
            
            // Focus on the first input in the displayed section
            const firstInput = targetElement.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => {
                    firstInput.focus();
                    console.log('Focused on first input in section');
                }, 100);
            }
        } else {
            console.error('Could not find element with ID:', targetElementId);
        }
    } catch (error) {
        console.error('Error in showResourceFields:', error);
    }
}

/**
 * Set up the resource type change handler to show/hide appropriate fields
 */
function setupResourceTypeHandler() {
    const resourceTypeSelect = document.getElementById('resourceType');
    
    if (resourceTypeSelect) {
        // Remove any existing event listeners (prevent duplicates)
        const newResourceTypeSelect = resourceTypeSelect.cloneNode(true);
        resourceTypeSelect.parentNode.replaceChild(newResourceTypeSelect, resourceTypeSelect);
        
        // Add the change event listener
        newResourceTypeSelect.addEventListener('change', function() {
            try {
                console.log('=== Change event triggered ===');
                const selectedOption = this.options[this.selectedIndex];
                const fieldsId = selectedOption.getAttribute('data-fields-id');
                console.log('Selected fields ID:', fieldsId);
                
                if (!fieldsId) {
                    console.error('No data-fields-id found on selected option');
                    return;
                }
                
                showResourceFields(fieldsId);
            } catch (error) {
                console.error('Error in change event handler:', error);
            }
        });
        
        // Initial setup if a value is already selected
        if (newResourceTypeSelect.selectedIndex > 0) {
            const selectedOption = newResourceTypeSelect.options[newResourceTypeSelect.selectedIndex];
            const fieldsId = selectedOption.getAttribute('data-fields-id');
            if (fieldsId) {
                showResourceFields(fieldsId);
            }
        } else {
            // Disable all required fields initially
            document.querySelectorAll('.resource-specific-fields').forEach(field => {
                const requiredInputs = field.querySelectorAll('input[required], select[required], textarea[required]');
                requiredInputs.forEach(input => {
                    input.disabled = true;
                });
            });
        }
    }
}

/**
 * Initialize the resource form with event handlers and UI components
 */
function initializeResourceForm() {
    // Save as draft functionality
    const saveDraftButton = document.getElementById('saveDraftButton');
    if (saveDraftButton) {
        saveDraftButton.addEventListener('click', function() {
            const draftInput = document.createElement('input');
            draftInput.type = 'hidden';
            draftInput.name = 'isDraft';
            draftInput.value = 'true';
            
            const form = document.getElementById('resourceForm');
            form.appendChild(draftInput);
            form.submit();
        });
    }
    
    // Form validation before submission
    const resourceForm = document.getElementById('resourceForm');
    if (resourceForm) {
        resourceForm.addEventListener('submit', function(event) {
            // First check if resource type is selected
            const resourceTypeSelect = document.getElementById('resourceType');
            if (!resourceTypeSelect || resourceTypeSelect.selectedIndex === 0) {
                event.preventDefault();
                showFormError('Please select a resource type.');
                resourceTypeSelect.classList.add('is-invalid');
                return;
            } else {
                resourceTypeSelect.classList.remove('is-invalid');
            }
            
            // Validate based on form field requirements
            if (!checkFieldRequirements()) {
                event.preventDefault();
                showFormError('Please fill in all required fields.');
                
                // Scroll to the first invalid field
                const firstInvalid = document.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => {
                        firstInvalid.focus();
                    }, 500);
                }
            }
        });
    }
    
    // Initialize Select2 for multi-select if available
    if (typeof $.fn !== 'undefined' && typeof $.fn.select2 !== 'undefined') {
        $('#resourceCommodities').select2({
            placeholder: "Select commodities",
            allowClear: true
        });
    }
    
    // Attach remove tag functionality to the default AANR tags
    attachRemoveTagHandlers();
}

/**
 * Function to attach handlers to the default AANR tags
 */
function attachRemoveTagHandlers() {
    const removeButtons = document.querySelectorAll('#tagContainer .remove-tag');
    const tagValues = document.getElementById('tagValues');
    const tags = tagValues.value ? tagValues.value.split(',') : [];
    
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tagElement = this.parentElement;
            const tagText = tagElement.textContent.replace('×', '').trim();
            
            // Remove from tags array
            const index = tags.indexOf(tagText);
            if (index !== -1) {
                tags.splice(index, 1);
            }
            
            // Remove from DOM
            tagElement.remove();
            
            // Update hidden input
            tagValues.value = tags.join(',');
        });
    });
}

/**
 * Initialize tag input functionality
 */
function initializeTagInput() {
    const tagInput = document.getElementById('tagInput');
    const tagContainer = document.getElementById('tagContainer');
    const tagValues = document.getElementById('tagValues');
    
    if (!tagInput || !tagContainer || !tagValues) return;
    
    // Initialize with the default tags from the hidden input
    const tags = tagValues.value ? tagValues.value.split(',') : [];
    
    tagInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            
            const tag = this.value.trim();
            
            if(tag && !tags.includes(tag)) {
                // Add to tags array
                tags.push(tag);
                
                // Create tag element
                const tagElement = document.createElement('div');
                tagElement.className = 'tag-badge';
                tagElement.innerHTML = `${tag} <span class="remove-tag">&times;</span>`;
                
                // Add remove functionality
                tagElement.querySelector('.remove-tag').addEventListener('click', function() {
                    // Remove from tags array
                    const index = tags.indexOf(tag);
                    if (index !== -1) {
                        tags.splice(index, 1);
                    }
                    // Remove from DOM
                    tagElement.remove();
                    // Update hidden field
                    tagValues.value = tags.join(',');
                });
                
                // Append to container
                tagContainer.appendChild(tagElement);
                
                // Update hidden field
                tagValues.value = tags.join(',');
                
                // Clear input
                this.value = '';
            }
        }
    });
}

/**
 * Initialize commodity selection handling
 */
function initializeCommoditySelection() {
    const commoditySelect = document.getElementById('resourceCommodities');
    const selectedCommoditiesList = document.getElementById('selectedCommodities');
    const commodityIdsInput = document.getElementById('commodityIds');
    
    if (!commoditySelect || !selectedCommoditiesList || !commodityIdsInput) return;
    
    let selectedCommodities = [];
    
    commoditySelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.value && !selectedCommodities.includes(selectedOption.value)) {
            // Add to selected commodities array
            selectedCommodities.push(selectedOption.value);
            
            // Create commodity tag
            const commodityTag = document.createElement('li');
            commodityTag.className = 'selected-tag';
            commodityTag.innerHTML = `
                ${selectedOption.text}
                <span class="remove-tag" data-value="${selectedOption.value}">&times;</span>
            `;
            
            // Add remove functionality
            commodityTag.querySelector('.remove-tag').addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                selectedCommodities = selectedCommodities.filter(id => id !== value);
                commodityTag.remove();
                updateCommodityIds();
            });
            
            // Add to list
            selectedCommoditiesList.appendChild(commodityTag);
            
            // Update hidden input
            updateCommodityIds();
            
            // Reset select
            this.selectedIndex = 0;
        }
    });
    
    function updateCommodityIds() {
        commodityIdsInput.value = selectedCommodities.join(',');
    }
}

/**
 * Show a form error message
 * @param {string} message - The error message to display
 */
function showFormError(message) {
    // Remove any existing error messages
    const existingAlerts = document.querySelectorAll('#resourceForm .alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert message
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show mt-3';
    errorAlert.role = 'alert';
    errorAlert.innerHTML = `
        <strong>Form Error!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to form
    const form = document.getElementById('resourceForm');
    form.insertBefore(errorAlert, form.firstChild);
    
    // Scroll to top of form
    errorAlert.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (errorAlert.parentNode) {
            errorAlert.parentNode.removeChild(errorAlert);
        }
    }, 5000);
}

/**
 * Reset the resource form
 */
function resetResourceForm() {
    const form = document.getElementById('resourceForm');
    if (form) {
        form.reset();
    }
    
    // Reset validation styling
    form.querySelectorAll('.is-invalid').forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    // Remove any error messages
    form.querySelectorAll('.alert').forEach(alert => {
        alert.remove();
    });
    
    // Restore default AANR tags
    const tagContainer = document.getElementById('tagContainer');
    const tagValues = document.getElementById('tagValues');
    
    if (tagContainer) {
        tagContainer.innerHTML = `
            <div class="tag-badge">Agriculture <span class="remove-tag">&times;</span></div>
            <div class="tag-badge">Aquatic <span class="remove-tag">&times;</span></div>
            <div class="tag-badge">Natural Resources <span class="remove-tag">&times;</span></div>
            <div class="tag-badge">Research <span class="remove-tag">&times;</span></div>
            <div class="tag-badge">Technology <span class="remove-tag">&times;</span></div>
        `;
    }
    
    if (tagValues) {
        tagValues.value = 'Agriculture,Aquatic,Natural Resources,Research,Technology';
    }
    
    // Reattach event handlers to remove tags
    attachRemoveTagHandlers();
    
    // Clear selected commodities
    const selectedCommoditiesList = document.getElementById('selectedCommodities');
    const commodityIdsInput = document.getElementById('commodityIds');
    
    if (selectedCommoditiesList) {
        selectedCommoditiesList.innerHTML = '';
    }
    
    if (commodityIdsInput) {
        commodityIdsInput.value = '';
    }
    
    // Hide all resource-specific sections
    document.querySelectorAll('.resource-specific-fields').forEach(field => {
        field.style.display = 'none';
        
        // Disable all required inputs in hidden sections
        const requiredInputs = field.querySelectorAll('input[required], select[required], textarea[required]');
        requiredInputs.forEach(input => {
            input.disabled = true;
        });
    });
    
    // Reset resource type select
    const resourceTypeSelect = document.getElementById('resourceType');
    if (resourceTypeSelect) {
        resourceTypeSelect.selectedIndex = 0;
    }
    
    // Reset Select2 if it exists
    if (typeof $.fn !== 'undefined' && typeof $.fn.select2 !== 'undefined') {
        $('#resourceCommodities').val(null).trigger('change');
    }
}

/**
 * Open the modal and reset the form
 */
function openResourceModal() {
    resetResourceForm();
    
    // Open the modal
    const modal = new bootstrap.Modal(document.getElementById('createResourceModal'));
    modal.show();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Mark all potentially required fields with a data attribute based on Django forms
    initializeRequiredFieldTracking();
    
    // Set up the resource type handler
    setupResourceTypeHandler();
    
    // Initialize all form functionalities
    initializeResourceForm();
    initializeTagInput();
    initializeCommoditySelection();
    
    // Disable all required fields in hidden sections initially
    document.querySelectorAll('.resource-specific-fields').forEach(field => {
        field.style.display = 'none';
        
        // Disable all inputs in hidden sections
        const allInputs = field.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            input.disabled = true;
        });
    });
    
    // Preload the form submission event to prevent validation errors on required fields
    // This will catch the submission before the browser tries to validate hidden required fields
    const resourceForm = document.getElementById('resourceForm');
    if (resourceForm) {
        resourceForm.setAttribute('novalidate', 'novalidate');
    }
});

/**
 * Mark fields that are required based on their Django form definitions
 */
function initializeRequiredFieldTracking() {
    // Map element IDs to their required status based on Django form fields
    const requiredFieldMap = {
        // ResourceMetadata (common fields)
        'resourceTitle': true,
        'resourceDescription': true,
        'resourceType': true,
        
        // Event form
        'eventStartDate': true,
        'eventEndDate': true,
        'eventLocation': true,
        'eventOrganizer': true,
        
        // Information Systems
        'infoSystemUrl': true,
        'infoSystemOwner': true,
        
        // Media form
        'mediaType': true,
        
        // News form
        'newsPublishDate': true,
        'newsSource': true,
        'newsContent': true,
        
        // Policy form
        'policyEffectiveDate': true,
        'policyIssuingBody': true,
        'policyStatus': true,
        
        // Project form
        'projectStartDate': true,
        'projectLead': true,
        'projectStatus': true,
        
        // Publication form
        'publicationAuthors': true,
        'publicationDate': true,
        'publicationType': true,
        
        // Technology form
        'technologyDeveloper': true,
        
        // Training/Seminar form
        'trainingStartDate': true,
        'trainingEndDate': true,
        'trainingLocation': true,
        
        // Webinar form
        'webinarDate': true,
        'webinarDuration': true,
        'webinarPlatform': true,
        'webinarPresenters': true,
        
        // Product form
        'productManufacturer': true,
        'productFeatures': true
    };
    
    // Apply required attribute and data-was-required to track fields
    Object.entries(requiredFieldMap).forEach(([fieldId, isRequired]) => {
        const field = document.getElementById(fieldId);
        if (field && isRequired) {
            field.setAttribute('required', 'required');
            field.setAttribute('data-was-required', 'true');
        }
    });
}
// Function to view resource details
function viewResource(resourceId) {
    // In a real application, this would navigate to a resource detail page
    alert('Viewing resource: ' + resourceId);
}

// Function to edit resource
function editResource(resourceId) {
    // In a real application, this would open an edit form with the resource's data
    alert('Editing resource: ' + resourceId);
}

// Function to toggle featured status
function toggleFeatured(resourceId) {
    // In a real application, this would update the resource's featured status
    alert('Toggling featured status for resource: ' + resourceId);
}

// Function to confirm deletion
function confirmDelete(resourceId) {
    if (confirm('Are you sure you want to delete this resource?')) {
        // In a real application, this would delete the resource
        alert('Resource deleted: ' + resourceId);
    }
}

// Tag input functionality
document.addEventListener('DOMContentLoaded', function() {
    const tagInput = document.querySelector('.tag-input');
    const tagContainer = document.querySelector('.tag-input-container');
    
    if (tagInput) {
        tagInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                
                const tagText = this.value.trim();
                if (tagText) {
                    // Create new tag
                    const tagBadge = document.createElement('div');
                    tagBadge.className = 'tag-badge';
                    tagBadge.innerHTML = `${tagText} <span class="remove-tag">&times;</span>`;
                    
                    // Insert before the input
                    tagContainer.insertBefore(tagBadge, this);
                    
                    // Clear input
                    this.value = '';
                    
                    // Add delete handler to the new tag
                    const removeBtn = tagBadge.querySelector('.remove-tag');
                    removeBtn.addEventListener('click', function() {
                        tagBadge.remove();
                    });
                }
            }
        });
        
        // Add delete handlers to existing tags
        document.querySelectorAll('.remove-tag').forEach(btn => {
            btn.addEventListener('click', function() {
                this.parentElement.remove();
            });
        });
    }
});

// Initialize Bootstrap tooltips and popovers
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
});
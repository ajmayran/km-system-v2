// Additional JavaScript for Enhanced Forum Features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    AOS.init({
        duration: 800,
        once: true
    });

    // Show all posts initially
    showAllPosts();

    // Function to show all posts when "All Topics" is selected
    function showAllPosts() {
      const posts = document.querySelectorAll('.discussion-post');
      posts.forEach(post => {
        post.style.display = 'block';
      });
      checkEmptyState();
    }

    // Topic Pills Selection
    const topicPills = document.querySelectorAll('.topic-pill');
    
    topicPills.forEach(pill => {
      pill.addEventListener('click', function() {
        // Remove active class from all pills
        topicPills.forEach(p => p.classList.remove('active'));
        
        // Add active class to clicked pill
        this.classList.add('active');
        
        // Filter posts based on selected topic
        const topic = this.textContent.trim();
        
        if (topic === 'All Topics') {
          showAllPosts();
        } else {
          filterPostsByTopic(topic);
        }
      });
    });
    
    function filterPostsByTopic(topic) {
      const lowercaseTopic = topic.toLowerCase();
      const discussionPosts = document.querySelectorAll('.discussion-post');
      
      discussionPosts.forEach(post => {
        const postTags = Array.from(post.querySelectorAll('.post-tag'))
          .map(tag => tag.textContent.trim().toLowerCase());
        
        // Map categories to topics for filtering
        let topicMatches = false;
        
        // Handle specific mappings
        switch(lowercaseTopic) {
          case 'crops':
            topicMatches = postTags.some(tag => 
              ['rice', 'corn', 'coconut'].includes(tag));
            break;
          case 'livestock':
            topicMatches = postTags.some(tag => 
              ['livestock', 'poultry', 'cattle', 'goat'].includes(tag));
            break;
          case 'aquaculture':
            topicMatches = postTags.some(tag => 
              ['aquaculture', 'tilapia', 'fish'].includes(tag));
            break;
          case 'technology':
            topicMatches = postTags.some(tag => 
              ['technology', 'innovation', 'tools', 'automation'].includes(tag));
            break;
          case 'market & economics':
            topicMatches = postTags.some(tag => 
              ['market', 'economics', 'pricing', 'trade'].includes(tag));
            break;
          case 'climate & environment':
            topicMatches = postTags.some(tag => 
              ['climate', 'environment', 'sustainability', 'weather'].includes(tag));
            break;
          default:
            // If no specific mapping, try a direct match
            topicMatches = postTags.some(tag => tag.includes(lowercaseTopic));
        }
        
        post.style.display = topicMatches ? 'block' : 'none';
      });
      
      checkEmptyState();
    }
    
    // Post interaction handlers
    const interactionItems = document.querySelectorAll('.interaction-item');
    
    interactionItems.forEach(item => {
      item.addEventListener('click', function() {
        const type = this.querySelector('span:not(.interaction-count)') ? 
          this.querySelector('span:not(.interaction-count)').textContent.trim() : 
          this.querySelector('i').className;
        
        // Handle different interaction types
        if (type.includes('thumbs-up')) {
          handleLike(this);
        } else if (type.includes('bookmark')) {
          handleBookmark(this);
        } else if (type.includes('share')) {
          handleShare(this);
        } else if (type.includes('comment')) {
          // Scroll to comment section or expand comments
          console.log('Comment interaction clicked');
        }
      });
    });
    
    function handleLike(element) {
      // Toggle like state
      const icon = element.querySelector('i');
      const countElement = element.querySelector('.interaction-count');
      let count = parseInt(countElement.textContent);
      
      if (icon.classList.contains('far')) {
        // Like
        icon.classList.replace('far', 'fas');
        icon.style.color = '#2c6e49';
        countElement.textContent = count + 1;
      } else {
        // Unlike
        icon.classList.replace('fas', 'far');
        icon.style.color = '';
        countElement.textContent = count - 1;
      }
    }
    
    function handleBookmark(element) {
      // Toggle bookmark state
      const icon = element.querySelector('i');
      const textSpan = element.querySelector('span:not(.interaction-count)');
      
      if (icon.classList.contains('far')) {
        // Bookmark
        icon.classList.replace('far', 'fas');
        icon.style.color = '#2c6e49';
        if (textSpan) textSpan.textContent = 'Saved';
      } else {
        // Unbookmark
        icon.classList.replace('fas', 'far');
        icon.style.color = '';
        if (textSpan) textSpan.textContent = 'Save';
      }
    }
    
    function handleShare(element) {
      // Show share options (could be expanded with a proper sharing menu)
      Swal.fire({
        title: 'Share this discussion',
        html: `
          <div style="display: flex; justify-content: center; gap: 1rem; margin: 1.5rem 0;">
            <button class="share-option" data-platform="facebook" style="background: #3b5998; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <i class="fab fa-facebook-f"></i>
            </button>
            <button class="share-option" data-platform="twitter" style="background: #1da1f2; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <i class="fab fa-twitter"></i>
            </button>
            <button class="share-option" data-platform="linkedin" style="background: #0077b5; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <i class="fab fa-linkedin-in"></i>
            </button>
            <button class="share-option" data-platform="whatsapp" style="background: #25d366; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <i class="fab fa-whatsapp"></i>
            </button>
          </div>
          <div style="margin: 1rem 0;">
            <input type="text" id="shareLink" value="https://aanr-hub.example.com/forum/post/123" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" readonly>
          </div>
        `,
        showConfirmButton: false,
        showCloseButton: true,
        focusConfirm: false,
        didOpen: () => {
          // Select link on click
          document.getElementById('shareLink').addEventListener('click', function() {
            this.select();
            document.execCommand('copy');
            Swal.showValidationMessage('Link copied to clipboard!');
            setTimeout(() => {
              Swal.resetValidationMessage();
            }, 2000);
          });
          
          // Handle share button clicks
          document.querySelectorAll('.share-option').forEach(button => {
            button.addEventListener('click', function() {
              const platform = this.getAttribute('data-platform');
              const postUrl = document.getElementById('shareLink').value;
              const postTitle = 'AANR Knowledge Hub Discussion';
              
              let shareUrl = '';
              switch(platform) {
                case 'facebook':
                  shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(postUrl)}`;
                  break;
                case 'twitter':
                  shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(postUrl)}&text=${encodeURIComponent(postTitle)}`;
                  break;
                case 'linkedin':
                  shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(postUrl)}`;
                  break;
                case 'whatsapp':
                  shareUrl = `https://wa.me/?text=${encodeURIComponent(postTitle + ' ' + postUrl)}`;
                  break;
              }
              
              if (shareUrl) {
                window.open(shareUrl, '_blank');
              }
            });
          });
        }
      });
    }
    
    // Function to check if we need to show empty state
    function checkEmptyState() {
      const activeTab = document.querySelector('.forum-tab.active');
      const activeTabId = activeTab ? activeTab.getAttribute('data-target') : 'newQuestions';
      const container = document.querySelector(`#${activeTabId}`);
      const visiblePosts = document.querySelectorAll(`#${activeTabId} .discussion-post[style*="display: block"]`);
      const emptyState = document.querySelector('.forum-empty-state');
      
      if (container && emptyState) {
        if (visiblePosts.length === 0) {
          // No visible posts, show empty state
          container.appendChild(emptyState);
          emptyState.style.display = 'block';
        } else {
          // Posts are visible, hide empty state
          emptyState.style.display = 'none';
        }
      }
    }
    
    // Commodity selection handling
    const commoditySelect = document.getElementById('commoditySelect');
    const selectedCommodityList = document.getElementById('selected-commodity');
    const commodityIdsInput = document.getElementById('commodity_ids');
    
    if (commoditySelect && selectedCommodityList && commodityIdsInput) {
        let selectedCommodities = [];  // Changed to array from Set
        
        // Set data-selected attribute for all options
        Array.from(commoditySelect.options).forEach(option => {
            option.dataset.selected = 'false';
        });
        
        commoditySelect.addEventListener('change', function() {
            const commodityId = this.value;
            const selectedOption = this.options[this.selectedIndex];
            
            if (commodityId && selectedOption.dataset.selected !== 'true') {
                // Mark option as selected
                selectedOption.dataset.selected = 'true';
                selectedCommodities.push(commodityId);
                
                // Create list item with remove button
                const li = document.createElement('li');
                li.style.position = 'relative';
                li.innerHTML = `
                    ${selectedOption.text}
                    <button class="remove-commodity-btn" data-commodity="${commodityId}" 
                            style="color: green; background-color: white; border: none; position: absolute; right: 0;">
                        <i class="fa fa-trash remove-commodity" aria-hidden="true"></i>
                    </button>
                `;
                
                selectedCommodityList.appendChild(li);
                updateTextarea();
                
                // Reset select
                this.selectedIndex = 0;
            }
        });
        
        // Handle remove button clicks
        selectedCommodityList.addEventListener('click', function(e) {
            const removeBtn = e.target.closest('.remove-commodity-btn');
            if (removeBtn) {
                const commodityId = removeBtn.dataset.commodity;
                
                // Remove from selected commodities array
                selectedCommodities = selectedCommodities.filter(id => id !== commodityId);
                
                // Reset option's selected state
                const option = commoditySelect.querySelector(`option[value="${commodityId}"]`);
                if (option) {
                    option.dataset.selected = 'false';
                }
                
                // Remove list item
                removeBtn.closest('li').remove();
                
                // Update textarea
                updateTextarea();
            }
        });
        
        // Function to update the textarea value
        function updateTextarea() {
            commodityIdsInput.value = selectedCommodities.join(',');
        }
    }

    function initForum() {
      // Tab functionality
      const tabButtons = document.querySelectorAll('.forum-tab');
      const tabContents = document.querySelectorAll('.forum-posts');
    
      if (tabButtons.length > 0 && tabContents.length > 0) {
        tabButtons.forEach(button => {
          button.addEventListener('click', function() {
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Get the target content
            const targetId = this.getAttribute('data-target');
            const targetContent = document.getElementById(targetId);
            
            if (targetContent) {
              // Hide all content
              tabContents.forEach(content => {
                if (content) {
                  content.style.display = 'none';
                }
              });
              
              // Show the target content
              targetContent.style.display = 'flex';
              
              // Check for empty state
              checkEmptyState(targetId);
            }
          });
        });
      }

      // Function to check if we need to show empty state
      function checkEmptyState(tabId) {
        const container = document.getElementById(tabId);
        if (!container) return;

        // Remove any existing empty state
        const existingEmptyState = container.querySelector('.forum-empty-state');
        if (existingEmptyState) {
          existingEmptyState.remove();
        }

        const visiblePosts = container.querySelectorAll('.discussion-post[style*="display: block"], .discussion-post:not([style*="display: none"])');
        
        if (visiblePosts.length === 0) {
          // Create empty state element
          const emptyState = document.createElement('div');
          emptyState.className = 'forum-empty-state';
          emptyState.innerHTML = `
            <div class="empty-state-content">
              <i class="fas fa-inbox fa-3x"></i>
              <h3>No Questions Yet</h3>
              <p>${tabId === 'popularQuestions' ? 'No popular questions available at the moment.' : 'Be the first to ask a question!'}</p>
              ${tabId === 'newQuestions' ? '<button class="ask-question-btn" data-toggle="modal" data-target="#questionModal"><i class="fas fa-plus-circle"></i> Ask Your Question</button>' : ''}
            </div>
          `;
          
          // Add styles to empty state
          emptyState.style.textAlign = 'center';
          emptyState.style.padding = '2rem';
          emptyState.style.margin = '2rem 0';
          emptyState.style.backgroundColor = '#f8f9fa';
          emptyState.style.borderRadius = '8px';
          
          // Add styles to empty state content
          const emptyStateContent = emptyState.querySelector('.empty-state-content');
          emptyStateContent.style.display = 'flex';
          emptyStateContent.style.flexDirection = 'column';
          emptyStateContent.style.alignItems = 'center';
          emptyStateContent.style.gap = '1rem';
          
          // Add styles to icon
          const icon = emptyState.querySelector('i');
          icon.style.color = '#6c757d';
          icon.style.marginBottom = '1rem';
          
          // Add styles to heading
          const heading = emptyState.querySelector('h3');
          heading.style.color = '#343a40';
          heading.style.marginBottom = '0.5rem';
          
          // Add styles to paragraph
          const paragraph = emptyState.querySelector('p');
          paragraph.style.color = '#6c757d';
          
          // Add styles to button if it exists
          const button = emptyState.querySelector('.ask-question-btn');
          if (button) {
            button.style.marginTop = '1rem';
            button.style.padding = '0.5rem 1rem';
            button.style.backgroundColor = '#2c6e49';
            button.style.color = 'white';
            button.style.border = 'none';
            button.style.borderRadius = '4px';
            button.style.cursor = 'pointer';
            button.style.display = 'flex';
            button.style.alignItems = 'center';
            button.style.gap = '0.5rem';
            
            // Add hover effect
            button.addEventListener('mouseover', () => {
              button.style.backgroundColor = '#1a472e';
            });
            button.addEventListener('mouseout', () => {
              button.style.backgroundColor = '#2c6e49';
            });
          }
          
          container.appendChild(emptyState);
        }
      }

      // Initialize empty state for active tab
      const activeTab = document.querySelector('.forum-tab.active');
      if (activeTab) {
        const activeTabId = activeTab.getAttribute('data-target');
        checkEmptyState(activeTabId);
      }
    
      // Topic pill selection
      const topicPills = document.querySelectorAll('.topic-pill');
    
      if (topicPills.length > 0) {
        topicPills.forEach(pill => {
          pill.addEventListener('click', function() {
            // Remove active class from all pills
            topicPills.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked pill
            this.classList.add('active');
            
            // Filter posts based on selected topic
            const topic = this.textContent.trim();
            
            if (topic === 'All Topics') {
              showAllPosts();
            } else {
              filterPostsByTopic(topic);
            }
          });
        });
      }
    
      // Filter checkbox functionality
      const commodityCheckboxes = document.querySelectorAll('input[name="commodity"]');
    
      if (commodityCheckboxes.length > 0) {
        commodityCheckboxes.forEach(checkbox => {
          checkbox.addEventListener('change', function() {
            const isAllCommodity = this.value === 'all';
            
            if (isAllCommodity && this.checked) {
              // If "All Commodities" is checked, uncheck all other options
              commodityCheckboxes.forEach(cb => {
                if (cb.value !== 'all') {
                  cb.checked = false;
                }
              });
              // Show all discussion posts
              const discussionPosts = document.querySelectorAll('.discussion-post');
              discussionPosts.forEach(post => {
                post.style.display = 'block';
              });
            } else if (!isAllCommodity && this.checked) {
              // If a specific commodity is checked, uncheck "All Commodities"
              const allCommodityCheckbox = document.querySelector('input[name="commodity"][value="all"]');
              if (allCommodityCheckbox) {
                allCommodityCheckbox.checked = false;
              }
              
              // Filter posts by the selected commodity
              filterPostsByCommodity();
            } else if (!isAllCommodity && !this.checked) {
              // If a specific commodity is unchecked, check if we need to show all again
              const anyChecked = Array.from(commodityCheckboxes).some(cb => cb.value !== 'all' && cb.checked);
              if (!anyChecked) {
                // If no specific commodities are checked, check "All Commodities" again
                const allCommodityCheckbox = document.querySelector('input[name="commodity"][value="all"]');
                if (allCommodityCheckbox) {
                  allCommodityCheckbox.checked = true;
                }
                // Show all discussion posts
                const discussionPosts = document.querySelectorAll('.discussion-post');
                discussionPosts.forEach(post => {
                  post.style.display = 'block';
                });
              } else {
                // Filter posts by the remaining checked commodities
                filterPostsByCommodity();
              }
            }
          });
        });
      }
    
      // Submit question button animation
      const submitQuestionBtn = document.getElementById('submitQuestion');
    
      if (submitQuestionBtn) {
        submitQuestionBtn.addEventListener('click', async function(e) {
          e.preventDefault();  // Prevent default form submission
          
          // Show loading state
          this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
          this.disabled = true;
          
          try {
            // Get the form data
            const form = document.getElementById('questionForm');
            if (!form) return;
            
            const formData = new FormData(form);
            
            // Submit the form
            const response = await fetch(form.action, {
              method: 'POST',
              body: formData,
              headers: {
                'X-Requested-With': 'XMLHttpRequest'
              }
            });
            
            const result = await response.json();
            
            if (result.success) {
              // If submission was successful
              $('#questionModal').modal('hide');
              showNotification('Question posted successfully!', 'success');
              
              // Refresh only the forum-posts div
              setTimeout(async () => {
                try {
                  const response = await fetch(window.location.href);
                  const text = await response.text();
                  const parser = new DOMParser();
                  const doc = parser.parseFromString(text, 'text/html');
                  const newForumPosts = doc.getElementById('forum-posts');
                  
                  if (newForumPosts) {
                    document.getElementById('forum-posts').innerHTML = newForumPosts.innerHTML;
                  }
                } catch (error) {
                  console.error('Error refreshing forum posts:', error);
                }
              }, 1000); // Wait for 1 second after showing notification before refreshing
            } else {
              // If submission failed
              showNotification(result.message || 'Failed to post question', 'error');
            }
          } catch (error) {
            showNotification('An error occurred while posting your question', 'error');
          } finally {
            // Reset button state
            this.innerHTML = 'Post Question';
            this.disabled = false;
          }
        });
      }
    }
});
            
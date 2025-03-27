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
      const visiblePosts = document.querySelectorAll(`#${activeTabId} .discussion-post[style*="display: block"]`);
      const emptyState = document.querySelector('.forum-empty-state');
      
      if (emptyState) {
        if (visiblePosts.length === 0) {
          // No visible posts, show empty state
          document.querySelector(`#${activeTabId}`).appendChild(emptyState);
          emptyState.style.display = 'block';
        } else {
          // Posts are visible, hide empty state
          emptyState.style.display = 'none';
        }
      }
    }
    
    // Filter menu functionality
    const filterButton = document.getElementById('filterButton');
    const filterMenu = document.getElementById('filterMenu');
    
    if (filterButton && filterMenu) {
      filterButton.addEventListener('click', function() {
        filterMenu.classList.toggle('show');
      });

      // Close filter menu when clicking outside
      document.addEventListener('click', function(e) {
        if (!filterButton.contains(e.target) && !filterMenu.contains(e.target)) {
          filterMenu.classList.remove('show');
        }
      });
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
});
            
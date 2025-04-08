$(document).ready(function () {
    // Initialize DataTables for discussions
    let discussionsTable = $('#discussionsTable').DataTable({
      language: {
        lengthMenu: '_MENU_',
        search: '',
        searchPlaceholder: 'Search discussions...'
      },
      lengthMenu: [
        [7, 10, 25, -1],
        [7, 10, 25, 'All']
      ],
      paging: true,
      lengthChange: true,
      autoWidth: false,
      bInfo: true,
      bSort: true,
      responsive: true,
      buttons: [
        {
          text: 'CSV',
          extend: 'csv'
        },
        {
          text: 'PDF',
          extend: 'pdf'
        }
      ],
      dom: '<"row"<"col-md-1"l><"col-md-8"B><"col-md-3"f>>' + 
           '<"row"<"col-md-12"tr>>' + 
           '<"row"<"col-md-5"i><"col-md-7"p>>'
    });
  
    // Initialize DataTables for comments
    let commentsTable = $('#commentsTable').DataTable({
      language: {
        lengthMenu: '_MENU_',
        search: '',
        searchPlaceholder: 'Search comments...'
      },
      lengthMenu: [
        [7, 10, 25, -1],
        [7, 10, 25, 'All']
      ],
      paging: true,
      lengthChange: true,
      autoWidth: false,
      bInfo: true,
      bSort: true,
      responsive: true,
      buttons: [
        {
          text: 'CSV',
          extend: 'csv'
        },
        {
          text: 'PDF',
          extend: 'pdf'
        }
      ],
      dom: '<"row"<"col-md-1"l><"col-md-8"B><"col-md-3"f>>' + 
           '<"row"<"col-md-12"tr>>' + 
           '<"row"<"col-md-5"i><"col-md-7"p>>'
    });
  
    // Filter discussions based on status
    $('#statusFilter').on('change', function() {
      const status = $(this).val();
      if (status === 'all') {
        discussionsTable.columns(5).search('').draw();
      } else {
        discussionsTable.columns(5).search(status).draw();
      }
    });
  
    // Filter comments based on status
    $('#commentStatusFilter').on('change', function() {
      const status = $(this).val();
      if (status === 'all') {
        commentsTable.columns(5).search('').draw();
      } else {
        commentsTable.columns(5).search(status).draw();
      }
    });
  
    // Initialize charts
    initializeCharts();
  
    // EVENT HANDLERS
  
    // Create Discussion Button Click
    $('#createDiscussionBtn').on('click', function() {
      $('#createDiscussionModal').modal('show');
    });
  
    // Save New Discussion Button Click
    $('#createNewDiscussionBtn').on('click', function() {
      // Validate form
      const form = $('#createDiscussionForm')[0];
      if (form.checkValidity() === false) {
        form.reportValidity();
        return;
      }
  
      // Show confirmation dialog
      Swal.fire({
        title: 'Create Discussion',
        text: 'Are you sure you want to create this discussion?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, create it!',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating discussion creation success
          Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: 'Discussion has been created successfully.'
          }).then(() => {
            // Close modal and refresh page
            $('#createDiscussionModal').modal('hide');
            // In a real application, submit form data to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // View Discussion Button Click
    $(document).on('click', '.view-btn', function() {
      const discussionId = $(this).data('id');
      
      // In a real application, fetch discussion details from the server
      // For demo, we use mock data
      const mockDiscussion = {
        id: discussionId,
        title: 'Sample Discussion Title',
        author: 'John Doe',
        commodity: 'Rice',
        date: '2025-03-18',
        content: 'This is a sample discussion content. It would typically be much longer and contain detailed information about the topic at hand.',
        comments: [
          { author: 'Jane Smith', date: '2025-03-19', content: 'This is a great discussion! Thanks for sharing.' },
          { author: 'Bob Johnson', date: '2025-03-20', content: 'I have a question about this topic...' }
        ]
      };
  
      // Populate modal with discussion data
      $('#view-discussion-title').text(mockDiscussion.title);
      $('#view-discussion-author').text(mockDiscussion.author);
      $('#view-discussion-commodity').text(mockDiscussion.commodity);
      $('#view-discussion-date').text(mockDiscussion.date);
      $('#view-discussion-content').html(mockDiscussion.content);
      $('#view-discussion-comment-count').text(mockDiscussion.comments.length);
  
      // Populate comments
      const commentsHtml = mockDiscussion.comments.map(comment => `
        <div class="comment-item">
          <div class="comment-meta">
            <strong>${comment.author}</strong> • ${comment.date}
          </div>
          <div class="comment-content">
            ${comment.content}
          </div>
        </div>
      `).join('');
      
      $('#view-discussion-comments').html(commentsHtml || '<p class="text-center">No comments yet</p>');
  
      // Show modal
      $('#viewDiscussionModal').modal('show');
    });
  
    // Edit Discussion Button Click
    $(document).on('click', '.edit-btn', function() {
      const discussionId = $(this).data('id');
      
      // In a real application, fetch discussion details from the server
      // For demo, we use mock data
      const mockDiscussion = {
        id: discussionId,
        title: 'Sample Discussion Title',
        commodity_id: 1,
        content: 'This is a sample discussion content. It would typically be much longer and contain detailed information about the topic at hand.',
        status: 'active'
      };
  
      // Populate edit form
      $('#edit-discussion-id').val(mockDiscussion.id);
      $('#edit-discussion-title').val(mockDiscussion.title);
      $('#edit-discussion-commodity').val(mockDiscussion.commodity_id);
      $('#edit-discussion-content').val(mockDiscussion.content);
      $('#edit-discussion-status').val(mockDiscussion.status);
  
      // Show modal
      $('#editDiscussionModal').modal('show');
    });
  
    // Save Edited Discussion Button Click
    $('#saveDiscussionBtn').on('click', function() {
      // Validate form
      const form = $('#editDiscussionForm')[0];
      if (form.checkValidity() === false) {
        form.reportValidity();
        return;
      }
  
      // Show confirmation dialog
      Swal.fire({
        title: 'Save Changes',
        text: 'Are you sure you want to save these changes?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, save changes',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating update success
          Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: 'Discussion has been updated successfully.'
          }).then(() => {
            // Close modal and refresh page
            $('#editDiscussionModal').modal('hide');
            // In a real application, submit form data to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // View Comment Button Click
    $(document).on('click', '.view-comment-btn', function() {
      const commentId = $(this).data('id');
      
      // In a real application, fetch comment details from the server
      // For demo, we use mock data
      const mockComment = {
        id: commentId,
        author: 'Jane Smith',
        discussion: 'Best farming techniques',
        date: '2025-03-19',
        status: 'Pending',
        content: 'This is a sample comment content that might need moderation.'
      };
  
      // Populate modal with comment data
      $('#view-comment-author').text(mockComment.author);
      $('#view-comment-discussion').text(mockComment.discussion);
      $('#view-comment-date').text(mockComment.date);
      $('#view-comment-status').text(mockComment.status);
      $('#view-comment-content').text(mockComment.content);
  
      // Show/hide approve button based on status
      if (mockComment.status.toLowerCase() === 'approved') {
        $('#approveCommentModalBtn').hide();
      } else {
        $('#approveCommentModalBtn').show();
      }
  
      // Set data attributes for action buttons
      $('#approveCommentModalBtn').data('id', commentId);
      $('#deleteCommentModalBtn').data('id', commentId);
  
      // Show modal
      $('#viewCommentModal').modal('show');
    });
  
    // Delete Discussion Button Click
    $(document).on('click', '.delete-btn', function() {
      const discussionId = $(this).data('id');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Delete Discussion',
        text: 'Are you sure you want to delete this discussion? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#d33'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating deletion success
          Swal.fire({
            icon: 'success',
            title: 'Deleted!',
            text: 'The discussion has been deleted.'
          }).then(() => {
            // In a real application, send delete request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Pin/Unpin Discussion Button Click
    $(document).on('click', '.pin-btn, .unpin-btn', function() {
      const discussionId = $(this).data('id');
      const isPinning = $(this).hasClass('pin-btn');
      const action = isPinning ? 'pin' : 'unpin';
      
      // Show confirmation dialog
      Swal.fire({
        title: isPinning ? 'Pin Discussion' : 'Unpin Discussion',
        text: `Are you sure you want to ${action} this discussion?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: `Yes, ${action} it!`,
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating action success
          Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: `The discussion has been ${action}ned.`
          }).then(() => {
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Archive/Restore Discussion Button Click
    $(document).on('click', '.archive-btn, .restore-btn', function() {
      const discussionId = $(this).data('id');
      const isArchiving = $(this).hasClass('archive-btn');
      const action = isArchiving ? 'archive' : 'restore';
      
      // Show confirmation dialog
      Swal.fire({
        title: isArchiving ? 'Archive Discussion' : 'Restore Discussion',
        text: `Are you sure you want to ${action} this discussion?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: `Yes, ${action} it!`,
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating action success
          Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: `The discussion has been ${action}d.`
          }).then(() => {
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Approve Comment Button Click (from modal)
    $('#approveCommentModalBtn').on('click', function() {
      const commentId = $(this).data('id');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Approve Comment',
        text: 'Are you sure you want to approve this comment?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, approve it!',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating approval success
          Swal.fire({
            icon: 'success',
            title: 'Approved!',
            text: 'The comment has been approved.'
          }).then(() => {
            // Close modal and refresh page
            $('#viewCommentModal').modal('hide');
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Delete Comment Button Click (from modal)
    $('#deleteCommentModalBtn').on('click', function() {
      const commentId = $(this).data('id');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Delete Comment',
        text: 'Are you sure you want to delete this comment? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#d33'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating deletion success
          Swal.fire({
            icon: 'success',
            title: 'Deleted!',
            text: 'The comment has been deleted.'
          }).then(() => {
            // Close modal and refresh page
            $('#viewCommentModal').modal('hide');
            // In a real application, send delete request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Approve Comment Button Click (from table)
    $(document).on('click', '.approve-comment-btn', function() {
      const commentId = $(this).data('id');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Approve Comment',
        text: 'Are you sure you want to approve this comment?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, approve it!',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating approval success
          Swal.fire({
            icon: 'success',
            title: 'Approved!',
            text: 'The comment has been approved.'
          }).then(() => {
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Delete Comment Button Click (from table)
    $(document).on('click', '.delete-comment-btn', function() {
      const commentId = $(this).data('id');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Delete Comment',
        text: 'Are you sure you want to delete this comment? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#d33'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating deletion success
          Swal.fire({
            icon: 'success',
            title: 'Deleted!',
            text: 'The comment has been deleted.'
          }).then(() => {
            // In a real application, send delete request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // View Reported Discussion Button Click
    $(document).on('click', '.view-reported-discussion-btn', function() {
      const reportId = $(this).data('id');
      
      // In a real application, fetch report details from the server
      // For demo, we use mock data
      const mockReport = {
        id: reportId,
        reported_by: 'Jane Smith',
        date_reported: '2025-03-20',
        reason: 'Inappropriate content',
        comments: 'This discussion contains content that violates community guidelines.',
        content_type: 'Discussion',
        content_author: 'John Doe',
        content_date: '2025-03-18',
        content: 'This is the reported discussion content.'
      };
  
      // Populate modal with report data
      $('#report-user').text(mockReport.reported_by);
      $('#report-date').text(mockReport.date_reported);
      $('#report-reason').text(mockReport.reason);
      $('#report-comments').text(mockReport.comments);
      $('#reported-content-type').text(mockReport.content_type);
      $('#reported-content-author').text(mockReport.content_author);
      $('#reported-content-date').text(mockReport.content_date);
      $('#reported-content').text(mockReport.content);
  
      // Set data attributes for action buttons
      $('#dismissReportBtn').data('id', reportId);
      $('#dismissReportBtn').data('type', 'discussion');
      $('#removeReportedContentBtn').data('id', reportId);
      $('#removeReportedContentBtn').data('type', 'discussion');
  
      // Show modal
      $('#reportDetailsModal').modal('show');
    });
  
    // View Reported Comment Button Click
    $(document).on('click', '.view-reported-comment-btn', function() {
      const reportId = $(this).data('id');
      
      // In a real application, fetch report details from the server
      // For demo, we use mock data
      const mockReport = {
        id: reportId,
        reported_by: 'Bob Johnson',
        date_reported: '2025-03-21',
        reason: 'Spam',
        comments: 'This comment appears to be spam.',
        content_type: 'Comment',
        content_author: 'Jane Smith',
        content_date: '2025-03-19',
        content: 'This is the reported comment content.'
      };
  
      // Populate modal with report data
      $('#report-user').text(mockReport.reported_by);
      $('#report-date').text(mockReport.date_reported);
      $('#report-reason').text(mockReport.reason);
      $('#report-comments').text(mockReport.comments);
      $('#reported-content-type').text(mockReport.content_type);
      $('#reported-content-author').text(mockReport.content_author);
      $('#reported-content-date').text(mockReport.content_date);
      $('#reported-content').text(mockReport.content);
  
      // Set data attributes for action buttons
      $('#dismissReportBtn').data('id', reportId);
      $('#dismissReportBtn').data('type', 'comment');
      $('#removeReportedContentBtn').data('id', reportId);
      $('#removeReportedContentBtn').data('type', 'comment');
  
      // Show modal
      $('#reportDetailsModal').modal('show');
    });
  
    // Dismiss Report Button Click
    $(document).on('click', '.dismiss-report-btn, #dismissReportBtn', function() {
      const reportId = $(this).data('id');
      const reportType = $(this).data('type');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Dismiss Report',
        text: 'Are you sure you want to dismiss this report?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, dismiss it',
        cancelButtonText: 'Cancel'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating dismissal success
          Swal.fire({
            icon: 'success',
            title: 'Dismissed!',
            text: 'The report has been dismissed.'
          }).then(() => {
            // Close modal if open
            $('#reportDetailsModal').modal('hide');
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  
    // Remove Reported Content Button Click
    $(document).on('click', '.remove-content-btn, #removeReportedContentBtn', function() {
      const contentId = $(this).data('id');
      const contentType = $(this).data('type');
      
      // Show confirmation dialog
      Swal.fire({
        title: 'Remove Content',
        text: `Are you sure you want to remove this ${contentType}? This action cannot be undone.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, remove it',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#d33'
      }).then((result) => {
        if (result.isConfirmed) {
          // Simulating removal success
          Swal.fire({
            icon: 'success',
            title: 'Removed!',
            text: `The ${contentType} has been removed.`
          }).then(() => {
            // Close modal if open
            $('#reportDetailsModal').modal('hide');
            // In a real application, send request to server and reload data
            // window.location.reload();
          });
        }
      });
    });
  });
  
  /**
   * Initialize dashboard charts
   */
  function initializeCharts() {
    // Forum Activity Chart
    const forumActivityCtx = document.getElementById('forumActivityChart');
    if (forumActivityCtx) {
      // Sample data for the forum activity chart
      const dates = [];
      const discussions = [];
      const comments = [];
      
      // Generate last 30 days
      const today = new Date();
      for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Random data for discussions and comments
        discussions.push(Math.floor(Math.random() * 10));
        comments.push(Math.floor(Math.random() * 20));
      }
      
      new Chart(forumActivityCtx, {
        type: 'line',
        data: {
          labels: dates,
          datasets: [
            {
              label: 'New Discussions',
              data: discussions,
              borderColor: '#0C356A',
              backgroundColor: 'rgba(12, 53, 106, 0.1)',
              borderWidth: 2,
              tension: 0.4,
              fill: true
            },
            {
              label: 'New Comments',
              data: comments,
              borderColor: '#28a745',
              backgroundColor: 'rgba(40, 167, 69, 0.1)',
              borderWidth: 2,
              tension: 0.4,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            x: {
              ticks: {
                maxRotation: 0,
                autoSkip: true,
                maxTicksLimit: 10
              }
            },
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0
              }
            }
          }
        }
      });
    }
  
    // Topic Distribution Chart
    const topicDistributionCtx = document.getElementById('topicDistributionChart');
    if (topicDistributionCtx) {
      // Sample data for the topic distribution chart
      const topics = ['Rice', 'Corn', 'Coconut', 'Aquaculture', 'Other'];
      const discussionCounts = [25, 18, 15, 12, 10];
      
      new Chart(topicDistributionCtx, {
        type: 'doughnut',
        data: {
          labels: topics,
          datasets: [{
            data: discussionCounts,
            backgroundColor: [
              '#0C356A',
              '#28a745',
              '#ffc107',
              '#17a2b8',
              '#6c757d'
            ],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const percentage = Math.round((value / total) * 100);
                  return `${label}: ${value} (${percentage}%)`;
                }
              }
            }
          }
        }
      });
    }
  }
  
  /**
   * Sparkline initialization for dashboard counters
   * Note: This function assumes the sparkline plugin is available
   */
  function initializeSparklines() {
    // Forum posts sparkline
    $("#sparklinedash").sparkline([5, 6, 7, 8, 9, 10, 12, 13, 15, 14, 13, 12, 10, 9, 8, 10, 12, 14, 15, 16], {
      type: 'line',
      width: '100%',
      height: '50',
      lineColor: '#28a745',
      fillColor: 'rgba(40, 167, 69, 0.2)',
      highlightLineColor: 'rgba(0, 0, 0, .1)',
      highlightSpotColor: 'rgba(0, 0, 0, .2)'
    });
  
    // Active discussions sparkline
    $("#sparklinedash2").sparkline([0, 5, 6, 10, 9, 12, 4, 9, 12, 10, 9, 12, 10, 15, 12, 14, 16, 12, 10, 9], {
      type: 'line',
      width: '100%',
      height: '50',
      lineColor: '#007bff',
      fillColor: 'rgba(0, 123, 255, 0.2)',
      highlightLineColor: 'rgba(0, 0, 0, .1)',
      highlightSpotColor: 'rgba(0, 0, 0, .2)'
    });
  
    // Comments sparkline
    $("#sparklinedash3").sparkline([2, 4, 6, 8, 10, 12, 14, 16, 14, 12, 10, 8, 6, 4, 2, 4, 6, 8, 10, 12], {
      type: 'line',
      width: '100%',
      height: '50',
      lineColor: '#6f42c1',
      fillColor: 'rgba(111, 66, 193, 0.2)',
      highlightLineColor: 'rgba(0, 0, 0, .1)',
      highlightSpotColor: 'rgba(0, 0, 0, .2)'
    });
  
    // Reactions sparkline
    $("#sparklinedash4").sparkline([5, 10, 15, 20, 25, 20, 15, 10, 5, 10, 15, 20, 25, 20, 15, 10, 5, 10, 15, 20], {
      type: 'line',
      width: '100%',
      height: '50',
      lineColor: '#dc3545',
      fillColor: 'rgba(220, 53, 69, 0.2)',
      highlightLineColor: 'rgba(0, 0, 0, .1)',
      highlightSpotColor: 'rgba(0, 0, 0, .2)'
    });
  }
  
  // Call sparkline initialization when the document is ready
  $(document).ready(function() {
    // Check if sparkline plugin is available
    if ($.fn.sparkline) {
      initializeSparklines();
    }
  });
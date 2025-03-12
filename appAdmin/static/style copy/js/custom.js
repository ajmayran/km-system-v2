// Load the admin navbar into the page
document.addEventListener('DOMContentLoaded', function() {
    fetch('admin-navbar.html')
      .then(response => response.text())
      .then(data => {
        document.getElementById('admin-navbar').innerHTML = data;
        initSidebar();
      });
    
    // Initialize the page loader
    window.addEventListener('load', function load() {
      const loader = document.getElementById('loader');
      setTimeout(function() {
        loader.classList.add('fadeOut');
      }, 300);
    });
  });
  
  // Sidebar functionality
  function initSidebar() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', function() {
        document.body.classList.toggle('sidebar-hidden');
      });
    }
    
    // Dropdown menus in sidebar
    const dropdownToggles = document.querySelectorAll('.sidebar-menu .dropdown-toggle');
    dropdownToggles.forEach(toggle => {
      toggle.addEventListener('click', function(e) {
        e.preventDefault();
        const parent = this.parentElement;
        parent.classList.toggle('open');
      });
    });
    
    // Mobile toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    if (mobileToggle) {
      mobileToggle.addEventListener('click', function(e) {
        e.preventDefault();
        document.body.classList.toggle('sidebar-mobile-open');
      });
    }
  }
  
  // Initialize DataTables if present
  function initDataTables() {
    if (typeof $.fn.DataTable !== 'undefined') {
      $('.data-table').DataTable({
        responsive: true,
        dom: 'Bfrtip',
        buttons: ['copy', 'csv', 'excel', 'pdf', 'print']
      });
    }
  }
  
  // Initialize search functionality
  function initSearch() {
    const searchToggle = document.querySelector('.search-toggle');
    if (searchToggle) {
      searchToggle.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector('.header').classList.toggle('search-active');
      });
    }
  }
  
  // Initialize any Select2 dropdowns
  function initSelect2() {
    if (typeof $.fn.select2 !== 'undefined') {
      $('.select2').select2();
    }
  }
  
  // Call initialization functions
  document.addEventListener('DOMContentLoaded', function() {
    initSearch();
    initSelect2();
    initDataTables();
  });
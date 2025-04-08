document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const mobileView = document.getElementById('mobileView');
    const dropdowns = document.querySelectorAll('.dropdown-fa-toggle-down');

    // Toggle mobile menu
    hamburger.addEventListener('click', function() {
        mobileView.classList.toggle('visible');
        this.classList.toggle('active');
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!mobileView.contains(event.target) && !hamburger.contains(event.target)) {
            mobileView.classList.remove('visible');
            hamburger.classList.remove('active');
        }
    });

    // Handle dropdowns in mobile view
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            if (window.innerWidth <= 992) {
                e.preventDefault();
                const menu = this.nextElementSibling;
                const isOpen = menu.style.display === 'block';
                
                // Close all other dropdowns
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    menu.style.display = 'none';
                });
                
                // Toggle current dropdown
                menu.style.display = isOpen ? 'none' : 'block';
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
});
  
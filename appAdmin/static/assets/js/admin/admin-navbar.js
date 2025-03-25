function expandNav() {
    var nav_texts = document.getElementsByClassName('nav-text');
    var arrow = document.getElementById('arrow');
    var logoImage = document.querySelector('.logo-image img');
    var verticalLine = document.querySelector('.logo-image::after'); // Select the vertical line pseudo-element
    var dropdownTxt = document.getElementsByClassName('dropdown-text');
    var mainContent = document.getElementById('main-content');


    document.getElementById('navbar').style.width = '240px';
    mainContent.style.width = 'calc(100% - 240px)';
    mainContent.style.left = '240px';

    Array.from(nav_texts).forEach(element => {
        element.style.display = 'block';
        setTimeout(function () {
            element.style.opacity = '1';
        }, 250);
    });

     // Update main-content class
     mainContent.classList.remove('retracted');
     mainContent.classList.add('expanded');

    Array.from(dropdownTxt).forEach(element => {
        element.style.display = 'block';
        setTimeout(function () {
            element.style.opacity = '1';
        }, 250);
    });

    arrow.style.display = 'block';

    // Set logo image width to 40px when expanding the nav
    if (logoImage) {
        logoImage.style.maxWidth = '150px';
    }

    // Display the vertical line after the logo when expanding the nav
    if (verticalLine) {
        verticalLine.style.display = 'block';
    }
}

function retractNav() {
    var navbar = document.getElementById('navbar');
    var mainContent = document.getElementById('main-content');
    var navTexts = document.getElementsByClassName('nav-text');
    var dropdownTxt = document.getElementsByClassName('dropdown-text');
    var logoImage = document.querySelector('.logo-image img');
    var arrow = document.getElementById('arrow');
    var verticalLine = document.querySelector('.logo-image::after'); // Select the vertical line pseudo-element

    navbar.style.width = '80px';
    mainContent.style.width = 'calc(100% - 80px)';
    mainContent.style.left = '80px';

    Array.from(navTexts).forEach(element => {
        element.style.opacity = '0';
        setTimeout(function () {
            element.style.display = 'none';
        }, 400);
    });

     // Update main-content class
     mainContent.classList.remove('expanded');
     mainContent.classList.add('retracted');

    Array.from(dropdownTxt).forEach(element => {
        element.style.opacity = '0';
        setTimeout(function () {
            element.style.display = 'none';
        }, 400);
    });

    arrow.style.display = 'none';

    // Set logo image width to 40px when retracting the nav
    if (logoImage) {
        logoImage.style.maxWidth = '55px';
    }

     // Hide the vertical line after the logo when retracting the nav
     if (verticalLine) {
        verticalLine.style.display = 'none';
    }
}

// Toggle variable to track the state of the navbar
var toggle = true;

// Click event handler for the toggle button
$(document).on('click', '#toggle-nav-btn', function () {
    if (toggle) {
        retractNav();
        toggle = false;
    } else {
        expandNav();
        toggle = true;
    }
});

// Function to check the window size and retract/expand the navbar accordingly
function checkWindowSize() {
    var currentPage = window.location.pathname; // Get the current page URL path

    if (window.innerWidth <= 1024 && currentPage !== '/main-content') {
        retractNav();
        toggle = false;
    } else {
        expandNav();
        toggle = true;
    }
}


// Call checkWindowSize on load and when the window is resized
window.addEventListener('resize', checkWindowSize);
checkWindowSize();

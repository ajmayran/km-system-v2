// AANR Knowledge Hub JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll)
    AOS.init({
      duration: 800,
      easing: 'ease-in-out',
      once: true,
      offset: 100
    });
  
    // Counter Animation for Stats
    const counters = document.querySelectorAll('.counter-animation');
    
    // Intersection Observer for counters
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    
    // Add observer to all counters
    counters.forEach(counter => {
      counterObserver.observe(counter);
    });
    
    // Function to animate counter
    function animateCounter(counter) {
      const target = parseInt(counter.getAttribute('data-count'));
      const duration = 2000; // 2 seconds
      const step = Math.ceil(target / (duration / 16)); // ~60fps
      let current = 0;
      
      const updateCounter = () => {
        current += step;
        if (current > target) {
          current = target;
        }
        counter.textContent = current.toLocaleString();
        
        if (current < target) {
          requestAnimationFrame(updateCounter);
        }
      };
      
      updateCounter();
    }
  
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle) {
      mobileMenuToggle.addEventListener('click', function() {
        this.classList.toggle('active');
        navMenu.classList.toggle('active');
      });
    }
  
    // Search form animation
    const searchInput = document.querySelector('.search-input');
    
    if (searchInput) {
      searchInput.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
      });
      
      searchInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
      });
    }
  
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        
        if (targetId === '#') return;
        
        e.preventDefault();
        
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop - 80, // Adjust for header height
            behavior: 'smooth'
          });
        }
      });
    });
  
    // Parallax effect for hero section
    const heroSection = document.querySelector('.hero-section');
    const heroImage = document.querySelector('.hero-bg');
    
    if (heroSection && heroImage) {
      window.addEventListener('scroll', function() {
        const scrollPosition = window.pageYOffset;
        const parallaxSpeed = 0.5;
        
        // Only apply effect when hero section is visible
        if (scrollPosition < heroSection.offsetHeight) {
          heroImage.style.transform = `translateY(${scrollPosition * parallaxSpeed}px)`;
        }
      });
    }
  
    // Resource card hover effects
    const resourceCards = document.querySelectorAll('.resource-card');
    
    resourceCards.forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.querySelector('.resource-title').style.color = 'var(--primary)';
      });
      
      card.addEventListener('mouseleave', function() {
        this.querySelector('.resource-title').style.color = 'var(--dark)';
      });
    });
  
    // Initialize custom scroll reveal animation
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const fadeObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    fadeElements.forEach(element => {
      fadeObserver.observe(element);
    });
  });
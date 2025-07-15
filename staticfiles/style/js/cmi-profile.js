document.addEventListener('DOMContentLoaded', function () {
    // Get DOM elements
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const profileUpload = document.getElementById('profile-upload');
    const profileImage = document.getElementById('profile-image');
    const uploadOptions = document.getElementById('upload-options');
    const notification = document.getElementById('notification');

    // Info display and edit sections
    const basicInfoDisplay = document.getElementById('basic-info-display');
    const basicInfoEdit = document.getElementById('basic-info-edit');
    const profInfoDisplay = document.getElementById('prof-info-display');
    const profInfoEdit = document.getElementById('prof-info-edit');
    const contactInfoDisplay = document.getElementById('contact-info-display');
    const contactInfoEdit = document.getElementById('contact-info-edit');

    // Form elements
    const firstName = document.getElementById('first-name');
    const middleName = document.getElementById('middle-name');
    const lastName = document.getElementById('last-name');
    const email = document.getElementById('email');
    const dateBirth = document.getElementById('date-birth');
    const sex = document.getElementById('sex');
    const gender = document.getElementById('gender');
    const institution = document.getElementById('institution');
    const position = document.getElementById('position');
    const specialization = document.getElementById('specialization');
    const highestEduc = document.getElementById('highest-educ');
    const contactNum = document.getElementById('contact-num');

    // Display elements
    const fullNameDisplay = document.getElementById('full-name');
    const emailDisplay = document.getElementById('email-display');
    const dobDisplay = document.getElementById('dob-display');
    const sexDisplay = document.getElementById('sex-display');
    const genderDisplay = document.getElementById('gender-display');
    const institutionDisplay = document.getElementById('institution-display');
    const positionDisplay = document.getElementById('position-display');
    const specializationDisplay = document.getElementById('specialization-display');
    const educationDisplay = document.getElementById('education-display');
    const userTypeDisplay = document.getElementById('user-type-display');
    const contactNumDisplay = document.getElementById('contact-num-display');

    // Current user data
    let userData = {
        firstName: "Maria",
        middleName: "Garcia",
        lastName: "Santos",
        email: "maria.santos@wesmaarrdec.org",
        dateBirth: "1988-05-15",
        sex: "Female",
        gender: "Female",
        institution: "Western Mindanao State University",
        position: "Research Specialist",
        specialization: "Agricultural Economics",
        highestEduc: "Masters",
        userType: "cmi",
        contactNum: "+63 912 345 6789"
    };

    // Original profile image URL
    let originalImageUrl = profileImage.src;
    // Variable to track editing state
    let isEditing = false;

    // Add event listeners
    editProfileBtn.addEventListener('click', toggleEditMode);
    profileUpload.addEventListener('change', handleProfileImageChange);

    // Function to toggle between view and edit modes
    function toggleEditMode() {
        isEditing = !isEditing;

        if (isEditing) {
            // Switch to edit mode
            editProfileBtn.innerHTML = '<i class="fas fa-save"></i><span>Save Profile</span>';
            editProfileBtn.classList.add('active');

            // Show edit forms, hide displays
            basicInfoDisplay.classList.add('hidden');
            basicInfoEdit.classList.add('show');
            basicInfoEdit.classList.remove('hidden');

            profInfoDisplay.classList.add('hidden');
            profInfoEdit.classList.add('show');
            profInfoEdit.classList.remove('hidden');

            contactInfoDisplay.classList.add('hidden');
            contactInfoEdit.classList.add('show');
            contactInfoEdit.classList.remove('hidden');

            // Add animation to form fields
            animateFormFields();
        } else {
            // Save the changes
            saveChanges();

            // Switch back to display mode
            editProfileBtn.innerHTML = '<i class="fas fa-edit"></i><span>Edit Profile</span>';
            editProfileBtn.classList.remove('active');

            // Show displays, hide edit forms
            basicInfoDisplay.classList.remove('hidden');
            basicInfoEdit.classList.remove('show');
            basicInfoEdit.classList.add('hidden');

            profInfoDisplay.classList.remove('hidden');
            profInfoEdit.classList.remove('show');
            profInfoEdit.classList.add('hidden');

            contactInfoDisplay.classList.remove('hidden');
            contactInfoEdit.classList.remove('show');
            contactInfoEdit.classList.add('hidden');

            // Show success notification
            showNotification();
        }
    }

    // Function to handle profile image change
    function handleProfileImageChange(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                profileImage.src = e.target.result;
                // Show upload options with animation
                uploadOptions.classList.remove('hidden');
                setTimeout(() => {
                    uploadOptions.classList.add('show');
                }, 10);
            };
            reader.readAsDataURL(file);
        }
    }

    // Function to save form changes
    function saveChanges() {
        // Update user data with form values
        userData.firstName = firstName.value;
        userData.middleName = middleName.value;
        userData.lastName = lastName.value;
        userData.email = email.value;
        userData.dateBirth = dateBirth.value;
        userData.sex = sex.value;
        userData.gender = gender.value;
        userData.institution = institution.value;
        userData.position = position.value;
        userData.specialization = specialization.value;
        userData.highestEduc = highestEduc.value;
        userData.contactNum = contactNum.value;

        // Update display elements
        updateDisplayValues();
    }

    // Function to update display values
    function updateDisplayValues() {
        // Format date of birth for display
        const dob = new Date(userData.dateBirth);
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        const formattedDob = dob.toLocaleDateString('en-US', options);

        // Update basic info
        fullNameDisplay.textContent = `${userData.firstName} ${userData.middleName ? userData.middleName + ' ' : ''}${userData.lastName}`;
        emailDisplay.textContent = userData.email;
        dobDisplay.textContent = formattedDob;
        sexDisplay.textContent = userData.sex;
        genderDisplay.textContent = userData.gender;

        // Update professional info
        institutionDisplay.textContent = userData.institution;
        positionDisplay.textContent = userData.position;
        specializationDisplay.textContent = userData.specialization;
        educationDisplay.textContent = `${userData.highestEduc} Degree`;

        // Update user type display with proper formatting
        let displayUserType = "User";
        if (userData.userType === "cmi") {
            displayUserType = "CMI User";
        } else if (userData.userType === "secretariat") {
            displayUserType = "Secretariat";
        } else if (userData.userType === "admin") {
            displayUserType = "Administrator";
        }
        userTypeDisplay.textContent = displayUserType;

        // Update contact info
        contactNumDisplay.textContent = userData.contactNum;
    }

    // Function to show notification
    function showNotification() {
        notification.classList.remove('hidden');
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.classList.add('hidden');
            }, 300);
        }, 3000);
    }

    // Function to animate form fields
    function animateFormFields() {
        const inputs = document.querySelectorAll('.info-edit input, .info-edit select');
        inputs.forEach((input, index) => {
            setTimeout(() => {
                input.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                input.style.transform = 'translateY(0)';
                input.style.opacity = '1';
            }, 50 * index);
        });
    }

    // Add animation to profile sections on page load
    function animateProfileSections() {
        const sections = document.querySelectorAll('.section-container');
        sections.forEach((section, index) => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';

            setTimeout(() => {
                section.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
                section.style.transform = 'translateY(0)';
                section.style.opacity = '1';
            }, 100 * index);
        });
    }

    // Initialize animations
    animateProfileSections();

    // Add hover animations to activity items
    function setupActivityAnimations() {
        const activityItems = document.querySelectorAll('.activity-item');

        activityItems.forEach(item => {
            item.addEventListener('mouseenter', () => {
                item.style.borderLeftWidth = '8px';
            });

            item.addEventListener('mouseleave', () => {
                item.style.borderLeftWidth = '4px';
            });
        });
    }

    setupActivityAnimations();

    // Add ripple effect to buttons
    function createRippleEffect() {
        const buttons = document.querySelectorAll('button');

        buttons.forEach(button => {
            button.addEventListener('click', function (e) {
                const ripple = document.createElement('span');
                const rect = button.getBoundingClientRect();

                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;

                ripple.style.width = ripple.style.height = `${size}px`;
                ripple.style.left = `${x}px`;
                ripple.style.top = `${y}px`;
                ripple.className = 'ripple';

                // Remove existing ripples
                const currentRipple = button.querySelector('.ripple');
                if (currentRipple) {
                    currentRipple.remove();
                }

                button.appendChild(ripple);

                // Remove ripple after animation completes
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    }

    // Add CSS for ripple effect
    function addRippleStyle() {
        const style = document.createElement('style');
        style.textContent = `
        button {
          position: relative;
          overflow: hidden;
        }
        
        .ripple {
          position: absolute;
          border-radius: 50%;
          background-color: rgba(255, 255, 255, 0.4);
          transform: scale(0);
          animation: ripple 0.6s linear;
          pointer-events: none;
        }
        
        @keyframes ripple {
          to {
            transform: scale(2.5);
            opacity: 0;
          }
        }
      `;
        document.head.appendChild(style);
    }

    addRippleStyle();
    createRippleEffect();

    // Add parallax effect to profile header
    function setupParallaxEffect() {
        const profileHeader = document.querySelector('.profile-header');

        window.addEventListener('scroll', () => {
            const scrollPosition = window.scrollY;
            if (scrollPosition < 200) {
                profileHeader.style.backgroundPosition = `center ${scrollPosition * 0.5}px`;
            }
        });
    }

    setupParallaxEffect();

});
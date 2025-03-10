document.addEventListener("DOMContentLoaded", function () {
    const hamburger = document.querySelector(".hamburger");
    const mobileView = document.querySelector(".mobileView");

    if (hamburger) {
        hamburger.addEventListener("click", function () {
            mobileView.style.display = mobileView.style.display === "block" ? "none" : "block";
        });
    }

    function adjustFontSize() {
        if (window.innerWidth <= 1340) {
            document.querySelectorAll(".footer .about, .footer .info, .footer .socials, .footer .links")
                .forEach(el => el.style.fontSize = "10px");
        } else {
            document.querySelectorAll(".footer .about, .footer .info, .footer .socials, .footer .links")
                .forEach(el => el.style.fontSize = "14px");
        }
    }

    window.addEventListener("resize", adjustFontSize);
    adjustFontSize();

    document.getElementById("rateMeBtn")?.addEventListener("click", function () {
        Swal.fire({
            title: "Rate the system",
            text: "Please take a moment to rate our system.",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Good",
            cancelButtonText: "Bad",
        }).then(function (result) {
            if (result.isConfirmed || result.dismiss === Swal.DismissReason.cancel) {
                Swal.fire({
                    title: "Thank you!",
                    text: "We appreciate your feedback.",
                    icon: "info",
                    input: "text",
                    inputPlaceholder: "Enter your feedback here",
                    confirmButtonText: "Send",
                }).then(function (feedbackResult) {
                    if (feedbackResult.isConfirmed) {
                        fetch("{% url 'app_general:feedback' %}", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": "{{ csrf_token }}",
                            },
                            body: JSON.stringify({
                                rate: result.isConfirmed ? "good" : "bad",
                                message: feedbackResult.value || "",
                            }),
                        }).then(response => {
                            if (response.ok) {
                                Swal.fire("Thank you!", "We appreciate your feedback.", "success");
                            } else {
                                Swal.fire("Error", "There was an issue submitting your feedback.", "error");
                            }
                        });
                    }
                });
            }
        });
    });

    document.querySelectorAll(".dropdown-btn").forEach(dropdown => {
        dropdown.addEventListener("click", function () {
            this.classList.toggle("none");
            let dropdownContent = this.nextElementSibling;
            let t1 = this.parentElement.querySelector(".t1");
            let t2 = this.parentElement.querySelector(".t2");

            let isDisplayed = window.getComputedStyle(dropdownContent).display === "block";

            dropdownContent.style.display = isDisplayed ? "none" : "block";
            if (t1 && t2) {
                t1.style.display = isDisplayed ? "block" : "none";
                t2.style.display = isDisplayed ? "block" : "none";
            }
        });
    });

    let lastClickTime = 0;

    window.handleDropdownClick = function (name) {
        let currentTime = Date.now();
        if (currentTime - lastClickTime < 300) {
            window.location.href = name === "knowledge" 
                ? "{% url 'app_general:general-resources' %}" 
                : "{% url 'app_general:all_commodities' %}";
        }
        lastClickTime = currentTime;
    };
});

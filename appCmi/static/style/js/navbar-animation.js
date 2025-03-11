function toggleMobileView() {
    const mobileView = document.getElementById("mobileView");
    if (mobileView.classList.contains("hidden")) {
      mobileView.classList.remove("hidden");
      mobileView.classList.add("visible");
    } else {
      mobileView.classList.remove("visible");
      mobileView.classList.add("hidden");
    }
  }
  
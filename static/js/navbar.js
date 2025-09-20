 document.addEventListener("DOMContentLoaded", () => {
    const menuBtn = document.getElementById("menu-btn");
    const closeBtn = document.getElementById("close-btn");
    const mobileMenu = document.getElementById("mobile-menu");
    const menuOverlay = document.getElementById("menu-overlay");

    function openMenu() {
      mobileMenu.classList.remove("translate-x-full");
      mobileMenu.classList.add("translate-x-0");
      menuOverlay.classList.remove("hidden");
      
      // Lock page scroll *without* causing a layout shift

      // Compute the width of the vertical scrollbar:
      // - window.innerWidth: viewport width INCLUDING the scrollbar
      // - document.documentElement.clientWidth: viewport width EXCLUDING the scrollbar
      // The difference is the scrollbar thickness
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

      // Disable scrolling on the page (removes the scrollbar)
      document.body.style.overflow = "hidden";

      // Add right padding equal to the removed scrollbar width so content doesn't "jump" horizontally
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }

    function closeMenu() {
      mobileMenu.classList.remove("translate-x-0");
      mobileMenu.classList.add("translate-x-full");
      menuOverlay.classList.add("hidden");
      
      // Restore normal scrolling
      document.body.style.overflow = "";
      document.body.style.paddingRight = "";
    }

    // Open menu button
    menuBtn.addEventListener("click", openMenu);
    
    // Close menu button inside menu
    closeBtn.addEventListener("click", closeMenu);

    // Close menu when clicking overlay
    menuOverlay.addEventListener("click", closeMenu);

    // Close menu when clicking any menu link
    const menuLinks = mobileMenu.querySelectorAll("a");
    menuLinks.forEach(link => {
      link.addEventListener("click", closeMenu);
    });

    // Close menu on escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && mobileMenu.classList.contains("translate-x-0")) {
        closeMenu();
      }
    });
  });
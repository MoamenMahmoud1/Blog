(function () {
    "use strict";

    const toggleButton = document.getElementById("themeToggle");
    if (!toggleButton) return;

    function updateAccessibleLabel() {
        const currentTheme = document.documentElement.getAttribute("data-bs-theme");
        toggleButton.setAttribute(
            "aria-label",
            currentTheme === "dark" ? "Switch to light theme" : "Switch to dark theme",
        );
        toggleButton.setAttribute(
            "title",
            currentTheme === "dark" ? "Light theme" : "Dark theme",
        );
    }

    updateAccessibleLabel();

    toggleButton.addEventListener("click", () => {
        const root = document.documentElement;
        const nextTheme = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-bs-theme", nextTheme);
        updateAccessibleLabel();

        try {
            localStorage.setItem("theme", nextTheme);
        } catch (error) {
            // Persisting the preference is optional.
        }
    });
})();

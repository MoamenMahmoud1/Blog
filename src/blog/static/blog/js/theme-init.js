(function () {
    "use strict";

    try {
        const savedTheme = localStorage.getItem("theme");
        const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
        document.documentElement.setAttribute(
            "data-bs-theme",
            savedTheme === "light" || savedTheme === "dark" ? savedTheme : preferredTheme,
        );
    } catch (error) {
        // The page still works when browser storage is unavailable.
    }
})();

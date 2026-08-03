(function () {
    "use strict";

    const dialog = document.getElementById("searchDialog");
    const openButton = document.getElementById("searchOpenButton");
    const input = document.getElementById("liveSearchInput");
    const results = document.getElementById("searchResults");
    const status = document.getElementById("searchStatus");

    if (!dialog || !openButton || !input || !results || !status) return;

    const endpoint = dialog.dataset.searchUrl;
    const minimumLength = Number(input.minLength) || 2;
    const idleMarkup = results.innerHTML;
    let debounceTimer;
    let activeRequest;
    let resultLinks = [];
    let activeResultIndex = -1;

    function openSearch() {
        if (!dialog.open) dialog.showModal();
        window.requestAnimationFrame(() => input.focus());
    }

    function resetKeyboardNavigation() {
        resultLinks = Array.from(results.querySelectorAll(".search-result"));
        activeResultIndex = -1;
    }

    function announce(message) {
        status.textContent = message;
    }

    function parseMarkup(markup) {
        const template = document.createElement("template");
        template.innerHTML = markup.trim();
        return template.content;
    }

    function renderMarkup(markup) {
        results.replaceChildren(parseMarkup(markup).cloneNode(true));
        resetKeyboardNavigation();
    }

    async function fetchResults(query) {
        activeRequest?.abort();
        const request = new AbortController();
        activeRequest = request;
        results.setAttribute("aria-busy", "true");
        announce("Searching…");

        const url = new URL(endpoint, window.location.origin);
        url.searchParams.set("q", query);

        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: request.signal,
            });
            if (!response.ok) throw new Error(`Search failed with status ${response.status}`);

            renderMarkup(await response.text());
            announce(resultLinks.length ? `${resultLinks.length} results shown.` : "No results found.");
        } catch (error) {
            if (error.name !== "AbortError") {
                renderMarkup('<div class="search-empty-state"><p class="mb-0">Search is temporarily unavailable. Please try again.</p></div>');
                announce("Search is temporarily unavailable.");
            }
        } finally {
            if (activeRequest === request) {
                results.setAttribute("aria-busy", "false");
            }
        }
    }

    function scheduleSearch() {
        window.clearTimeout(debounceTimer);
        activeRequest?.abort();
        const query = input.value.trim();

        if (query.length < minimumLength) {
            results.innerHTML = idleMarkup;
            resetKeyboardNavigation();
            announce("Type at least two characters to search.");
            return;
        }

        debounceTimer = window.setTimeout(() => fetchResults(query), 250);
    }

    function moveSelection(direction) {
        if (!resultLinks.length) return;
        activeResultIndex = (activeResultIndex + direction + resultLinks.length) % resultLinks.length;
        resultLinks[activeResultIndex].focus();
    }

    openButton.addEventListener("click", openSearch);
    input.addEventListener("input", scheduleSearch);
    dialog.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown") {
            event.preventDefault();
            moveSelection(1);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            moveSelection(-1);
        }
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
        window.clearTimeout(debounceTimer);
        activeRequest?.abort();
        openButton.focus();
    });

    document.addEventListener("keydown", (event) => {
        const target = event.target;
        const isTyping = target instanceof HTMLElement && (
            target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
        );
        const shortcut = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
        const slashShortcut = event.key === "/" && !isTyping;

        if (shortcut || slashShortcut) {
            event.preventDefault();
            openSearch();
        }
    });
})();

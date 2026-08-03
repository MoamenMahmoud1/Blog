(function () {
    "use strict";

    const lists = document.querySelectorAll("[data-infinite-list]");
    if (!lists.length) return;

    class InfiniteList {
        constructor(root) {
            this.root = root;
            this.status = root.parentElement.querySelector("[data-infinite-status]");
            this.itemLabel = root.dataset.itemLabel || "items";
            this.loading = false;
            this.observer = null;

            root.addEventListener("click", (event) => {
                const link = event.target.closest(".infinite-load-more");
                if (!link) return;
                event.preventDefault();
                this.load(link);
            });

            this.observeNextLink();
        }

        announce(message) {
            if (this.status) this.status.textContent = message;
        }

        observeNextLink() {
            this.observer?.disconnect();
            const link = this.root.querySelector(".infinite-load-more");
            const saveData = navigator.connection?.saveData === true;
            if (!link || saveData || !("IntersectionObserver" in window)) return;

            this.observer = new IntersectionObserver(
                (entries) => {
                    if (entries.some((entry) => entry.isIntersecting)) this.load(link);
                },
                { rootMargin: "500px 0px" },
            );
            this.observer.observe(link);
        }

        setLoading(link, loading) {
            const label = link.querySelector(".infinite-load-more__label");
            if (label && !link.dataset.defaultLabel) {
                link.dataset.defaultLabel = label.textContent.trim();
            }
            link.classList.toggle("disabled", loading);
            link.setAttribute("aria-disabled", String(loading));
            link.querySelector(".spinner-border")?.classList.toggle("d-none", !loading);
            if (label) {
                label.textContent = loading
                    ? "Loading…"
                    : link.dataset.retryLabel || link.dataset.defaultLabel;
            }
            this.root.setAttribute("aria-busy", String(loading));
        }

        async load(link) {
            if (this.loading) return;
            this.loading = true;
            this.observer?.unobserve(link);
            this.setLoading(link, true);
            let shouldObserveNext = false;

            try {
                const response = await fetch(link.dataset.nextUrl, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });
                if (!response.ok) throw new Error(`Request failed with status ${response.status}`);

                const template = document.createElement("template");
                template.innerHTML = (await response.text()).trim();
                const incomingItems = template.content.querySelector(".infinite-items");
                const currentItems = this.root.querySelector(".infinite-items");
                const incomingControls = template.content.querySelector(".infinite-controls");
                if (!incomingItems || !currentItems) throw new Error("Invalid partial response");

                const addedItems = Array.from(incomingItems.children);
                addedItems.forEach((item) => item.classList.add("feed-item--entering"));
                currentItems.append(...addedItems);
                this.root.querySelector(".infinite-controls")?.remove();
                if (incomingControls) this.root.append(incomingControls);

                this.announce(
                    addedItems.length
                        ? `${addedItems.length} more ${this.itemLabel} loaded.`
                        : `All ${this.itemLabel} loaded.`,
                );
                shouldObserveNext = true;
            } catch (error) {
                link.dataset.retryLabel = "Try again";
                this.setLoading(link, false);
                this.announce(`Could not load more ${this.itemLabel}. Use the button to try again.`);
            } finally {
                this.loading = false;
                this.root.setAttribute("aria-busy", "false");
                if (shouldObserveNext) {
                    window.requestAnimationFrame(() => this.observeNextLink());
                }
            }
        }
    }

    lists.forEach((root) => new InfiniteList(root));
})();

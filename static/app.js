        document.querySelectorAll("[data-search-form]").forEach((form) => {
            form.addEventListener("submit", () => {
                const button = form.querySelector("[data-submit-button]");
                const label = form.querySelector("[data-button-label]");
                if (!button || !label) return;
                button.disabled = true;
                button.classList.add("is-loading");
                label.textContent = "查询中";
            });
        });

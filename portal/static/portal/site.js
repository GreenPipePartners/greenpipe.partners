(() => {
    const copyText = async (text) => {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return;
        }

        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.setAttribute("readonly", "");
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
    };

    document.querySelectorAll('[data-component="tabs"]').forEach((tabs) => {
        const tabButtons = tabs.querySelectorAll("[data-tab]");
        const panels = tabs.querySelectorAll("[data-panel]");

        tabButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const key = button.dataset.tab;
                tabs.dataset.active = key;

                tabButtons.forEach((tabButton) => {
                    const selected = tabButton.dataset.tab === key;
                    tabButton.toggleAttribute("data-selected", selected);
                    tabButton.setAttribute("aria-selected", selected ? "true" : "false");
                });

                panels.forEach((panel) => {
                    const selected = panel.dataset.panel === key;
                    panel.toggleAttribute("data-selected", selected);
                    panel.hidden = !selected;
                });
            });
        });
    });

    document.querySelectorAll("[data-copy]").forEach((button) => {
        button.addEventListener("click", async () => {
            const command = button.querySelector('[data-slot="command-script"]');
            if (!command) {
                return;
            }

            await copyText(command.textContent.trim());
            button.dataset.copied = "true";
            window.setTimeout(() => {
                delete button.dataset.copied;
            }, 1400);
        });
    });
})();

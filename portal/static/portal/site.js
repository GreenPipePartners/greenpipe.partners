(() => {
    const copyResetTimers = new WeakMap();

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

    const showCopiedState = (button, label = null) => {
        button.dataset.copied = "true";
        if (label) {
            button.dataset.copyLabel = button.dataset.copyLabel || button.textContent;
            button.textContent = label;
        }

        window.clearTimeout(copyResetTimers.get(button));
        copyResetTimers.set(button, window.setTimeout(() => {
            delete button.dataset.copied;
            if (button.dataset.copyLabel) {
                button.textContent = button.dataset.copyLabel;
                delete button.dataset.copyLabel;
            }
        }, 1400));
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
            showCopiedState(button);
        });
    });

    document.querySelectorAll(".report-markdown pre, .source-snippet pre").forEach((pre) => {
        const code = pre.querySelector("code");
        if (!code || pre.dataset.copyReady) {
            return;
        }

        if (window.hljs) {
            window.hljs.highlightElement(code);
        }

        const wrapper = document.createElement("div");
        wrapper.className = "report-code-block";
        pre.before(wrapper);
        wrapper.appendChild(pre);
        pre.dataset.copyReady = "true";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "report-code-copy";
        button.textContent = "Copy";
        button.setAttribute("aria-label", "Copy code");
        button.addEventListener("click", async () => {
            await copyText(code.textContent);
            showCopiedState(button, "Copied");
        });
        wrapper.appendChild(button);
    });
})();

(() => {
    const copyResetTimers = new WeakMap();

    const getStoredTheme = () => {
        try {
            return localStorage.getItem("greenpipe-theme");
        } catch {
            return null;
        }
    };

    const storeTheme = (theme) => {
        try {
            localStorage.setItem("greenpipe-theme", theme);
        } catch {
            return;
        }
    };

    const applyTheme = (theme) => {
        const normalizedTheme = theme === "dark" ? "dark" : "light";
        const nextTheme = normalizedTheme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = normalizedTheme;

        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            button.setAttribute("aria-pressed", normalizedTheme === "dark" ? "true" : "false");
            button.setAttribute("aria-label", `Switch to ${nextTheme} mode`);

            const label = button.querySelector("[data-theme-toggle-label]");
            if (label) {
                label.textContent = nextTheme === "dark" ? "🌙" : "☀️";
            }
        });
    };

    const savedTheme = getStoredTheme();
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(savedTheme || (prefersDark ? "dark" : "light"));

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
            const nextTheme = currentTheme === "dark" ? "light" : "dark";
            storeTheme(nextTheme);
            applyTheme(nextTheme);
        });
    });

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

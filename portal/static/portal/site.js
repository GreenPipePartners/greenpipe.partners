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

    document.querySelectorAll("[data-report-markdown-copy]").forEach((button) => {
        button.addEventListener("click", async () => {
            const source = document.getElementById("report-markdown-source");
            if (!source) {
                return;
            }

            await copyText(JSON.parse(source.textContent));
            showCopiedState(button, "Copied");
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

    document.querySelectorAll("[data-ailab-quote]").forEach((root) => {
        const basePrice = Number(root.dataset.basePrice) || 0;
        const maxAttendees = Number(root.dataset.maxAttendees) || 5;
        const currency = new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0,
        });
        const quantityInputs = Array.from(root.querySelectorAll("[data-quantity]"));
        const fixedOptions = Array.from(root.querySelectorAll("[data-fixed-option]"));
        const addonInputs = Array.from(root.querySelectorAll("[data-addon-quantity]"));
        const attendeeTotal = root.querySelector("[data-attendee-total]");
        const lineItems = root.querySelector("[data-line-items]");
        const totalAmount = root.querySelector("[data-total]");
        const pdfButton = root.querySelector("[data-generate-pdf]");

        const readQuantity = (input) => {
            const value = Number.parseInt(input.value, 10);
            return Number.isFinite(value) ? Math.max(0, value) : 0;
        };

        const selectedPackages = () => quantityInputs.map((input) => ({
            input,
            label: input.dataset.label || "Attendee package",
            price: Number(input.dataset.price) || 0,
            quantity: readQuantity(input),
        }));

        const selectedFixedOptions = () => fixedOptions.filter((input) => input.checked).map((input) => ({
            id: input.dataset.option || "optional-add-on",
            label: input.dataset.label || "Optional add-on",
            price: Number(input.dataset.price) || 0,
        }));

        const optionIsSelected = (optionId) => fixedOptions.some((input) => (
            input.dataset.option === optionId && input.checked
        ));

        const selectedAddons = () => addonInputs.map((input) => ({
            input,
            label: input.dataset.label || "Add-on",
            price: Number(input.dataset.price) || 0,
            quantity: readQuantity(input),
        }));

        const totalSelected = () => selectedPackages().reduce((sum, pkg) => sum + pkg.quantity, 0);

        const clampAttendeeInput = (input) => {
            const others = quantityInputs.reduce((sum, other) => (
                other === input ? sum : sum + readQuantity(other)
            ), 0);
            const allowed = Math.max(0, maxAttendees - others);
            input.value = String(Math.min(readQuantity(input), allowed));
        };

        const clampAddonInput = (input) => {
            const max = input.max ? Number.parseInt(input.max, 10) : Infinity;
            const allowed = Number.isFinite(max) ? max : Infinity;
            input.value = String(Math.min(readQuantity(input), allowed));
        };

        const syncAddonAvailability = () => {
            addonInputs.forEach((input) => {
                const requiredOption = input.dataset.requires;
                const enabled = !requiredOption || optionIsSelected(requiredOption);
                const card = input.closest("[data-addon]");

                input.disabled = !enabled;
                card?.toggleAttribute("data-disabled", !enabled);

                if (!enabled) {
                    input.value = "0";
                }
            });
        };

        const updateQuote = () => {
            syncAddonAvailability();

            const packages = selectedPackages();
            const options = selectedFixedOptions();
            const addons = selectedAddons();
            const attendees = packages.reduce((sum, pkg) => sum + pkg.quantity, 0);
            const packageTotal = packages.reduce((sum, pkg) => sum + pkg.quantity * pkg.price, 0);
            const optionTotal = options.reduce((sum, option) => sum + option.price, 0);
            const addonTotal = addons.reduce((sum, addon) => sum + addon.quantity * addon.price, 0);
            const total = basePrice + packageTotal + optionTotal + addonTotal;

            if (attendeeTotal) {
                attendeeTotal.textContent = String(attendees);
            }
            if (totalAmount) {
                totalAmount.textContent = currency.format(total);
            }

            if (lineItems) {
                lineItems.textContent = "";
                const selected = packages.filter((pkg) => pkg.quantity > 0);
                const selectedAddonsWithQuantity = addons.filter((addon) => addon.quantity > 0);

                if (selected.length === 0 && options.length === 0 && selectedAddonsWithQuantity.length === 0) {
                    const empty = document.createElement("p");
                    empty.className = "ailab-empty-line";
                    empty.textContent = "No attendee packages selected yet.";
                    lineItems.append(empty);
                }

                selected.forEach((pkg) => {
                    const item = document.createElement("div");
                    item.className = "ailab-line-item";

                    const label = document.createElement("span");
                    label.textContent = `${pkg.quantity} x ${pkg.label}`;

                    const amount = document.createElement("strong");
                    amount.textContent = currency.format(pkg.quantity * pkg.price);

                    item.append(label, amount);
                    lineItems.append(item);
                });

                options.forEach((option) => {
                    const item = document.createElement("div");
                    item.className = "ailab-line-item";

                    const label = document.createElement("span");
                    label.textContent = option.label;

                    const amount = document.createElement("strong");
                    amount.textContent = currency.format(option.price);

                    item.append(label, amount);
                    lineItems.append(item);
                });

                selectedAddonsWithQuantity.forEach((addon) => {
                    const item = document.createElement("div");
                    item.className = "ailab-line-item";

                    const label = document.createElement("span");
                    label.textContent = `${addon.quantity} x ${addon.label}`;

                    const amount = document.createElement("strong");
                    amount.textContent = currency.format(addon.quantity * addon.price);

                    item.append(label, amount);
                    lineItems.append(item);
                });
            }

            quantityInputs.forEach((input) => {
                const current = readQuantity(input);
                const others = attendees - current;
                input.max = String(Math.max(0, maxAttendees - others));

                const card = input.closest("[data-package]");
                const decrement = card?.querySelector("[data-action='decrement']");
                const increment = card?.querySelector("[data-action='increment']");

                if (decrement) {
                    decrement.disabled = current === 0;
                }
                if (increment) {
                    increment.disabled = attendees >= maxAttendees;
                }
            });

            addonInputs.forEach((input) => {
                const current = readQuantity(input);
                const max = input.max ? Number.parseInt(input.max, 10) : Infinity;
                const card = input.closest("[data-addon]");
                const decrement = card?.querySelector("[data-action='decrement']");
                const increment = card?.querySelector("[data-action='increment']");
                const atMax = Number.isFinite(max) && current >= max;

                if (decrement) {
                    decrement.disabled = input.disabled || current === 0;
                }
                if (increment) {
                    increment.disabled = input.disabled || atMax;
                }
            });
        };

        const addWrappedRows = (rows, text, options = {}) => {
            const size = options.size || 11;
            const gap = options.gap || 16;
            const maxChars = options.maxChars || Math.floor(92 * (11 / size));
            const words = String(text).split(/\s+/);
            let line = "";

            const pushLine = (value) => {
                rows.push({
                    text: value,
                    size,
                    gap,
                    color: options.color,
                    font: options.font,
                    indent: options.indent,
                });
            };

            words.forEach((word) => {
                if (word.length > maxChars) {
                    if (line) {
                        pushLine(line);
                        line = "";
                    }

                    for (let index = 0; index < word.length; index += maxChars) {
                        const chunk = word.slice(index, index + maxChars);
                        if (index + maxChars < word.length) {
                            pushLine(chunk);
                        } else {
                            line = chunk;
                        }
                    }
                    return;
                }

                const next = line ? `${line} ${word}` : word;
                if (next.length > maxChars && line) {
                    pushLine(line);
                    line = word;
                } else {
                    line = next;
                }
            });

            if (line) {
                pushLine(line);
            }
        };

        const addPdfSection = (rows, text) => {
            rows.push({ text, size: 14, gap: 22, color: "green", font: "bold" });
        };

        const pdfText = (value) => String(value)
            .normalize("NFKD")
            .replace(/[^\x20-\x7E]/g, "")
            .replace(/\\/g, "\\\\")
            .replace(/\(/g, "\\(")
            .replace(/\)/g, "\\)");

        const makePdf = (rows) => {
            const encoder = new TextEncoder();
            const byteLength = (value) => encoder.encode(value).length;
            const objects = [null];
            const reserve = () => {
                objects.push("");
                return objects.length - 1;
            };
            const setObject = (id, body) => {
                objects[id] = body;
            };
            const catalogId = reserve();
            const pagesId = reserve();
            const fontId = reserve();
            const boldFontId = reserve();
            const pageIds = [];
            const pages = [];
            let currentPage = [];
            let usedHeight = 0;
            const availableHeight = 610;
            const colors = {
                accent: [0.608, 0.89, 0.729],
                green: [0.157, 0.455, 0.337],
                header: [0.051, 0.141, 0.114],
                ink: [0.051, 0.141, 0.114],
                muted: [0.36, 0.42, 0.39],
                rule: [0.85, 0.92, 0.89],
                white: [1, 1, 1],
            };
            const fill = (colorName) => (colors[colorName] || colors.ink).join(" ");

            rows.forEach((row) => {
                const gap = row.gap || (row.size || 11) + 6;
                if (currentPage.length && usedHeight + gap > availableHeight) {
                    pages.push(currentPage);
                    currentPage = [];
                    usedHeight = 0;
                }
                currentPage.push(row);
                usedHeight += gap;
            });
            if (currentPage.length) {
                pages.push(currentPage);
            }

            setObject(fontId, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
            setObject(boldFontId, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>");

            pages.forEach((pageRows, pageIndex) => {
                let y = 680;
                let stream = [
                    `${fill("header")} rg 0 720 612 72 re f`,
                    `${fill("accent")} rg 54 716 155 4 re f`,
                    `${fill("white")} rg BT /F2 18 Tf 54 758 Td (${pdfText("Green Pipe Partners")}) Tj ET`,
                    `${fill("accent")} rg BT /F1 10 Tf 54 740 Td (${pdfText("AgentLab Training Proposal")}) Tj ET`,
                    `${fill("rule")} rg 54 48 504 1 re f`,
                    `${fill("muted")} rg BT /F1 8 Tf 54 32 Td (${pdfText(`Page ${pageIndex + 1} of ${pages.length}`)}) Tj ET`,
                ].join("\n") + "\n";

                pageRows.forEach((row) => {
                    const size = row.size || 11;
                    const gap = row.gap || size + 6;
                    const font = row.font === "bold" ? "F2" : "F1";
                    const x = 54 + (row.indent || 0);
                    stream += `${fill(row.color || "ink")} rg BT /${font} ${size} Tf ${x} ${y} Td (${pdfText(row.text)}) Tj ET\n`;
                    y -= gap;
                });

                const contentId = reserve();
                const pageId = reserve();
                setObject(contentId, `<< /Length ${byteLength(stream)} >>\nstream\n${stream}endstream`);
                setObject(
                    pageId,
                    `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontId} 0 R /F2 ${boldFontId} 0 R >> >> /Contents ${contentId} 0 R >>`,
                );
                pageIds.push(pageId);
            });

            setObject(catalogId, `<< /Type /Catalog /Pages ${pagesId} 0 R >>`);
            setObject(
                pagesId,
                `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`,
            );

            let pdf = "%PDF-1.4\n";
            const offsets = [0];
            for (let id = 1; id < objects.length; id += 1) {
                offsets[id] = byteLength(pdf);
                pdf += `${id} 0 obj\n${objects[id]}\nendobj\n`;
            }

            const xrefOffset = byteLength(pdf);
            pdf += `xref\n0 ${objects.length}\n0000000000 65535 f \n`;
            for (let id = 1; id < objects.length; id += 1) {
                pdf += `${String(offsets[id]).padStart(10, "0")} 00000 n \n`;
            }
            pdf += `trailer\n<< /Size ${objects.length} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
            return pdf;
        };

        const generatePdf = () => {
            syncAddonAvailability();

            const packages = selectedPackages();
            const selected = packages.filter((pkg) => pkg.quantity > 0);
            const options = selectedFixedOptions();
            const addons = selectedAddons().filter((addon) => addon.quantity > 0);
            const packageTotal = selected.reduce((sum, pkg) => sum + pkg.quantity * pkg.price, 0);
            const optionTotal = options.reduce((sum, option) => sum + option.price, 0);
            const addonTotal = addons.reduce((sum, addon) => sum + addon.quantity * addon.price, 0);
            const total = basePrice + packageTotal + optionTotal + addonTotal;
            const attendees = selected.reduce((sum, pkg) => sum + pkg.quantity, 0);
            const date = new Date();
            const validUntil = new Date(date);
            validUntil.setDate(validUntil.getDate() + 30);
            const rows = [];

            addPdfSection(rows, "Proposal Summary");
            addWrappedRows(rows, "AgentLab Training for Controls Engineers", { size: 16, gap: 24, font: "bold" });
            addWrappedRows(rows, `Generated: ${date.toLocaleDateString()}`, { color: "muted" });
            addWrappedRows(rows, `Valid through: ${validUntil.toLocaleDateString()}`, { color: "muted" });

            rows.push({ text: " ", size: 6, gap: 10 });
            addPdfSection(rows, "Program");
            addWrappedRows(rows, "Three-Day Agent Workbench Crash Course", { font: "bold" });
            addWrappedRows(rows, "Onsite training for teams that want practical controls AI workflow help, and training on Linux, sandbox virtual machines and containers.");
            addWrappedRows(rows, "Training flow:", { font: "bold" });
            [
                "Day 1: Set up computers, OpenCode, and AI-assisted host applications while reviewing the software stack.",
                "Day 2: Build each attendee's Ubuntu VM lab with containerized Ignition and SQL Server while reviewing Docker and WSLC.",
                "Day 3: Implement a site-specific project tailored to the facility and engineering needs.",
                "Day 4 (Optional): Use AI agents to build out a Windows VM with Rockwell software and demonstrate advanced agent-assisted utility.",
            ].forEach((item) => addWrappedRows(rows, `- ${item}`, { indent: 12 }));

            rows.push({ text: " ", size: 6, gap: 10 });
            addPdfSection(rows, "Quote");
            addWrappedRows(rows, `Base Training Price: ${currency.format(basePrice)}`);

            if (selected.length === 0) {
                addWrappedRows(rows, "Attendee packages: To be selected");
            } else {
                selected.forEach((pkg) => {
                    addWrappedRows(
                        rows,
                        `${pkg.quantity} x ${pkg.label} at ${currency.format(pkg.price)}: ${currency.format(pkg.quantity * pkg.price)}`,
                    );
                });
            }

            if (options.length > 0 || addons.length > 0) {
                rows.push({ text: " ", size: 6, gap: 10 });
                addPdfSection(rows, "Optional Add-ons");
            }

            options.forEach((option) => {
                addWrappedRows(rows, `${option.label}: ${currency.format(option.price)}`);
            });

            addons.forEach((addon) => {
                addWrappedRows(
                    rows,
                    `${addon.quantity} x ${addon.label} at ${currency.format(addon.price)}: ${currency.format(addon.quantity * addon.price)}`,
                );
            });

            rows.push({ text: " ", size: 6, gap: 10 });
            addWrappedRows(rows, `Attendees selected: ${attendees} of ${maxAttendees}`);
            rows.push({ text: `Total: ${currency.format(total)}`, size: 16, gap: 24, color: "green", font: "bold" });

            rows.push({ text: " ", size: 6, gap: 10 });
            addPdfSection(rows, "Terms");
            addWrappedRows(rows, `This proposal is valid for 30 days from the generated date and expires on ${validUntil.toLocaleDateString()}.`);
            addWrappedRows(rows, "Travel, lodging, per diem, and other onsite expenses may result in additional costs depending on training location, schedule, and site requirements.");
            addWrappedRows(rows, "Scheduling is subject to mutual availability, site access, and receipt of required purchase authorization.");
            addWrappedRows(rows, "Customer is responsible for third-party subscriptions, operating system licenses, Rockwell software licensing, and other software approvals unless explicitly listed in this proposal.");
            addWrappedRows(rows, "Taxes, duties, shipping, and procurement fees are not included unless explicitly stated.");

            rows.push({ text: " ", size: 6, gap: 10 });
            addPdfSection(rows, "Notes");
            addWrappedRows(rows, "Laptop packages include Dell XPS 16-inch lab hardware configured for the selected Linux environment.");
            addWrappedRows(rows, "Bring Your Own covers setup and validation for attendee-provided workstations.");
            addWrappedRows(rows, "A ChatGPT Pro plan is required and is not provided: https://chatgpt.com/?ifpazk=1k0d2&default_tab=personal&highlight_plan=pro#pricing");
            addWrappedRows(rows, "Generated proposals are for review and may require final confirmation before purchase order issuance.");

            const pdf = makePdf(rows);
            const blob = new Blob([pdf], { type: "application/pdf" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `green-pipe-agentlab-proposal-${date.toISOString().slice(0, 10)}.pdf`;
            document.body.append(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        };

        root.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) {
                return;
            }

            const button = target.closest("[data-action]");
            if (!button) {
                return;
            }

            const card = button.closest("[data-package], [data-addon]");
            const input = card?.querySelector("[data-quantity], [data-addon-quantity]");
            if (!input || input.disabled) {
                return;
            }

            const delta = button.dataset.action === "increment" ? 1 : -1;
            const isAttendeeInput = input.hasAttribute("data-quantity");

            if (isAttendeeInput && delta > 0 && totalSelected() >= maxAttendees) {
                return;
            }

            input.value = String(Math.max(0, readQuantity(input) + delta));
            if (isAttendeeInput) {
                clampAttendeeInput(input);
            } else {
                clampAddonInput(input);
            }
            updateQuote();
        });

        quantityInputs.forEach((input) => {
            input.addEventListener("input", () => {
                clampAttendeeInput(input);
                updateQuote();
            });
        });

        addonInputs.forEach((input) => {
            input.addEventListener("input", () => {
                clampAddonInput(input);
                updateQuote();
            });
        });

        fixedOptions.forEach((input) => {
            input.addEventListener("change", () => {
                updateQuote();
            });
        });

        pdfButton?.addEventListener("click", generatePdf);
        updateQuote();
    });
})();

(() => {
    const currency = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
    });

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
        rows.push({text, size: 14, gap: 22, color: "green", font: "bold"});
    };

    const pdfText = (value) => String(value)
        .normalize("NFKD")
        .replace(/[^\x20-\x7E]/g, "")
        .replace(/\\/g, "\\\\")
        .replace(/\(/g, "\\(")
        .replace(/\)/g, "\\)");

    const makePdf = (rows, documentTitle) => {
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
                `${fill("accent")} rg BT /F1 10 Tf 54 740 Td (${pdfText(documentTitle)}) Tj ET`,
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

    document.querySelectorAll("[data-panellock-builder]").forEach((root) => {
        const stack = root.querySelector("[data-conversion-stack]");
        const template = root.querySelector("[data-conversion-template]");
        const countOutput = root.querySelector("[data-conversion-count]");
        const summaryCount = root.querySelector("[data-summary-count]");
        const quoteLines = root.querySelector("[data-quote-lines]");
        const quoteTotal = root.querySelector("[data-quote-total]");
        const protectTotal = root.querySelector("[data-protect-total]");
        const proposalButton = root.querySelector("[data-generate-proposal]");
        const approvalButton = root.querySelector("[data-request-final-approval]");
        const sourceAuthorized = root.querySelector("[data-source-authorized]");
        const agentLabAcknowledged = root.querySelector("[data-agentlab-acknowledged]");
        const agentLabAttestation = root.querySelector("[data-agentlab-attestation]");
        const proposalStatus = root.querySelector("[data-proposal-status]");
        const proposalCompany = root.querySelector("[data-proposal-company]");
        const proposalName = root.querySelector("[data-proposal-name]");
        const proposalEmail = root.querySelector("[data-proposal-email]");
        const proposalProject = root.querySelector("[data-proposal-project]");
        const csrfToken = root.querySelector("[name='csrfmiddlewaretoken']")?.value || "";
        const maxConversions = Number.parseInt(root.dataset.maxConversions || "20", 10);
        const proposalEndpoint = root.dataset.proposalEndpoint || "";
        let authoritativeProposal = null;
        let authoritativeFingerprint = "";

        const rows = () => Array.from(root.querySelectorAll("[data-conversion]"));
        const spareRows = () => Array.from(root.querySelectorAll("[data-spare-pc]"));

        const selected = (row, selector) => {
            const option = row.querySelector(selector)?.selectedOptions[0];
            return {
                code: option?.value || "",
                label: option?.dataset.label || option?.textContent.trim() || "Not selected",
                price: Number.parseInt(option?.dataset.price || "0", 10),
            };
        };

        const renumber = () => {
            rows().forEach((row, index) => {
                const number = String(index + 1).padStart(2, "0");
                const output = row.querySelector("[data-conversion-number]");
                if (output) {
                    output.textContent = number;
                }
            });
        };

        const addQuoteLine = (index, configuration) => {
            const line = document.createElement("div");
            line.className = "ailab-line-item";
            const label = document.createElement("span");
            const amount = document.createElement("strong");
            label.textContent = `${String(index + 1).padStart(2, "0")} - ${configuration.source.label}`;
            amount.textContent = currency.format(configuration.total / 100);
            line.append(label, amount);
            quoteLines?.append(line);
        };

        const addProtectLine = (index, configuration) => {
            const line = document.createElement("div");
            line.className = "ailab-line-item panellock-protect-line";
            const label = document.createElement("span");
            const amount = document.createElement("strong");
            label.textContent = `${String(index + 1).padStart(2, "0")} - PanelLock Protect`;
            amount.textContent = `${currency.format(configuration.annual / 100)} / yr`;
            line.append(label, amount);
            quoteLines?.append(line);
        };

        const addSpareLine = (spare) => {
            const line = document.createElement("div");
            line.className = "ailab-line-item";
            const label = document.createElement("span");
            const amount = document.createElement("strong");
            label.textContent = `${String(spare.index + 1).padStart(2, "0")} - Spare ${spare.label} x ${spare.quantity}`;
            amount.textContent = currency.format(spare.total / 100);
            line.append(label, amount);
            quoteLines?.append(line);
        };

        const readConfigurations = () => rows().map((row) => {
            const source = selected(row, "[data-source-platform]");
            const pc = selected(row, "[data-pc-type]");
            const screen = selected(row, "[data-screen-type]");
            const license = selected(row, "[data-ignition-license]");
            const protectInput = row.querySelector("[data-panel-protect]");
            const annual = protectInput?.checked
                ? Number.parseInt(protectInput.dataset.price || "0", 10)
                : 0;
            const total = source.price + pc.price + screen.price + license.price;
            const rowPrice = row.querySelector("[data-conversion-price]");
            if (rowPrice) {
                rowPrice.textContent = currency.format(total / 100);
            }
            return {source, pc, screen, license, total, annual, protect: protectInput?.checked === true};
        });

        const readSpares = () => spareRows().map((row, index) => {
            const count = row.querySelector("[data-spare-count]");
            const quantity = Number.parseInt(count?.value || "0", 10);
            const price = Number.parseInt(row.dataset.price || "0", 10);
            const total = price * quantity;
            const totalOutput = row.querySelector("[data-spare-total]");
            if (totalOutput) {
                totalOutput.textContent = currency.format(total / 100);
            }
            row.querySelector("[data-spare-action='decrement']")?.toggleAttribute("disabled", quantity <= 0);
            row.querySelector("[data-spare-action='increment']")?.toggleAttribute("disabled", quantity >= 20);
            return {index, code: row.dataset.code || "", label: row.dataset.label || "Spare PC", price, quantity, total};
        });

        const buildPayload = () => ({
            contact: {
                company: proposalCompany?.value.trim() || "",
                name: proposalName?.value.trim() || "",
                email: proposalEmail?.value.trim() || "",
                project: proposalProject?.value.trim() || "",
            },
            configurations: readConfigurations().map((configuration) => ({
                source_code: configuration.source.code,
                pc_code: configuration.pc.code,
                screen_code: configuration.screen.code,
                license_code: configuration.license.code,
                protect: configuration.protect,
            })),
            spares: readSpares().map((spare) => ({pc_code: spare.code, quantity: spare.quantity})),
            source_authorized: sourceAuthorized?.checked === true,
            agentlab_acknowledged: agentLabAcknowledged?.checked === true,
        });

        const generateProposal = (authoritative) => {
            const configurations = authoritative.configuration.configurations;
            const spares = authoritative.configuration.spares.map((spare, index) => ({...spare, index}));
            const selectedSpares = spares.filter((spare) => spare.quantity > 0);
            const oneTimeTotal = authoritative.one_time_total_cents;
            const annualTotal = authoritative.annual_total_cents;
            const date = new Date();
            const validUntil = new Date(`${authoritative.valid_until}T00:00:00`);
            const proposalRows = [];

            addPdfSection(proposalRows, "Proposal Summary");
            addWrappedRows(proposalRows, "PanelLock HMI Modernization Budgetary Proposal", {size: 16, gap: 24, font: "bold"});
            addWrappedRows(proposalRows, `Proposal reference: ${authoritative.reference}`, {color: "green", font: "bold"});
            addWrappedRows(proposalRows, `Generated: ${date.toLocaleDateString()}`, {color: "muted"});
            addWrappedRows(proposalRows, `Valid through: ${validUntil.toLocaleDateString()}`, {color: "muted"});
            addWrappedRows(
                proposalRows,
                "Status: Server-priced budgetary proposal. Green Pipe Partners expects to honor standard configurations as written; source review may identify exceptional scope requiring revision.",
                {color: "muted", font: "bold"},
            );
            proposalRows.push({text: " ", size: 6, gap: 10});

            addPdfSection(proposalRows, "Project Overview");
            addWrappedRows(
                proposalRows,
                "PanelLock provides a reviewed path for rebuilding a qualifying source HMI application, supplying and configuring the selected industrial PC for the approved application, supplying the selected panel display, and optionally enrolling the completed panel in PanelLock Protect.",
            );
            addWrappedRows(
                proposalRows,
                "The selected source platform, hardware, and budget are planning inputs. Final scope depends on technical review of the actual source project and supporting materials.",
            );
            proposalRows.push({text: " ", size: 6, gap: 10});

            addPdfSection(proposalRows, "Panel Configurations");
            configurations.forEach((configuration, index) => {
                addWrappedRows(proposalRows, `Conversion ${String(index + 1).padStart(2, "0")}`, {font: "bold"});
                addWrappedRows(
                    proposalRows,
                    `Source platform: ${configuration.source.label} - ${currency.format(configuration.source.price / 100)}`,
                    {indent: 12},
                );
                addWrappedRows(
                    proposalRows,
                    `Industrial PC: ${configuration.pc.label} - ${currency.format(configuration.pc.price / 100)}`,
                    {indent: 12},
                );
                addWrappedRows(
                    proposalRows,
                    `Panel display: ${configuration.screen.label} - ${currency.format(configuration.screen.price / 100)}`,
                    {indent: 12},
                );
                addWrappedRows(
                    proposalRows,
                    `Ignition license: ${configuration.license.label} - ${currency.format(configuration.license.price / 100)}`,
                    {indent: 12},
                );
                addWrappedRows(
                    proposalRows,
                    `One-time configuration total: ${currency.format(configuration.total / 100)}`,
                    {indent: 12, font: "bold"},
                );
                addWrappedRows(
                    proposalRows,
                    configuration.annual > 0
                        ? `PanelLock Protect: ${currency.format(configuration.annual / 100)} per year`
                        : "PanelLock Protect: Not selected",
                    {indent: 12},
                );
                proposalRows.push({text: " ", size: 5, gap: 8});
            });

            if (selectedSpares.length) {
                addPdfSection(proposalRows, "Optional Preconfigured Spare PCs");
                selectedSpares.forEach((spare) => {
                    addWrappedRows(
                        proposalRows,
                        `${String(spare.index + 1).padStart(2, "0")} - ${spare.label}: ${spare.quantity} x ${currency.format(spare.price / 100)} = ${currency.format(spare.total / 100)}`,
                    );
                });
                proposalRows.push({text: " ", size: 5, gap: 8});
            }

            addPdfSection(proposalRows, "Pricing");
            proposalRows.push({
                text: `One-time total: ${currency.format(oneTimeTotal / 100)}`,
                size: 16,
                gap: 24,
                color: "green",
                font: "bold",
            });
            addWrappedRows(
                proposalRows,
                `Annual PanelLock Protect: ${currency.format(annualTotal / 100)}`,
                {font: "bold"},
            );

            proposalRows.push({text: " ", size: 6, gap: 10});
            addPdfSection(proposalRows, "Confirmations");
            addWrappedRows(proposalRows, "Source authorization: Confirmed.");
            if (annualTotal > 0) {
                addWrappedRows(proposalRows, "AgentLab configuration and maintenance requirement: Acknowledged.");
            }

            proposalRows.push({text: " ", size: 6, gap: 10});
            addPdfSection(proposalRows, "Client Responsibilities");
            addWrappedRows(
                proposalRows,
                "Provide a complete, restorable source project or documented export, applicable passwords and licenses, version information, custom components, communications details, representative data, and other materials reasonably required to evaluate and perform the conversion.",
            );
            addWrappedRows(
                proposalRows,
                "Provide qualified operations, controls, IT, and process personnel for technical review, testing, acceptance, deployment planning, and validation of operational results.",
            );
            addWrappedRows(
                proposalRows,
                "Maintain responsibility for process specifications, controller and safety logic, independent safeguards, production authorization, site access, infrastructure, backups outside the contracted service, and required software licenses.",
            );

            proposalRows.push({text: " ", size: 6, gap: 10});
            addPdfSection(proposalRows, "Assumptions and Exclusions");
            addWrappedRows(
                proposalRows,
                "The source project is assumed to be complete, restorable, legally available for conversion, and supported by sufficient documentation to identify its screens, tags, alarms, scripts, drivers, custom controls, and external dependencies.",
            );
            addWrappedRows(
                proposalRows,
                "Unless expressly included in a final approved proposal, pricing excludes PLC or safety-logic changes, process-engineering design, historical-data migration, unsupported custom controls, third-party integrations, licenses, taxes, duties, shipping, site work, and remediation of pre-existing infrastructure defects.",
            );

            proposalRows.push({text: " ", size: 6, gap: 10});
            addPdfSection(proposalRows, "Terms and Conditions");
            addWrappedRows(proposalRows, "1. Budgetary Proposal", {font: "bold"});
            addWrappedRows(
                proposalRows,
                `This server-priced budgetary proposal is valid for 30 days and expires on ${validUntil.toLocaleDateString()}. Green Pipe Partners expects to honor the listed standard configuration and pricing unless source review identifies exceptional complexity, missing dependencies, unavailable components, compatibility limits, taxes, shipping, or scheduling changes.`,
                {indent: 12},
            );
            addWrappedRows(proposalRows, "2. Convertibility Review and Final Approval", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Green Pipe Partners will review the source project, exports, dependencies, licenses, custom controls, communications, and supporting documentation. Material findings may revise scope, price, schedule, assumptions, or the proposed method when the supplied materials differ substantially from the standard configuration represented here.",
                {indent: 12},
            );
            addWrappedRows(
                proposalRows,
                "This proposal is the commercial starting point for review but is not a binding commitment to perform work until Green Pipe Partners confirms scope and scheduling in writing.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "3. Scope, Deliverables, and Background Intellectual Property", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Green Pipe Partners retains ownership of its pre-existing tools, templates, frameworks, libraries, configuration methods, and know-how. After full payment, the customer retains its data, existing systems, and project-specific deliverables identified in the final approved proposal. Reusable background components remain licensed for use as embedded in the delivered solution.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "4. Taxes and Third-Party Costs", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Prices exclude applicable taxes, software licenses, unlisted hardware, freight, duties, and third-party charges unless expressly included. Authorized pass-through costs are payable by the customer.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "5. Access, Scheduling, Delivery, and Acceptance", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "The customer will provide timely access, credentials, permissions, technical inputs, maintenance windows, test data, and qualified personnel. Final delivery and acceptance criteria will be defined in the approved scope. Material non-conformities must be reported in writing within ten business days of delivery unless the final proposal states otherwise.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "6. Safety and Process-Control Responsibility", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "The customer retains responsibility for process specifications, engineering tolerances, controller and safety logic, independent safeguards, production authorization, and validation of operational results. PanelLock is not a substitute for required safety controls or engineering review.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "7. Force Majeure", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Green Pipe Partners is not liable for delay, loss, or damage caused by events beyond reasonable control, including utility, telecommunications, site-access, cybersecurity, supply-chain, or third-party system failures not caused by Green Pipe Partners.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "8. Limitation of Liability", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Green Pipe Partners' cumulative liability will not exceed fees paid under the final approved proposal. Green Pipe Partners is not liable for consequential, incidental, special, exemplary, or punitive damages, including lost production, profits, revenue, opportunity, or data, to the extent permitted by law.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "9. Limited Services Warranty and Support", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Unless the final proposal states otherwise, Green Pipe Partners warrants for ninety days after production delivery that project services will be performed professionally and delivered changes will conform materially to approved acceptance criteria. The warranty excludes third-party products, hardware failures, pre-existing conditions, source-data errors, infrastructure failures, unauthorized changes, and conditions outside Green Pipe Partners' control.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "10. Payment Terms", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Payment milestones will be stated in the final approved proposal. Unless otherwise stated, invoices are due within thirty days. Green Pipe Partners may suspend work for materially overdue balances after written notice.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "11. Changes, Delay, and Cancellation", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Changes to approved source materials, interfaces, requirements, security controls, access, schedule, or scope may change price and delivery. Out-of-scope work requires written authorization. Upon cancellation, the customer is responsible for completed work, committed non-cancelable costs, and reasonable closeout effort.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "12. Confidentiality", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "Each party will use reasonable care to protect the other's confidential information and use it only for the proposed services, excluding information lawfully public, previously known, independently developed, or received from an authorized third party.",
                {indent: 12},
            );
            addWrappedRows(proposalRows, "13. Final Agreement and Governing Law", {font: "bold"});
            addWrappedRows(
                proposalRows,
                "This budgetary proposal is not the final services agreement. The confirmed proposal, its appendices, and signed change orders will constitute the agreement and will be governed by South Carolina law, with actions brought in courts located in Charleston, South Carolina.",
                {indent: 12},
            );

            proposalRows.push({text: " ", size: 6, gap: 10});
            addPdfSection(proposalRows, "PanelLock Protect");
            addWrappedRows(
                proposalRows,
                "When selected, PanelLock Protect includes two scheduled update reviews per year, protected backups, and applicable critical vulnerability response. It uses the same AgentLab workbench infrastructure configured and maintained by qualified personnel. Detailed service levels and exclusions will be stated in the confirmed proposal.",
            );

            const pdf = makePdf(proposalRows, "PanelLock Proposal");
            const blob = new Blob([pdf], {type: "application/pdf"});
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `green-pipe-panellock-${authoritative.reference.toLowerCase()}-${date.toISOString().slice(0, 10)}.pdf`;
            document.body.append(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        };

        const setProposalStatus = (message, error = false) => {
            if (!proposalStatus) {
                return;
            }
            proposalStatus.textContent = message;
            proposalStatus.toggleAttribute("data-error", error);
        };

        const submitProposal = async () => {
            const payload = buildPayload();
            proposalButton.disabled = true;
            proposalButton.textContent = "Pricing proposal...";
            setProposalStatus("Validating the configuration against the current server catalog.");
            try {
                const response = await fetch(proposalEndpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify(payload),
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || "The proposal could not be created.");
                }
                authoritativeProposal = result;
                authoritativeFingerprint = JSON.stringify(payload);
                setProposalStatus(`${result.reference} is saved and server-priced through ${new Date(`${result.valid_until}T00:00:00`).toLocaleDateString()}.`);
                generateProposal(result);
            } catch (error) {
                setProposalStatus(error.message || "The proposal could not be created.", true);
            } finally {
                proposalButton.textContent = "Generate Budgetary Proposal";
                update();
            }
        };

        const update = () => {
            const configurations = readConfigurations();
            const spares = readSpares();
            const oneTimeTotal = configurations.reduce((sum, configuration) => sum + configuration.total, 0)
                + spares.reduce((sum, spare) => sum + spare.total, 0);
            const annualTotal = configurations.reduce((sum, configuration) => sum + configuration.annual, 0);
            const sourcesAuthorized = sourceAuthorized?.checked === true;
            const protectSelected = annualTotal > 0;
            const proposalDetailsComplete = [proposalCompany, proposalName, proposalEmail, proposalProject]
                .every((input) => input?.value.trim() && input.checkValidity());

            if (agentLabAcknowledged) {
                agentLabAcknowledged.disabled = !protectSelected;
                if (!protectSelected) {
                    agentLabAcknowledged.checked = false;
                }
            }
            agentLabAttestation?.toggleAttribute("data-disabled", !protectSelected);
            const agentLabRequirementAccepted = !protectSelected || agentLabAcknowledged?.checked === true;
            const prerequisitesMet = sourcesAuthorized && agentLabRequirementAccepted && proposalDetailsComplete;
            const currentFingerprint = JSON.stringify(buildPayload());
            const proposalIsCurrent = Boolean(
                authoritativeProposal && authoritativeFingerprint === currentFingerprint,
            );
            if (authoritativeProposal && !proposalIsCurrent) {
                setProposalStatus("The configuration changed. Generate a new server-priced proposal before continuing.");
            }

            if (countOutput) {
                countOutput.value = String(configurations.length);
            }
            if (summaryCount) {
                summaryCount.textContent = String(configurations.length);
            }
            if (quoteTotal) {
                quoteTotal.textContent = currency.format(oneTimeTotal / 100);
            }
            if (protectTotal) {
                protectTotal.textContent = `${currency.format(annualTotal / 100)} / year`;
            }
            if (quoteLines) {
                quoteLines.textContent = "";
                configurations.forEach((configuration, index) => {
                    addQuoteLine(index, configuration);
                    if (configuration.annual > 0) {
                        addProtectLine(index, configuration);
                    }
                });
                spares.filter((spare) => spare.quantity > 0).forEach(addSpareLine);
            }

            const decrement = root.querySelector("[data-conversion-action='decrement']");
            const increment = root.querySelector("[data-conversion-action='increment']");
            if (decrement) {
                decrement.disabled = configurations.length <= 1;
            }
            if (increment) {
                increment.disabled = configurations.length >= maxConversions;
            }

            if (proposalButton) {
                proposalButton.disabled = !prerequisitesMet;
            }

            if (approvalButton) {
                if (proposalIsCurrent) {
                    approvalButton.removeAttribute("aria-disabled");
                    approvalButton.href = authoritativeProposal.proposal_url;
                } else {
                    approvalButton.setAttribute("aria-disabled", "true");
                    approvalButton.removeAttribute("href");
                }
            }
        };

        root.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) {
                return;
            }
            const generateButton = target.closest("[data-generate-proposal]");
            if (generateButton) {
                if (!generateButton.disabled) {
                    submitProposal();
                }
                return;
            }
            const spareButton = target.closest("[data-spare-action]");
            if (spareButton && !spareButton.disabled) {
                const spare = spareButton.closest("[data-spare-pc]");
                const count = spare?.querySelector("[data-spare-count]");
                if (count) {
                    const current = Number.parseInt(count.value || "0", 10);
                    count.value = String(
                        spareButton.dataset.spareAction === "increment"
                            ? Math.min(20, current + 1)
                            : Math.max(0, current - 1),
                    );
                    update();
                }
                return;
            }
            const button = target.closest("[data-conversion-action]");
            if (!button || button.disabled) {
                return;
            }
            if (button.dataset.conversionAction === "increment" && rows().length < maxConversions) {
                stack?.append(template.content.cloneNode(true));
            }
            if (button.dataset.conversionAction === "decrement" && rows().length > 1) {
                rows().at(-1)?.remove();
            }
            renumber();
            update();
        });

        root.addEventListener("change", (event) => {
            if (event.target.matches("select, [data-panel-protect], [data-source-authorized], [data-agentlab-acknowledged]")) {
                update();
            }
        });

        root.addEventListener("input", (event) => {
            if (event.target.matches("[data-proposal-company], [data-proposal-name], [data-proposal-email], [data-proposal-project]")) {
                update();
            }
        });

        renumber();
        update();
    });
})();

(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const motionScale = 1.15;
    const sceneDwell = 450;

    const generalScenes = [
        {
            label: "SIGNED PLAN / HTTPS",
            title: "PanelLock signs the exact work scope.",
            description: "The portal sends an allowlisted plan to AgentLab over its independent HTTPS uplink. The panel connection remains closed.",
            path: "plan",
            duration: 2100,
            nodes: ["portal", "agentlab"],
            statuses: {
                signature: ["Signed", "verified"], validation: ["Receiving", "active"], authorization: ["Required", "waiting"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "AGENTLAB VALIDATION",
            title: "AgentLab verifies before it can act.",
            description: "Signature, target identity, approved operations, and expected inputs are checked locally. Validation does not grant execution authority.",
            duration: 1900,
            nodes: ["agentlab"],
            scan: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "HUMAN AUTHORIZATION",
            title: "A person controls the final boundary.",
            description: "AgentLab stops here. Direct Ethernet remains closed until authorized staff approve this plan for this panel.",
            path: "authorization",
            duration: 0,
            nodes: ["operator", "gate"],
            approval: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Decision required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "DIRECT ETHERNET",
            title: "Only the approved operation reaches the panel.",
            description: "AgentLab uses its separate direct Ethernet port. It does not bridge, route, or forward traffic between the portal and panel PC.",
            path: "ethernet",
            duration: 2300,
            nodes: ["agentlab", "panel"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Collecting", "active"],
            },
        },
        {
            label: "VALIDATION EVIDENCE",
            title: "The result returns to AgentLab as inspectable evidence.",
            description: "AgentLab measures the panel outcome and records the evidence locally before reporting the verified result.",
            path: "evidence",
            duration: 2600,
            nodes: ["panel", "agentlab"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Returning", "active"],
            },
        },
        {
            label: "EVIDENCE VERIFIED",
            title: "PanelLock receives the verified evidence.",
            description: "AgentLab returns the validated result over its independent HTTPS uplink. PanelLock records completion and the service path closes.",
            path: "verification",
            duration: 2400,
            nodes: ["agentlab", "portal"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Approved", "verified"], connection: ["Closed", "secure"], evidence: ["Evidence Verified", "verified"],
            },
        },
    ];

    const updateScenes = [
        {
            label: "SIGNED UPDATE / HTTPS",
            title: "PanelLock signs the exact update scope.",
            description: "The plan names the panel, current and target versions, maintenance window, required backup, and rollback boundary.",
            payload: {
                title: "Update Scope:",
                badge: "SIGNED",
                rows: [
                    ["Panel", "tank_monitoring"],
                    ["Plan", "PL-UPD-2026-0505"],
                    ["Versions", "Ignition 8.3.6 -> 8.3.8\nUbuntu 24.04.3 -> 24.04.4 LTS"],
                    ["Window", "2026-05-05 / 02:00-03:00"],
                    ["Protection", "Backup required / rollback required"],
                ],
            },
            path: "plan",
            duration: 2100,
            nodes: ["portal", "agentlab"],
            statuses: {
                signature: ["Signed", "verified"], validation: ["Receiving", "active"], authorization: ["Required", "waiting"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "UPDATE PREFLIGHT",
            title: "AgentLab checks every update prerequisite.",
            description: "Current versions, target packages, protected backup, available storage, health baseline, and rollback inputs are verified locally.",
            payload: {
                title: "Preflight Result:",
                badge: "PASSED",
                rows: [
                    ["Panel identity", "Matched"],
                    ["Signature", "Valid"],
                    ["Protected backup", "Verified"],
                    ["Available storage", "42 GB"],
                    ["Health baseline", "Captured"],
                    ["Rollback media", "Ready"],
                ],
            },
            duration: 1900,
            nodes: ["agentlab"],
            scan: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "HUMAN AUTHORIZATION",
            title: "A person authorizes this update.",
            description: "AgentLab stops until authorized staff approve the panel, target versions, maintenance window, and rollback plan.",
            payload: {
                title: "Authorization Request:",
                badge: "REQUIRED",
                rows: [
                    ["Plan", "PL-UPD-2026-0505"],
                    ["Panel", "tank_monitoring"],
                    ["Scope hash", "sha256:7c4f...91a2"],
                    ["Window opens", "2026-05-05 / 02:00"],
                    ["Decision", "Required"],
                ],
            },
            path: "authorization",
            duration: 0,
            nodes: ["operator", "gate"],
            approval: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Decision required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "DIRECT ETHERNET",
            title: "AgentLab applies only the approved update.",
            description: "The allowlisted update reaches the panel over separate direct Ethernet. AgentLab does not bridge or route the HTTPS uplink.",
            payload: {
                title: "Execution Allowlist:",
                badge: "ALLOWLIST",
                rows: [
                    ["Target", "tank_monitoring"],
                    ["Operations", "install:ignition@8.3.8\nupgrade:ubuntu@24.04.4"],
                    ["Transport", "Direct Ethernet"],
                    ["IP forwarding", "False"],
                ],
            },
            path: "ethernet",
            duration: 2300,
            nodes: ["agentlab", "panel"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Collecting", "active"],
            },
        },
        {
            label: "POST-UPDATE VALIDATION",
            title: "AgentLab validates the panel after the update.",
            description: "Gateway health, project startup, package versions, tag quality, and the rollback checkpoint are measured before the change closes.",
            payload: {
                title: "Validation Result:",
                badge: "PASSED",
                rows: [
                    ["Gateway", "Healthy"],
                    ["Project", "Running"],
                    ["Observed versions", "Ignition 8.3.8\nUbuntu 24.04.4 LTS"],
                    ["Tag quality", "Good"],
                    ["Rollback checkpoint", "Retained"],
                ],
            },
            path: "evidence",
            duration: 2600,
            nodes: ["panel", "agentlab"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Post-checks passed", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Returning", "active"],
            },
        },
        {
            label: "UPDATE RECORD VERIFIED",
            title: "PanelLock receives an inspectable update record.",
            description: "The verified record includes the approved scope, observed versions, prerequisites, post-checks, and attached evidence.",
            path: "verification",
            duration: 2400,
            nodes: ["agentlab", "portal"],
            context: "update",
            statuses: {
                signature: ["Verified", "verified"], validation: ["Post-checks passed", "verified"], authorization: ["Approved", "verified"], connection: ["Closed", "secure"], evidence: ["Update verified", "verified"],
            },
        },
    ];

    const spareScenes = [
        {
            label: "SIGNED SPARE PLAN / HTTPS",
            title: "PanelLock signs the project-matching scope.",
            description: "The plan identifies the existing Panel PC project, protected backup, approved software versions, and spare hardware target.",
            payload: {
                title: "Spare Match Scope:",
                badge: "SIGNED",
                rows: [
                    ["Existing project", "tank_monitoring"],
                    ["Plan", "PL-SPARE-2026-0505"],
                    ["Spare asset", "SPARE-MED-02"],
                    ["Source backup", "tank_monitoring-2026-05-05.gwbk"],
                    ["Matched versions", "Ignition 8.3.6\nUbuntu 24.04.3 LTS"],
                    ["Live panel write", "Prohibited"],
                ],
            },
            path: "plan",
            duration: 2100,
            nodes: ["portal", "agentlab"],
            statuses: {
                signature: ["Signed", "verified"], validation: ["Receiving", "active"], authorization: ["Required", "waiting"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "SPARE PREFLIGHT",
            title: "AgentLab checks the project and spare.",
            description: "The project backup hash, source versions, spare inventory, image inputs, and recovery media are verified before write access.",
            payload: {
                title: "Spare Preflight:",
                badge: "PASSED",
                rows: [
                    ["Project backup", "Hash verified"],
                    ["Project fingerprint", "sha256:2b6d...03f1"],
                    ["Source versions", "Matched"],
                    ["Spare inventory", "Medium fanless PC / 16 GB / 512 GB"],
                    ["Image inputs", "Ready"],
                    ["Recovery media", "Ready"],
                ],
            },
            duration: 1900,
            nodes: ["agentlab"],
            scan: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "HUMAN AUTHORIZATION",
            title: "A person authorizes writing the spare.",
            description: "AgentLab stops until staff approve matching this spare to the selected existing Panel PC project and protected backup.",
            payload: {
                title: "Authorization Request:",
                badge: "REQUIRED",
                rows: [
                    ["Plan", "PL-SPARE-2026-0505"],
                    ["Existing project", "tank_monitoring"],
                    ["Spare asset", "SPARE-MED-02"],
                    ["Scope hash", "sha256:48ae...b730"],
                    ["Decision", "Required"],
                ],
            },
            path: "authorization",
            duration: 0,
            nodes: ["operator", "gate"],
            approval: true,
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Decision required", "required"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            },
        },
        {
            label: "DIRECT ETHERNET",
            title: "AgentLab writes the approved project state to the spare.",
            description: "The spare is imaged and restored over separate direct Ethernet. The existing live Panel PC is not connected or altered.",
            payload: {
                title: "Spare Write Allowlist:",
                badge: "ALLOWLIST",
                rows: [
                    ["Target", "SPARE-MED-02"],
                    ["Operations", "image:ubuntu@24.04.3\ninstall:ignition@8.3.6\nrestore:tank_monitoring"],
                    ["Transport", "Direct Ethernet"],
                    ["Existing panel", "Not connected"],
                ],
            },
            path: "ethernet",
            duration: 2300,
            nodes: ["agentlab", "panel"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Preflight passed", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Collecting", "active"],
            },
        },
        {
            label: "SPARE VALIDATION",
            title: "AgentLab proves the spare can run the existing project.",
            description: "Gateway and project startup, matched versions, display behavior, tag quality, and burn-in checks become validation evidence.",
            payload: {
                title: "Spare Validation Result:",
                badge: "PASSED",
                rows: [
                    ["Gateway", "Healthy"],
                    ["Project", "tank_monitoring / running"],
                    ["Observed versions", "Ignition 8.3.6\nUbuntu 24.04.3 LTS"],
                    ["Tag quality", "Good"],
                    ["Burn-in", "4 hours / passed"],
                ],
            },
            path: "evidence",
            duration: 2600,
            nodes: ["panel", "agentlab"],
            statuses: {
                signature: ["Verified", "verified"], validation: ["Spare checks passed", "verified"], authorization: ["Approved", "verified"], connection: ["Direct only", "active"], evidence: ["Returning", "active"],
            },
        },
        {
            label: "SPARE RECORD VERIFIED",
            title: "PanelLock records a project-matched spare.",
            description: "The record ties the spare hardware and restored image to the existing Panel PC project and its validation evidence.",
            path: "verification",
            duration: 2400,
            nodes: ["agentlab", "portal"],
            context: "spare",
            statuses: {
                signature: ["Verified", "verified"], validation: ["Spare checks passed", "verified"], authorization: ["Approved", "verified"], connection: ["Closed", "secure"], evidence: ["Spare matched", "verified"],
            },
        },
    ];

    const variants = {
        general: {
            scenes: generalScenes,
            subtitle: "Controlled modernization simulation",
            idleLabel: "SYSTEM READY",
            idleTitle: "Nothing crosses the boundary by default.",
            idleDescription: "The portal, AgentLab, and panel are separate. Start the flow to follow one authorized change.",
            planLabel: "SIGNED PLAN / HTTPS",
            timeline: ["Signed plan", "Validate", "Authorize", "Execute", "Evidence", "Verified"],
            nodeDetails: {
                portal: "Defines scope / signs plan / records intent",
                agentlab: "Validates scope / waits for a person / collects proof",
                panel: "Local execution / measured result / no cloud agent",
            },
            panelKicker: "CONTROLLED ENDPOINT",
            panelTitle: "Panel PC",
            approvalTitle: "AgentLab is waiting.",
            approvalCopy: "The direct panel connection remains closed until a person decides.",
            rejectDescription: "The plan stops at AgentLab. Nothing reaches the panel PC and the direct connection remains closed.",
        },
        update: {
            scenes: updateScenes,
            subtitle: "Approved panel update simulation",
            idleLabel: "UPDATE READY",
            idleTitle: "Updates stop before the panel by default.",
            idleDescription: "Start the flow to follow an approved update from version context through post-update evidence.",
            planLabel: "SIGNED UPDATE / HTTPS",
            timeline: ["Update plan", "Preflight", "Authorize", "Apply update", "Post-checks", "Recorded"],
            nodeDetails: {
                portal: "Defines update / signs versions / records result",
                agentlab: "Checks versions / waits for approval / collects proof",
                panel: "Approved update / measured result / no cloud agent",
            },
            panelKicker: "UPDATE TARGET",
            panelTitle: "Panel PC",
            approvalTitle: "AgentLab preflight passed.",
            approvalCopy: "The panel connection remains closed until a person approves the target versions and maintenance window.",
            rejectDescription: "The update stops at AgentLab. No package reaches the panel and the direct connection remains closed.",
        },
        spare: {
            scenes: spareScenes,
            subtitle: "Existing-project spare synchronization",
            idleLabel: "SPARE READY",
            idleTitle: "The spare is untouched by default.",
            idleDescription: "Start the flow to match a spare to an approved existing Panel PC project without altering the live panel.",
            planLabel: "SIGNED SPARE PLAN / HTTPS",
            timeline: ["Spare plan", "Preflight", "Authorize", "Write spare", "Validate", "Matched"],
            nodeDetails: {
                portal: "Defines project match / signs source / records result",
                agentlab: "Checks backup / writes spare / collects proof",
                panel: "Matched to existing project / restored / validated",
            },
            panelKicker: "STAGED REPLACEMENT",
            panelTitle: "Spare Panel PC",
            approvalTitle: "AgentLab spare preflight passed.",
            approvalCopy: "The spare remains untouched until a person approves the existing project source and target hardware.",
            rejectDescription: "The spare plan stops at AgentLab. The spare remains untouched and the existing Panel PC is not altered.",
        },
    };

    document.querySelectorAll("[data-panel-flow]").forEach((root) => {
        const playButton = root.querySelector("[data-flow-play]");
        const resetButton = root.querySelector("[data-flow-reset]");
        const approveButton = root.querySelector("[data-flow-approve]");
        const rejectButton = root.querySelector("[data-flow-reject]");
        const approval = root.querySelector("[data-flow-approval]");
        const approvalTitle = root.querySelector("[data-flow-approval-title]");
        const approvalCopy = root.querySelector("[data-flow-approval-copy]");
        const mode = root.querySelector("[data-flow-mode]");
        const subtitle = root.querySelector("[data-flow-subtitle]");
        const stepNumber = root.querySelector("[data-flow-step-number]");
        const stepLabel = root.querySelector("[data-flow-step-label]");
        const title = root.querySelector("[data-flow-title]");
        const description = root.querySelector("[data-flow-description]");
        const triggers = Array.from(root.querySelectorAll("[data-flow-trigger]"));
        const triggerLabels = Array.from(root.querySelectorAll("[data-flow-trigger-label]"));
        const variantTriggers = Array.from(root.querySelectorAll("[data-flow-variant-trigger]"));
        const contextPanels = Array.from(root.querySelectorAll("[data-flow-context]"));
        const payloadPanel = root.querySelector("[data-flow-payload]");
        const payloadTitle = root.querySelector("[data-flow-payload-title]");
        const payloadBadge = root.querySelector("[data-flow-payload-badge]");
        const payloadBody = root.querySelector("[data-flow-payload-body]");
        const paths = Array.from(root.querySelectorAll("[data-flow-path]"));
        const nodes = Array.from(root.querySelectorAll("[data-flow-node]"));
        const statusFields = Array.from(root.querySelectorAll("[data-flow-status]"));
        const planLabel = root.querySelector("[data-flow-plan-label]");
        const portalDetail = root.querySelector('[data-flow-node-detail="portal"]');
        const agentlabDetail = root.querySelector('[data-flow-node-detail="agentlab"]');
        const panelDetail = root.querySelector('[data-flow-node-detail="panel"]');
        const panelKicker = root.querySelector('[data-flow-node-kicker="panel"]');
        const panelTitle = root.querySelector('[data-flow-node-title="panel"]');
        const token = root.querySelector("[data-flow-token]");
        let currentStep = -1;
        let isRunning = false;
        let isFinished = false;
        let isWaitingForApproval = false;
        let resumeAfterApproval = false;
        let sceneTimer = null;
        let animationFrame = null;

        if (!playButton || !resetButton || !approveButton || !rejectButton || !approval || !token) {
            return;
        }

        const getVariant = () => variants[root.dataset.flowVariant] || variants.general;

        const getScenes = () => getVariant().scenes;

        const applyVariantCopy = () => {
            const variant = getVariant();
            if (subtitle) subtitle.textContent = variant.subtitle;
            if (planLabel) planLabel.textContent = variant.planLabel;
            if (portalDetail) portalDetail.textContent = variant.nodeDetails.portal;
            if (agentlabDetail) agentlabDetail.textContent = variant.nodeDetails.agentlab;
            if (panelDetail) panelDetail.textContent = variant.nodeDetails.panel;
            if (panelKicker) panelKicker.textContent = variant.panelKicker;
            if (panelTitle) panelTitle.textContent = variant.panelTitle;
            if (approvalTitle) approvalTitle.textContent = variant.approvalTitle;
            if (approvalCopy) approvalCopy.textContent = variant.approvalCopy;
            triggerLabels.forEach((label, index) => {
                label.textContent = variant.timeline[index];
            });
            variantTriggers.forEach((trigger) => {
                const selected = trigger.dataset.flowVariantTrigger === root.dataset.flowVariant;
                trigger.setAttribute("aria-selected", String(selected));
                trigger.tabIndex = selected ? 0 : -1;
            });
        };

        const stopTimers = () => {
            window.clearTimeout(sceneTimer);
            window.cancelAnimationFrame(animationFrame);
            sceneTimer = null;
            animationFrame = null;
            token.setAttribute("hidden", "");
        };

        const updatePlayButton = () => {
            playButton.disabled = isWaitingForApproval;
            if (reduceMotion) {
                playButton.textContent = currentStep < 0 || isFinished ? "Show first step" : "Show next step";
                return;
            }
            playButton.textContent = isWaitingForApproval
                ? "Awaiting approval"
                : isRunning
                    ? "Pause flow"
                    : isFinished || root.dataset.outcome === "rejected"
                        ? "Replay flow"
                        : currentStep >= 0
                            ? "Resume flow"
                            : "Run flow";
        };

        const setPathStates = (index) => {
            paths.forEach((path) => path.classList.remove("is-active", "is-complete"));
            const plan = root.querySelector('[data-flow-path="plan"]');
            const authorization = root.querySelector('[data-flow-path="authorization"]');
            const ethernet = root.querySelector('[data-flow-path="ethernet"]');
            const evidence = root.querySelector('[data-flow-path="evidence"]');
            const verification = root.querySelector('[data-flow-path="verification"]');

            if (index === 0) plan?.classList.add("is-active");
            if (index > 0) plan?.classList.add("is-complete");
            if (index === 2) authorization?.classList.add("is-active");
            if (index > 2) authorization?.classList.add("is-complete");
            if (index === 3) ethernet?.classList.add("is-active");
            if (index > 3) ethernet?.classList.add("is-complete");
            if (index === 4) evidence?.classList.add("is-active");
            if (index > 4) evidence?.classList.add("is-complete");
            if (index === 5) verification?.classList.add("is-active");
        };

        const setNodeStates = (scene, index) => {
            nodes.forEach((node) => node.classList.remove("is-active", "is-complete", "is-scanning"));
            nodes.forEach((node) => {
                const key = node.dataset.flowNode;
                if (scene.nodes.includes(key)) node.classList.add("is-active");
                if ((key === "portal" && index > 0)
                    || (key === "agentlab" && index > 1)
                    || ((key === "operator" || key === "gate") && index > 2)
                    || (key === "panel" && index > 3)) {
                    node.classList.add("is-complete");
                }
            });
            if (scene.scan) root.querySelector('[data-flow-node="agentlab"]')?.classList.add("is-scanning");
        };

        const setStatusFields = (statuses) => {
            statusFields.forEach((field) => {
                const status = statuses[field.dataset.flowStatus];
                if (!status) return;
                field.textContent = status[0];
                field.dataset.state = status[1];
            });
        };

        const setScene = (index) => {
            stopTimers();
            const activeScenes = getScenes();
            const scene = activeScenes[index];
            currentStep = index;
            root.dataset.currentStep = String(index);
            root.dataset.outcome = index > 2 ? "approved" : "running";
            stepNumber.textContent = String(index + 1).padStart(2, "0");
            stepLabel.textContent = scene.label;
            title.textContent = scene.title;
            description.textContent = scene.description;
            description.hidden = Boolean(scene.context || scene.payload);
            if (payloadPanel) payloadPanel.hidden = !scene.payload;
            if (scene.payload && payloadTitle && payloadBody) {
                payloadTitle.textContent = scene.payload.title;
                if (payloadBadge) payloadBadge.textContent = scene.payload.badge;
                payloadBody.replaceChildren(...scene.payload.rows.map(([term, value]) => {
                    const row = document.createElement("div");
                    const label = document.createElement("dt");
                    const detail = document.createElement("dd");
                    label.textContent = term;
                    detail.textContent = value;
                    row.append(label, detail);
                    return row;
                }));
            }
            contextPanels.forEach((panel) => {
                panel.hidden = panel.dataset.flowContext !== scene.context;
            });
            mode.textContent = scene.approval ? "AUTHORIZATION HOLD" : index === activeScenes.length - 1 ? "VERIFYING" : "IN PROGRESS";
            approval.hidden = !scene.approval;
            isWaitingForApproval = scene.approval;
            setStatusFields(scene.statuses);
            setPathStates(index);
            setNodeStates(scene, index);

            triggers.forEach((trigger, triggerIndex) => {
                trigger.toggleAttribute("data-complete", triggerIndex < index);
                if (triggerIndex === index) trigger.setAttribute("aria-current", "step");
                else trigger.removeAttribute("aria-current");
            });
            updatePlayButton();
        };

        const animatePath = (pathName, duration) => {
            const path = root.querySelector(`[data-flow-path="${pathName}"]`);
            if (!path || reduceMotion) return;
            const length = path.getTotalLength();
            const startedAt = performance.now();
            token.dataset.kind = pathName;
            token.removeAttribute("hidden");

            const tick = (now) => {
                const progress = Math.min((now - startedAt) / duration, 1);
                const eased = progress < 0.5 ? 2 * progress * progress : 1 - ((-2 * progress + 2) ** 2) / 2;
                const point = path.getPointAtLength(length * eased);
                token.setAttribute("transform", `translate(${point.x} ${point.y})`);
                if (progress < 1) animationFrame = window.requestAnimationFrame(tick);
                else token.setAttribute("hidden", "");
            };
            animationFrame = window.requestAnimationFrame(tick);
        };

        const finishFlow = () => {
            stopTimers();
            isRunning = false;
            isFinished = true;
            root.dataset.playback = "stopped";
            root.dataset.outcome = "verified";
            mode.textContent = "VERIFIED";
            setStatusFields(getScenes().at(-1).statuses);
            paths.forEach((path) => path.classList.remove("is-active"));
            paths.forEach((path) => path.classList.add("is-complete"));
            nodes.forEach((node) => {
                node.classList.remove("is-active", "is-scanning");
                node.classList.add("is-complete");
            });
            triggers.forEach((trigger) => trigger.toggleAttribute("data-complete", true));
            updatePlayButton();
        };

        const runScene = (index) => {
            setScene(index);
            const activeScenes = getScenes();
            const scene = activeScenes[index];
            if (scene.approval) {
                resumeAfterApproval = true;
                isRunning = false;
                root.dataset.playback = "waiting";
                updatePlayButton();
                return;
            }

            isRunning = true;
            root.dataset.playback = "running";
            const motionDuration = scene.duration * motionScale;
            animatePath(scene.path, motionDuration);
            updatePlayButton();
            sceneTimer = window.setTimeout(() => {
                if (index >= activeScenes.length - 1) finishFlow();
                else runScene(index + 1);
            }, motionDuration + sceneDwell);
        };

        const showStaticScene = (index) => {
            isRunning = false;
            isFinished = false;
            resumeAfterApproval = false;
            const activeScenes = getScenes();
            root.dataset.playback = activeScenes[index].approval ? "waiting" : "stopped";
            setScene(index);
            if (!activeScenes[index].approval) {
                isWaitingForApproval = false;
                animatePath(activeScenes[index].path, activeScenes[index].duration * motionScale);
            }
            updatePlayButton();
        };

        const reset = () => {
            stopTimers();
            const variant = getVariant();
            currentStep = -1;
            isRunning = false;
            isFinished = false;
            isWaitingForApproval = false;
            resumeAfterApproval = false;
            root.dataset.currentStep = "idle";
            root.dataset.outcome = "ready";
            root.dataset.playback = "stopped";
            mode.textContent = "READY";
            stepNumber.textContent = "00";
            stepLabel.textContent = variant.idleLabel;
            title.textContent = variant.idleTitle;
            description.textContent = variant.idleDescription;
            description.hidden = false;
            approval.hidden = true;
            if (payloadPanel) payloadPanel.hidden = true;
            contextPanels.forEach((panel) => { panel.hidden = true; });
            paths.forEach((path) => path.classList.remove("is-active", "is-complete"));
            nodes.forEach((node) => node.classList.remove("is-active", "is-complete", "is-scanning"));
            triggers.forEach((trigger) => {
                trigger.removeAttribute("aria-current");
                trigger.removeAttribute("data-complete");
            });
            setStatusFields({
                signature: ["Not received", "waiting"], validation: ["Waiting", "waiting"], authorization: ["Required", "waiting"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            });
            applyVariantCopy();
            updatePlayButton();
        };

        playButton.addEventListener("click", () => {
            if (reduceMotion) {
                const activeScenes = getScenes();
                if (currentStep < 0 || isFinished || root.dataset.outcome === "rejected") showStaticScene(0);
                else if (currentStep < activeScenes.length - 1 && !isWaitingForApproval) showStaticScene(currentStep + 1);
                else if (currentStep >= activeScenes.length - 1) finishFlow();
                return;
            }
            if (isRunning) {
                stopTimers();
                isRunning = false;
                root.dataset.playback = "stopped";
                updatePlayButton();
                return;
            }
            if (isFinished || root.dataset.outcome === "rejected") runScene(0);
            else runScene(Math.max(0, currentStep));
        });

        resetButton.addEventListener("click", reset);

        triggers.forEach((trigger) => {
            trigger.addEventListener("click", () => showStaticScene(Number(trigger.dataset.flowTrigger)));
        });

        variantTriggers.forEach((trigger) => {
            trigger.addEventListener("click", () => {
                root.dataset.flowVariant = trigger.dataset.flowVariantTrigger;
                reset();
            });
            trigger.addEventListener("keydown", (event) => {
                if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
                event.preventDefault();
                const direction = event.key === "ArrowRight" ? 1 : -1;
                const currentIndex = variantTriggers.indexOf(trigger);
                const next = variantTriggers[(currentIndex + direction + variantTriggers.length) % variantTriggers.length];
                next.click();
                next.focus();
            });
        });

        approveButton.addEventListener("click", () => {
            const shouldContinue = resumeAfterApproval && !reduceMotion;
            isWaitingForApproval = false;
            approval.hidden = true;
            root.dataset.outcome = "approved";
            if (shouldContinue) runScene(3);
            else showStaticScene(3);
        });

        rejectButton.addEventListener("click", () => {
            stopTimers();
            isRunning = false;
            isFinished = false;
            isWaitingForApproval = false;
            resumeAfterApproval = false;
            root.dataset.playback = "stopped";
            root.dataset.outcome = "rejected";
            approval.hidden = true;
            mode.textContent = "STOPPED";
            title.textContent = "Authorization was withheld.";
            description.textContent = getVariant().rejectDescription;
            description.hidden = false;
            if (payloadPanel) payloadPanel.hidden = true;
            contextPanels.forEach((panel) => { panel.hidden = true; });
            const authorization = root.querySelector('[data-flow-status="authorization"]');
            authorization.textContent = "Rejected";
            authorization.dataset.state = "blocked";
            paths.forEach((path) => path.classList.remove("is-active"));
            updatePlayButton();
        });

        reset();
    });
})();

(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const scenes = [
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

    document.querySelectorAll("[data-panel-flow]").forEach((root) => {
        const playButton = root.querySelector("[data-flow-play]");
        const resetButton = root.querySelector("[data-flow-reset]");
        const approveButton = root.querySelector("[data-flow-approve]");
        const rejectButton = root.querySelector("[data-flow-reject]");
        const approval = root.querySelector("[data-flow-approval]");
        const mode = root.querySelector("[data-flow-mode]");
        const stepNumber = root.querySelector("[data-flow-step-number]");
        const stepLabel = root.querySelector("[data-flow-step-label]");
        const title = root.querySelector("[data-flow-title]");
        const description = root.querySelector("[data-flow-description]");
        const triggers = Array.from(root.querySelectorAll("[data-flow-trigger]"));
        const paths = Array.from(root.querySelectorAll("[data-flow-path]"));
        const nodes = Array.from(root.querySelectorAll("[data-flow-node]"));
        const statusFields = Array.from(root.querySelectorAll("[data-flow-status]"));
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
            const scene = scenes[index];
            currentStep = index;
            root.dataset.currentStep = String(index);
            root.dataset.outcome = index > 2 ? "approved" : "running";
            stepNumber.textContent = String(index + 1).padStart(2, "0");
            stepLabel.textContent = scene.label;
            title.textContent = scene.title;
            description.textContent = scene.description;
            mode.textContent = scene.approval ? "AUTHORIZATION HOLD" : index === scenes.length - 1 ? "VERIFYING" : "IN PROGRESS";
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
            setStatusFields({
                signature: ["Verified", "verified"], validation: ["Verified", "verified"], authorization: ["Approved", "verified"], connection: ["Closed", "secure"], evidence: ["Verified", "verified"],
            });
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
            const scene = scenes[index];
            if (scene.approval) {
                resumeAfterApproval = true;
                isRunning = false;
                root.dataset.playback = "waiting";
                updatePlayButton();
                return;
            }

            isRunning = true;
            root.dataset.playback = "running";
            animatePath(scene.path, scene.duration);
            updatePlayButton();
            sceneTimer = window.setTimeout(() => {
                if (index >= scenes.length - 1) finishFlow();
                else runScene(index + 1);
            }, scene.duration);
        };

        const showStaticScene = (index) => {
            isRunning = false;
            isFinished = false;
            resumeAfterApproval = false;
            root.dataset.playback = scenes[index].approval ? "waiting" : "stopped";
            setScene(index);
            if (!scenes[index].approval) {
                isWaitingForApproval = false;
                animatePath(scenes[index].path, scenes[index].duration);
            }
            updatePlayButton();
        };

        const reset = () => {
            stopTimers();
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
            stepLabel.textContent = "SYSTEM READY";
            title.textContent = "Nothing crosses the boundary by default.";
            description.textContent = "The portal, AgentLab, and panel are separate. Start the flow to follow one authorized change.";
            approval.hidden = true;
            paths.forEach((path) => path.classList.remove("is-active", "is-complete"));
            nodes.forEach((node) => node.classList.remove("is-active", "is-complete", "is-scanning"));
            triggers.forEach((trigger) => {
                trigger.removeAttribute("aria-current");
                trigger.removeAttribute("data-complete");
            });
            setStatusFields({
                signature: ["Not received", "waiting"], validation: ["Waiting", "waiting"], authorization: ["Required", "waiting"], connection: ["Closed", "secure"], evidence: ["Waiting", "waiting"],
            });
            updatePlayButton();
        };

        playButton.addEventListener("click", () => {
            if (reduceMotion) {
                if (currentStep < 0 || isFinished || root.dataset.outcome === "rejected") showStaticScene(0);
                else if (currentStep < scenes.length - 1 && !isWaitingForApproval) showStaticScene(currentStep + 1);
                else if (currentStep >= scenes.length - 1) finishFlow();
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
            description.textContent = "The plan stops at AgentLab. Nothing reaches the panel PC and the direct connection remains closed.";
            const authorization = root.querySelector('[data-flow-status="authorization"]');
            authorization.textContent = "Rejected";
            authorization.dataset.state = "blocked";
            paths.forEach((path) => path.classList.remove("is-active"));
            updatePlayButton();
        });

        reset();
    });
})();

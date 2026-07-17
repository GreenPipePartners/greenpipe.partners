(() => {
    const hexDigest = (buffer) => Array.from(new Uint8Array(buffer))
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");

    document.querySelectorAll("[data-gateway-upload]").forEach((root) => {
        const form = root.querySelector("[data-gateway-upload-form]");
        const panel = root.querySelector("[data-upload-panel]");
        const fileInput = root.querySelector("[data-upload-file]");
        const status = root.querySelector("[data-upload-status]");
        const button = form?.querySelector("button[type='submit']");
        const csrfToken = form?.querySelector("[name='csrfmiddlewaretoken']")?.value;

        form?.addEventListener("submit", async (event) => {
            event.preventDefault();
            const file = fileInput.files[0];
            if (!file) {
                status.textContent = "Select a gateway or project archive first.";
                return;
            }

            button.disabled = true;
            try {
                status.textContent = "Calculating SHA-256...";
                const checksum = hexDigest(await crypto.subtle.digest("SHA-256", await file.arrayBuffer()));
                status.textContent = "Preparing private upload session...";
                const sessionResponse = await fetch(root.dataset.uploadUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify({
                        panel_id: panel.value,
                        filename: file.name,
                        size_bytes: file.size,
                        sha256: checksum,
                    }),
                });
                const session = await sessionResponse.json();
                if (!sessionResponse.ok) {
                    throw new Error(session.error || "Unable to prepare the upload.");
                }

                status.textContent = "Uploading to private quarantine storage...";
                const payload = new FormData();
                Object.entries(session.upload.fields).forEach(([key, value]) => payload.append(key, value));
                payload.append("file", file);
                const uploadResponse = await fetch(session.upload.url, {method: "POST", body: payload});
                if (!uploadResponse.ok) {
                    throw new Error("The private object upload failed.");
                }
                status.textContent = "Upload complete. The archive is pending integrity and malware review.";
                form.reset();
            } catch (error) {
                status.textContent = error.message;
            } finally {
                button.disabled = false;
            }
        });
    });
})();

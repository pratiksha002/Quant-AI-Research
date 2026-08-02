async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const statusDiv = document.getElementById('statusMessage');
    const uploadBtn = document.getElementById('uploadBtn');

    if (fileInput.files.length === 0) {
        statusDiv.innerText = "Please select files first.";
        statusDiv.style.color = "var(--danger-text)";
        return;
    }

    const formData = new FormData();
    for (const file of fileInput.files) {
        formData.append('files[]', file);
    }

    statusDiv.innerText = "Uploading...";
    statusDiv.style.color = "var(--text-muted)";
    uploadBtn.disabled = true;
    uploadBtn.style.opacity = "0.7";

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            statusDiv.innerText = `Success: ${result.message}`;
            statusDiv.style.color = "var(--success-text)";
            fileInput.value = "";
            loadHistory();
        } else {
            statusDiv.innerText = `Error: ${result.error}`;
            statusDiv.style.color = "var(--danger-text)";
        }
    } catch (error) {
        statusDiv.innerText = "Upload failed due to network error.";
        statusDiv.style.color = "var(--danger-text)";
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.style.opacity = "1";
    }
}

async function loadHistory() {
    const container = document.getElementById('historyContainer');
    const btn = document.querySelector('.btn-refresh');

    // Add a spinning effect to the refresh button
    const icon = btn.querySelector('.icon');
    icon.style.display = 'inline-block';
    icon.style.transition = 'transform 0.5s';
    icon.style.transform = `rotate(360deg)`;

    try {
        const response = await fetch('/history');
        const batches = await response.json();

        container.innerHTML = "";

        if (batches.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--text-muted); background: var(--surface); border-radius: 12px;">
                    No conversions found yet. Upload some files!
                </div>`;
            setTimeout(() => { icon.style.transform = `rotate(0deg)`; }, 500);
            return;
        }

        batches.forEach(batch => {
            const batchCard = document.createElement('div');
            batchCard.className = 'batch-card';

            // Format the datetime to be more readable
            const dateObj = new Date(batch.created_at);
            const dateStr = dateObj.toLocaleString('en-US', {
                month: 'short', day: 'numeric',
                hour: 'numeric', minute: '2-digit', hour12: true
            });

            let filesHtml = batch.files.map(f => {
                const statusLower = f.status.toLowerCase();
                const badgeClass = `badge-${statusLower}`;

                let errorHtml = f.error ? `<span class="file-error">${f.error}</span>` : '';

                let downloadBtn = statusLower === 'completed'
                    ? `<a href="/download/${f.id}" class="btn-small">Download</a>`
                    : '';

                return `
                    <li class="file-item">
                        <div class="file-info">
                            <span class="file-name">📄 ${f.filename}</span>
                            ${errorHtml}
                        </div>
                        <div class="file-actions">
                            <span class="badge ${badgeClass}">${f.status}</span>
                            ${downloadBtn}
                        </div>
                    </li>
                `;
            }).join('');

            batchCard.innerHTML = `
                <div class="batch-header">
                    <span class="batch-time">Batch • ${dateStr}</span>
                    <a href="/download_batch/${batch.batch_uuid}" class="btn-batch">↓ Download All</a>
                </div>
                <ul class="file-list">
                    ${filesHtml}
                </ul>
            `;
            container.appendChild(batchCard);
        });
    } catch (error) {
        container.innerHTML = "<div style='color: var(--danger-text); padding: 1rem;'>Failed to load history.</div>";
    }

    setTimeout(() => { icon.style.transform = `rotate(0deg)`; }, 500);
}

window.onload = loadHistory;
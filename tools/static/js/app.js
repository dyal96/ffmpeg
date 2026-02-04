/**
 * FFmpeg Web UI - Main Application JavaScript
 */

// State
const state = {
    tools: [],
    currentTool: null,
    currentJob: null,
    browsePath: '',
    selectedFile: null,
    fileSelectCallback: null
};

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    loadTools();
    setupSearch();
    setupEventListeners();
});

// Load tools from API
async function loadTools() {
    try {
        const res = await fetch('/api/tools');
        state.tools = await res.json();
        renderToolGrid(state.tools);
        renderNavigation(state.tools);
    } catch (e) {
        showToast('Failed to load tools', 'error');
    }
}

// Render tool grid
function renderToolGrid(tools) {
    const grid = document.getElementById('toolGrid');
    if (!grid) return;

    grid.innerHTML = tools.map(t => `
        <div class="tool-card cat-${t.cat}" data-tool="${t.id}" onclick="openTool('${t.id}')">
            <span class="badge">${t.cat}</span>
            <span class="tool-icon">${t.icon}</span>
            <div class="tool-name">${t.name}</div>
            <div class="tool-desc">${t.desc}</div>
        </div>
    `).join('');
}

// Render sidebar navigation
function renderNavigation(tools) {
    const nav = document.getElementById('navSection');
    if (!nav) return;

    const categories = {
        quick: { title: 'Quick Tools', items: [] },
        advanced: { title: 'Advanced', items: [] },
        utility: { title: 'Utilities', items: [] },
        system: { title: 'System', items: [] }
    };

    tools.forEach(t => {
        if (categories[t.cat]) {
            categories[t.cat].items.push(t);
        }
    });

});

let html = '';

// File browser link (Top Priority)
html += `<div class="nav-title">Quick Access</div>
        <div class="nav-item" onclick="openFileBrowser()">
            <span class="icon">📁</span>
            <span>File Browser</span>
        </div>`;

for (const [key, cat] of Object.entries(categories)) {
    html += `<div class="nav-title">${cat.title}</div>`;
    cat.items.forEach(t => {
        html += `<div class="nav-item" onclick="openTool('${t.id}')">
                <span class="icon">${t.icon}</span>
                <span>${t.name}</span>
            </div>`;
    });
}

    // File browser link
    }

nav.innerHTML = html;
}

// Search functionality
function setupSearch() {
    const input = document.getElementById('searchInput');
    if (!input) return;

    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = state.tools.filter(t =>
            t.name.toLowerCase().includes(query) ||
            t.desc.toLowerCase().includes(query)
        );
        renderToolGrid(filtered);
    });
}

// Open tool modal
function openTool(toolId) {
    const tool = state.tools.find(t => t.id === toolId);
    if (!tool) return;

    // Special handler for browser tool
    if (toolId === 'browser') {
        openFileBrowser();
        return;
    }

    state.currentTool = tool;

    const modal = document.getElementById('toolModal');
    const header = document.getElementById('modalHeader');
    const body = document.getElementById('modalBody');

    header.innerHTML = `<span>${tool.icon}</span> ${tool.name}`;
    body.innerHTML = renderToolForm(tool);

    modal.classList.add('active');
}

// Render tool form based on inputs
function renderToolForm(tool) {
    if (!tool.inputs || tool.inputs.length === 0) {
        return `<p style="color: var(--text-secondary)">This tool has no configurable inputs. Click Run to execute.</p>`;
    }

    return tool.inputs.map(input => {
        const id = `input_${input.name}`;
        const value = input.default !== undefined ? input.default : '';

        switch (input.type) {
            case 'file':
            case 'folder':
                return `<div class="form-group">
                    <label>${input.label}</label>
                    <div class="file-input-wrapper">
                        <input type="text" id="${id}" placeholder="Select ${input.type}..." readonly value="${value}">
                        <button class="btn btn-secondary btn-browse" onclick="browseFile('${id}', '${input.type}', '${input.accept || ''}')">Browse</button>
                        <button class="btn btn-secondary btn-upload" onclick="uploadToolFile('${id}', '${input.accept || ''}')">Upload</button>
                    </div>
                </div>`;

            case 'filelist':
                return `<div class="form-group">
                    <label>${input.label}</label>
                    <div class="file-input-wrapper">
                        <input type="text" id="${id}" placeholder="Select files..." readonly>
                        <button class="btn btn-secondary btn-browse" onclick="browseFiles('${id}', '${input.accept || ''}')">Browse</button>
                    </div>
                    <div id="${id}_list" class="file-list" style="margin-top:8px;"></div>
                </div>`;

            case 'select':
                const options = input.options.map(o =>
                    `<option value="${o}" ${o === value ? 'selected' : ''}>${o}</option>`
                ).join('');
                return `<div class="form-group">
                    <label>${input.label}</label>
                    <select id="${id}">${options}</select>
                </div>`;

            case 'range':
                return `<div class="form-group">
                    <label>${input.label}: <span id="${id}_val">${value}</span></label>
                    <input type="range" id="${id}" min="${input.min || 0}" max="${input.max || 100}" 
                           step="${input.step || 1}" value="${value}"
                           oninput="document.getElementById('${id}_val').textContent = this.value">
                </div>`;

            case 'checkbox':
                const checked = value ? 'checked' : '';
                return `<div class="form-group">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="${id}" ${checked}>
                        <label for="${id}">${input.label}</label>
                    </div>
                </div>`;

            case 'number':
                return `<div class="form-group">
                    <label>${input.label}</label>
                    <input type="number" id="${id}" value="${value}" step="${input.step || 1}">
                </div>`;

            default: // text
                return `<div class="form-group">
                    <label>${input.label}</label>
                    <input type="text" id="${id}" value="${value}" placeholder="${input.placeholder || ''}">
                </div>`;
        }
    }).join('');
}

// Close modal
function closeModal() {
    document.getElementById('toolModal').classList.remove('active');
    state.currentTool = null;
}

// Browse file
function browseFile(inputId, type, accept) {
    state.fileSelectCallback = (path) => {
        document.getElementById(inputId).value = path;
    };
    openFileBrowser(type === 'folder');
}

// Browse multiple files
function browseFiles(inputId, accept) {
    // For now, just allow single selection
    browseFile(inputId, 'file', accept);
}

// File Browser Modal
async function openFileBrowser(foldersOnly = false) {
    const modal = document.getElementById('browseModal');
    modal.classList.add('active');
    modal.dataset.foldersOnly = foldersOnly;
    await loadDirectory('');
}

function closeBrowseModal() {
    document.getElementById('browseModal').classList.remove('active');
    state.fileSelectCallback = null;
}

async function loadDirectory(path) {
    state.browsePath = path;
    const container = document.getElementById('browseContent');

    try {
        const res = await fetch(`/api/browse/${path}`);
        const data = await res.json();

        // Breadcrumb
        document.getElementById('browsePath').textContent = '/' + (path || 'Home');

        // Parent link
        let html = '';
        if (data.parent !== null) {
            html += `<div class="file-item" onclick="loadDirectory('${data.parent}')">
                <span class="file-icon">📁</span>
                <span class="file-name">..</span>
            </div>`;
        }

        const foldersOnly = document.getElementById('browseModal').dataset.foldersOnly === 'true';

        data.items.forEach(item => {
            if (foldersOnly && !item.is_dir) return;

            const icon = item.is_dir ? '📁' : (
                item.type === 'video' ? '🎬' :
                    item.type === 'audio' ? '🎵' :
                        item.type === 'image' ? '🖼️' : '📄'
            );

            const onclick = item.is_dir ?
                `loadDirectory('${item.path}')` :
                `selectFile('${item.path}', '${item.name}')`;

            html += `<div class="file-item" onclick="${onclick}">
                <span class="file-icon">${icon}</span>
                <span class="file-name">${item.name}</span>
                ${item.size ? `<span class="file-size">${item.size}</span>` : ''}
            </div>`;
        });

        container.innerHTML = html || '<p style="color:var(--text-muted);padding:20px;">Empty folder</p>';
    } catch (e) {
        container.innerHTML = '<p style="color:var(--error);padding:20px;">Failed to load directory</p>';
    }
}

function selectFile(path, name) {
    state.selectedFile = path;

    // Highlight selected
    document.querySelectorAll('#browseContent .file-item').forEach(el => el.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

function confirmFileSelection() {
    if (state.selectedFile && state.fileSelectCallback) {
        state.fileSelectCallback(state.selectedFile);
    }
    closeBrowseModal();
}

function selectCurrentFolder() {
    if (state.fileSelectCallback) {
        state.fileSelectCallback(state.browsePath || '/');
    }
    closeBrowseModal();
}

// Upload File
function uploadToolFile(inputId, accept) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        showToast('Uploading...', 'info');

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (data.error) {
                showToast(data.error, 'error');
            } else {
                document.getElementById(inputId).value = data.path;
                showToast('Upload complete', 'success');
            }
        } catch (err) {
            showToast('Upload failed', 'error');
        }
    };

    input.click();
}

// Run tool
async function runTool() {
    if (!state.currentTool) return;

    const tool = state.currentTool;
    const data = {};

    // Collect form values
    tool.inputs.forEach(input => {
        const el = document.getElementById(`input_${input.name}`);
        if (el) {
            if (input.type === 'checkbox') {
                data[input.name] = el.checked;
            } else if (input.type === 'number' || input.type === 'range') {
                data[input.name] = parseFloat(el.value);
            } else {
                data[input.name] = el.value;
            }
        }
    });

    // Special handling for yt-dlp to allow empty input if we have URL
    // Actually, 'input' is not in ytdl inputs list, so this is fine.
    // But for other tools, input might be required.
    // We rely on backend validation or add it here.

    // Close tool modal
    closeModal();

    // Show progress panel
    showProgress();
    updateProgress(0, 'Starting...');

    try {
        const res = await fetch(`/api/tools/${tool.id}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (result.error) {
            showToast(result.error, 'error');
            hideProgress();
            return;
        }

        state.currentJob = result.job_id;
        showToast(`Started: ${tool.name}`, 'info');

        // Start progress polling
        pollProgress(result.job_id);

    } catch (e) {
        showToast('Failed to start job', 'error');
        hideProgress();
    }
}

// Poll job progress
async function pollProgress(jobId) {
    const eventSource = new EventSource(`/api/jobs/${jobId}/progress`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
            eventSource.close();
            hideProgress();
            return;
        }

        updateProgress(data.progress, data.status);

        // Update console
        const console = document.getElementById('consoleOutput');
        if (console && data.logs) {
            console.innerHTML = data.logs.map(l =>
                `<div class="console-line">${escapeHtml(l)}</div>`
            ).join('');
            console.scrollTop = console.scrollHeight;
        }

        if (data.status === 'done') {
            eventSource.close();
            updateProgress(100, 'Complete!');
            showToast('Job completed successfully!', 'success');
            setTimeout(hideProgress, 3000);
        } else if (data.status === 'error') {
            eventSource.close();
            showToast('Job failed!', 'error');
            setTimeout(hideProgress, 5000);
        } else if (data.status === 'stopped') {
            eventSource.close();
            showToast('Job stopped', 'info');
            hideProgress();
        }
        if (data.status === 'done') {
            eventSource.close();
            updateProgress(100, 'Complete!');
            showToast('Job completed successfully!', 'success');
            setTimeout(hideProgress, 3000);
        } else if (data.status === 'error') {
            eventSource.close();
            showToast('Job failed!', 'error');
            setTimeout(hideProgress, 5000);
        } else if (data.status === 'stopped') {
            eventSource.close();
            showToast('Job stopped', 'info');
            hideProgress();
        }
    };

    // Add specific yt-dlp handling logic if needed in message parsing
    // but the backend sends 'progress' and 'logs', which we already handle.
    // The webui.py logs parsing for yt-dlp needs to be robust, 
    // but here in JS we just display what we get.

    eventSource.onerror = () => {
        eventSource.close();
    };
}

// Stop current job
async function stopJob() {
    if (!state.currentJob) return;

    try {
        await fetch(`/api/jobs/${state.currentJob}/stop`, { method: 'POST' });
        showToast('Stopping job...', 'info');
    } catch (e) {
        showToast('Failed to stop job', 'error');
    }
}

// Progress panel
function showProgress() {
    document.getElementById('progressPanel').classList.add('active');
}

function hideProgress() {
    document.getElementById('progressPanel').classList.remove('active');
    state.currentJob = null;
}

function updateProgress(percent, status) {
    document.getElementById('progressBar').style.width = `${percent}%`;
    document.getElementById('progressText').textContent = `${percent}% - ${status || 'Processing...'}`;
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const id = 'toast_' + Date.now();

    const icons = { success: '✓', error: '✕', info: 'ℹ' };

    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setupEventListeners() {
    // Close modals on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeBrowseModal();
        }
    });

    // Click outside modal to close
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

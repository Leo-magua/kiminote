/**
 * AI Notes - Frontend Application
 */

// Configure marked.js options
marked.setOptions({
    gfm: true,              // GitHub Flavored Markdown
    breaks: true,           // Convert line breaks to <br>
    tables: true,           // Enable tables
    sanitize: false,        // Disable built-in sanitization (we use DOMPurify)
    smartLists: true,       // Use smarter list behavior
    smartypants: true,      // Use smart punctuation
    highlight: function(code, lang) {
        // Use highlight.js for syntax highlighting
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (e) {
                console.warn('Highlight error:', e);
            }
        }
        // Auto-detect language if not specified
        try {
            return hljs.highlightAuto(code).value;
        } catch (e) {
            console.warn('Auto-highlight error:', e);
        }
        return code;
    }
});

// Custom renderer for task lists
const renderer = new marked.Renderer();
const originalListitem = renderer.listitem;
renderer.listitem = function(text, task, checked) {
    if (task) {
        return `<li class="task-list-item">
            <input type="checkbox" ${checked ? 'checked' : ''} disabled> 
            ${text.replace(/^\[x\]\s*|^\[ \]\s*/, '')}
        </li>`;
    }
    return originalListitem.call(this, text, task, checked);
};
marked.setOptions({ renderer: renderer });

// XSS Sanitization configuration
const DOMPURIFY_CONFIG = {
    ALLOWED_TAGS: [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del', 's',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'task-list-item',
        'blockquote', 'code', 'pre',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'hr',
        'input'  // For task list checkboxes
    ],
    ALLOWED_ATTR: [
        'href', 'title', 'target', 'rel',
        'src', 'alt', 'width', 'height',
        'class', 'id',
        'checked', 'type', 'disabled'  // For task list checkboxes
    ],
    ALLOW_DATA_ATTR: false,
    SANITIZE_DOM: true
};

// Global state
let currentNote = null;
let allNotes = [];
let allTags = [];
let currentTagFilter = null;
let isAiAvailable = false;
let currentShares = [];

// DOM Elements
const elements = {
    // Views
    notesListView: document.getElementById('notesListView'),
    noteEditView: document.getElementById('noteEditView'),
    searchResultsView: document.getElementById('searchResultsView'),
    
    // Sidebar
    searchInput: document.getElementById('searchInput'),
    smartSearchBtn: document.getElementById('smartSearchBtn'),
    newNoteBtn: document.getElementById('newNoteBtn'),
    tagsList: document.getElementById('tagsList'),
    notesCount: document.getElementById('notesCount'),
    exportJsonBtn: document.getElementById('exportJsonBtn'),
    exportMdBtn: document.getElementById('exportMdBtn'),
    
    // Notes list
    notesList: document.getElementById('notesList'),
    sortSelect: document.getElementById('sortSelect'),
    
    // Editor
    backBtn: document.getElementById('backBtn'),
    previewBtn: document.getElementById('previewBtn'),
    aiEnhanceBtn: document.getElementById('aiEnhanceBtn'),
    saveBtn: document.getElementById('saveBtn'),
    deleteBtn: document.getElementById('deleteBtn'),
    noteTitle: document.getElementById('noteTitle'),
    noteContent: document.getElementById('noteContent'),
    previewContent: document.getElementById('previewContent'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    editTab: document.getElementById('editTab'),
    previewTab: document.getElementById('previewTab'),
    noteTags: document.getElementById('noteTags'),
    noteSummary: document.getElementById('noteSummary'),
    noteDates: document.getElementById('noteDates'),
    aiActions: document.getElementById('aiActions'),
    generateSummaryBtn: document.getElementById('generateSummaryBtn'),
    generateTagsBtn: document.getElementById('generateTagsBtn'),
    
    // Search results
    closeSearchBtn: document.getElementById('closeSearchBtn'),
    searchQuery: document.getElementById('searchQuery'),
    searchResults: document.getElementById('searchResults'),
    
    // Modals
    smartSearchModal: document.getElementById('smartSearchModal'),
    smartSearchInput: document.getElementById('smartSearchInput'),
    doSmartSearch: document.getElementById('doSmartSearch'),
    aiEnhanceModal: document.getElementById('aiEnhanceModal'),
    enhanceInstruction: document.getElementById('enhanceInstruction'),
    doEnhance: document.getElementById('doEnhance'),
    enhanceResult: document.getElementById('enhanceResult'),
    modalCloseBtns: document.querySelectorAll('.modal-close'),
    
    // Toast
    toast: document.getElementById('toast'),
    
    // Share Modal
    shareModal: document.getElementById('shareModal'),
    sharePermission: document.getElementById('sharePermission'),
    sharePassword: document.getElementById('sharePassword'),
    shareExpires: document.getElementById('shareExpires'),
    passwordGroup: document.getElementById('passwordGroup'),
    createShareBtn: document.getElementById('createShareBtn'),
    createShareForm: document.getElementById('createShareForm'),
    shareResult: document.getElementById('shareResult'),
    shareUrlInput: document.getElementById('shareUrlInput'),
    copyShareUrlBtn: document.getElementById('copyShareUrlBtn'),
    createNewShareBtn: document.getElementById('createNewShareBtn'),
    closeShareBtn: document.getElementById('closeShareBtn'),
    shareInfoPermission: document.getElementById('shareInfoPermission'),
    shareInfoExpires: document.getElementById('shareInfoExpires'),
    existingShares: document.getElementById('existingShares'),
    sharesList: document.getElementById('sharesList'),
    shareBtn: document.getElementById('shareBtn')
};

// API Helper
const api = {
    async get(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },
    
    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },
    
    async put(url, data) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },
    
    async delete(url) {
        const response = await fetch(url, { method: 'DELETE' });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },
    
    async download(url, filename) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(await response.text());
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
    }
};

// Toast notification
function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.remove('hidden');
    
    setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

// View management
function showView(viewName) {
    elements.notesListView.classList.add('hidden');
    elements.noteEditView.classList.add('hidden');
    elements.searchResultsView.classList.add('hidden');
    
    switch(viewName) {
        case 'list':
            elements.notesListView.classList.remove('hidden');
            break;
        case 'edit':
            elements.noteEditView.classList.remove('hidden');
            break;
        case 'search':
            elements.searchResultsView.classList.remove('hidden');
            break;
    }
}

// Modal management
function toggleModal(modal, show) {
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Render notes list
function renderNotes(notes) {
    if (notes.length === 0) {
        elements.notesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>还没有笔记</h3>
                <p>点击 "新建笔记" 开始创建</p>
            </div>
        `;
        return;
    }
    
    elements.notesList.innerHTML = notes.map(note => `
        <div class="note-card" data-id="${note.id}">
            <h3>${escapeHtml(note.title)}</h3>
            <div class="note-summary">${escapeHtml(note.summary || note.content.substring(0, 150) + '...')}</div>
            <div class="note-meta">
                <div class="note-tags">
                    ${note.tags.map(tag => `<span class="note-tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
                <span>${formatDate(note.updated_at)}</span>
            </div>
        </div>
    `).join('');
    
    // Add click handlers
    document.querySelectorAll('.note-card').forEach(card => {
        card.addEventListener('click', () => {
            const id = parseInt(card.dataset.id);
            openNote(id);
        });
    });
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render tags
function renderTags() {
    if (allTags.length === 0) {
        elements.tagsList.innerHTML = '<span style="color: var(--text-muted); font-size: 12px;">暂无标签</span>';
        return;
    }
    
    elements.tagsList.innerHTML = allTags.map(tag => `
        <span class="tag ${tag === currentTagFilter ? 'active' : ''}" data-tag="${escapeHtml(tag)}">
            ${escapeHtml(tag)}
        </span>
    `).join('');
    
    // Add click handlers
    document.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', () => {
            const tagName = tag.dataset.tag;
            if (currentTagFilter === tagName) {
                currentTagFilter = null;
            } else {
                currentTagFilter = tagName;
            }
            renderTags();
            filterNotes();
        });
    });
}

// Filter notes
function filterNotes() {
    let filtered = allNotes;
    
    // Filter by tag
    if (currentTagFilter) {
        filtered = filtered.filter(note => note.tags.includes(currentTagFilter));
    }
    
    // Filter by search
    const searchTerm = elements.searchInput.value.toLowerCase().trim();
    if (searchTerm) {
        filtered = filtered.filter(note => 
            note.title.toLowerCase().includes(searchTerm) ||
            note.content.toLowerCase().includes(searchTerm) ||
            note.tags.some(tag => tag.toLowerCase().includes(searchTerm))
        );
    }
    
    // Sort
    const sortBy = elements.sortSelect.value;
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'created':
                return new Date(b.created_at) - new Date(a.created_at);
            case 'title':
                return a.title.localeCompare(b.title);
            case 'updated':
            default:
                return new Date(b.updated_at) - new Date(a.updated_at);
        }
    });
    
    renderNotes(filtered);
}

// Open note for editing
async function openNote(id) {
    try {
        currentNote = await api.get(`/api/notes/${id}`);
        
        elements.noteTitle.value = currentNote.title;
        elements.noteContent.value = currentNote.content;
        
        renderNoteMeta();
        
        // Show AI actions if available
        elements.aiActions.style.display = isAiAvailable ? 'flex' : 'none';
        elements.aiEnhanceBtn.style.display = isAiAvailable ? 'inline-block' : 'none';
        
        // Show share button
        elements.shareBtn.style.display = 'inline-block';
        
        showView('edit');
        updatePreview();
    } catch (error) {
        showToast('加载笔记失败: ' + error.message, 'error');
    }
}

// Render note meta information
function renderNoteMeta() {
    if (!currentNote) return;
    
    // Tags
    elements.noteTags.innerHTML = currentNote.tags.map(tag => 
        `<span class="tag">${escapeHtml(tag)}</span>`
    ).join('');
    
    // Summary
    if (currentNote.summary) {
        elements.noteSummary.innerHTML = `<strong>🤖 AI 摘要:</strong> ${escapeHtml(currentNote.summary)}`;
    } else {
        elements.noteSummary.innerHTML = '';
    }
    
    // Dates
    elements.noteDates.innerHTML = `
        创建: ${formatDate(currentNote.created_at)} | 
        更新: ${formatDate(currentNote.updated_at)}
    `;
}

// Create new note
async function createNewNote() {
    currentNote = null;
    elements.noteTitle.value = '';
    elements.noteContent.value = '';
    elements.noteTags.innerHTML = '';
    elements.noteSummary.innerHTML = '';
    elements.noteDates.innerHTML = '';
    elements.aiActions.style.display = isAiAvailable ? 'flex' : 'none';
    elements.aiEnhanceBtn.style.display = isAiAvailable ? 'inline-block' : 'none';
    
    // Hide share button for new notes
    elements.shareBtn.style.display = 'none';
    
    showView('edit');
    elements.noteTitle.focus();
}

// Save note
async function saveNote() {
    const title = elements.noteTitle.value.trim();
    const content = elements.noteContent.value.trim();
    
    if (!title) {
        showToast('请输入标题', 'error');
        return;
    }
    
    try {
        if (currentNote) {
            // Update existing
            await api.put(`/api/notes/${currentNote.id}`, { title, content });
            showToast('笔记已更新');
        } else {
            // Create new
            const result = await api.post('/api/notes', { title, content });
            currentNote = result;
            showToast('笔记已创建');
        }
        
        // Reload notes
        await loadNotes();
        renderNoteMeta();
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
}

// Delete note
async function deleteNote() {
    if (!currentNote) {
        showView('list');
        return;
    }
    
    if (!confirm('确定要删除这个笔记吗？')) return;
    
    try {
        await api.delete(`/api/notes/${currentNote.id}`);
        showToast('笔记已删除');
        await loadNotes();
        showView('list');
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// Load all notes
async function loadNotes() {
    try {
        allNotes = await api.get('/api/notes');
        elements.notesCount.textContent = `${allNotes.length} 笔记`;
        filterNotes();
    } catch (error) {
        showToast('加载笔记失败: ' + error.message, 'error');
    }
}

// Load all tags
async function loadTags() {
    try {
        const result = await api.get('/api/tags');
        allTags = result.tags;
        renderTags();
    } catch (error) {
        console.error('Failed to load tags:', error);
    }
}

// Check AI availability
async function checkAiStatus() {
    try {
        const stats = await api.get('/api/stats');
        isAiAvailable = stats.ai_available;
        elements.aiEnhanceBtn.style.display = isAiAvailable ? 'inline-block' : 'none';
    } catch (error) {
        console.error('Failed to check AI status:', error);
    }
}

// Update markdown preview
function updatePreview() {
    const content = elements.noteContent.value;
    
    // Parse markdown
    let html = marked.parse(content);
    
    // Sanitize HTML to prevent XSS attacks
    if (typeof DOMPurify !== 'undefined') {
        html = DOMPurify.sanitize(html, DOMPURIFY_CONFIG);
    }
    
    elements.previewContent.innerHTML = html;
    
    // Apply syntax highlighting
    elements.previewContent.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Generate summary
async function generateSummary() {
    if (!currentNote) {
        showToast('请先保存笔记', 'error');
        return;
    }
    
    elements.generateSummaryBtn.innerHTML = '<span class="spinner"></span>';
    elements.generateSummaryBtn.disabled = true;
    
    try {
        const result = await api.post(`/api/notes/${currentNote.id}/summarize`);
        currentNote.summary = result.summary;
        renderNoteMeta();
        showToast('摘要已生成');
    } catch (error) {
        showToast('生成摘要失败: ' + error.message, 'error');
    } finally {
        elements.generateSummaryBtn.innerHTML = '生成摘要';
        elements.generateSummaryBtn.disabled = false;
    }
}

// Generate tags
async function generateTags() {
    if (!currentNote) {
        showToast('请先保存笔记', 'error');
        return;
    }
    
    elements.generateTagsBtn.innerHTML = '<span class="spinner"></span>';
    elements.generateTagsBtn.disabled = true;
    
    try {
        const result = await api.post(`/api/notes/${currentNote.id}/tags`);
        currentNote.tags = result.tags;
        renderNoteMeta();
        await loadTags();
        showToast('标签已生成');
    } catch (error) {
        showToast('生成标签失败: ' + error.message, 'error');
    } finally {
        elements.generateTagsBtn.innerHTML = '生成标签';
        elements.generateTagsBtn.disabled = false;
    }
}

// Smart search
async function performSmartSearch() {
    const query = elements.smartSearchInput.value.trim();
    if (!query) return;
    
    elements.doSmartSearch.innerHTML = '<span class="spinner"></span> 搜索中...';
    elements.doSmartSearch.disabled = true;
    
    try {
        const result = await api.post('/api/search/smart', { query });
        
        elements.searchQuery.textContent = `查询: "${query}"`;
        
        if (result.results.length === 0) {
            elements.searchResults.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3>未找到相关笔记</h3>
                    <p>尝试使用不同的关键词</p>
                </div>
            `;
        } else {
            elements.searchResults.innerHTML = result.results.map(note => `
                <div class="note-item" data-id="${note.id}">
                    <div class="relevance">相关度: ${note.search_relevance}%</div>
                    <h4>${escapeHtml(note.title)}</h4>
                    <p>${escapeHtml(note.search_reason)}</p>
                </div>
            `).join('');
            
            // Add click handlers
            document.querySelectorAll('.note-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = parseInt(item.dataset.id);
                    toggleModal(elements.smartSearchModal, false);
                    openNote(id);
                });
            });
        }
        
        showView('search');
        toggleModal(elements.smartSearchModal, false);
    } catch (error) {
        showToast('搜索失败: ' + error.message, 'error');
    } finally {
        elements.doSmartSearch.innerHTML = '搜索';
        elements.doSmartSearch.disabled = false;
    }
}

// Enhance text
async function enhanceText() {
    const content = elements.noteContent.value.trim();
    if (!content) {
        showToast('请先输入内容', 'error');
        return;
    }
    
    const instruction = elements.enhanceInstruction.value;
    
    elements.doEnhance.innerHTML = '<span class="spinner"></span> 处理中...';
    elements.doEnhance.disabled = true;
    
    try {
        const result = await api.post('/api/ai/enhance', { content, instruction });
        
        elements.enhanceResult.innerHTML = `
            <h4>增强结果:</h4>
            <p>${escapeHtml(result.enhanced)}</p>
            <button id="useEnhanced" class="btn-primary" style="margin-top: 12px;">使用此文本</button>
        `;
        elements.enhanceResult.classList.add('show');
        
        document.getElementById('useEnhanced').addEventListener('click', () => {
            elements.noteContent.value = result.enhanced;
            toggleModal(elements.aiEnhanceModal, false);
            elements.enhanceResult.classList.remove('show');
            showToast('文本已更新');
        });
    } catch (error) {
        showToast('增强失败: ' + error.message, 'error');
    } finally {
        elements.doEnhance.innerHTML = '增强';
        elements.doEnhance.disabled = false;
    }
}

// Event Listeners
elements.newNoteBtn.addEventListener('click', createNewNote);
elements.backBtn.addEventListener('click', () => showView('list'));
elements.saveBtn.addEventListener('click', saveNote);
elements.deleteBtn.addEventListener('click', deleteNote);

elements.searchInput.addEventListener('input', filterNotes);
elements.sortSelect.addEventListener('change', filterNotes);

elements.previewBtn.addEventListener('click', () => {
    updatePreview();
    elements.tabBtns.forEach(btn => btn.classList.toggle('active'));
    elements.editTab.classList.toggle('active');
    elements.previewTab.classList.toggle('active');
});

elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        elements.tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        elements.editTab.classList.toggle('active', tab === 'edit');
        elements.previewTab.classList.toggle('active', tab === 'preview');
        
        if (tab === 'preview') {
            updatePreview();
        }
    });
});

elements.noteContent.addEventListener('input', () => {
    // Auto-update preview if visible
    if (elements.previewTab.classList.contains('active')) {
        updatePreview();
    }
});

elements.generateSummaryBtn.addEventListener('click', generateSummary);
elements.generateTagsBtn.addEventListener('click', generateTags);

elements.smartSearchBtn.addEventListener('click', () => {
    elements.smartSearchInput.value = '';
    toggleModal(elements.smartSearchModal, true);
});

elements.closeSearchBtn.addEventListener('click', () => showView('list'));

elements.doSmartSearch.addEventListener('click', performSmartSearch);
elements.smartSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSmartSearch();
});

elements.aiEnhanceBtn.addEventListener('click', () => {
    elements.enhanceResult.classList.remove('show');
    toggleModal(elements.aiEnhanceModal, true);
});

elements.doEnhance.addEventListener('click', enhanceText);

elements.modalCloseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        toggleModal(elements.smartSearchModal, false);
        toggleModal(elements.aiEnhanceModal, false);
        toggleModal(elements.shareModal, false);
    });
});

elements.exportJsonBtn.addEventListener('click', async () => {
    try {
        await api.download('/api/export/json', 'notes_export.json');
        showToast('导出成功');
    } catch (error) {
        showToast('导出失败: ' + error.message, 'error');
    }
});

elements.exportMdBtn.addEventListener('click', async () => {
    try {
        await api.download('/api/export/markdown', 'notes_export.md');
        showToast('导出成功');
    } catch (error) {
        showToast('导出失败: ' + error.message, 'error');
    }
});

// Logout button
document.getElementById('logoutBtn').addEventListener('click', logout);

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        toggleModal(e.target, false);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (!elements.noteEditView.classList.contains('hidden')) {
            saveNote();
        }
    }
    
    // Esc to go back
    if (e.key === 'Escape') {
        if (!elements.shareModal.classList.contains('hidden')) {
            toggleModal(elements.shareModal, false);
        } else if (!elements.smartSearchModal.classList.contains('hidden')) {
            toggleModal(elements.smartSearchModal, false);
        } else if (!elements.aiEnhanceModal.classList.contains('hidden')) {
            toggleModal(elements.aiEnhanceModal, false);
        } else if (!elements.noteEditView.classList.contains('hidden')) {
            showView('list');
        }
    }
});

// Initialize
async function init() {
    await checkAiStatus();
    await loadNotes();
    await loadTags();
}

init();

// ========== Share Functions ==========

// Open share modal
function openShareModal() {
    if (!currentNote) {
        showToast('请先保存笔记', 'error');
        return;
    }
    
    // Reset form
    elements.sharePermission.value = 'public';
    elements.sharePassword.value = '';
    elements.shareExpires.value = '7';
    elements.passwordGroup.style.display = 'none';
    
    // Show create form, hide result
    elements.createShareForm.classList.remove('hidden');
    elements.shareResult.classList.add('hidden');
    elements.existingShares.classList.remove('hidden');
    
    // Load existing shares
    loadNoteShares();
    
    toggleModal(elements.shareModal, true);
}

// Load shares for current note
async function loadNoteShares() {
    if (!currentNote) return;
    
    try {
        const result = await api.get(`/api/shares/note/${currentNote.id}`);
        currentShares = result.shares;
        renderSharesList();
    } catch (error) {
        console.error('Failed to load shares:', error);
        elements.sharesList.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">加载分享列表失败</p>';
    }
}

// Render shares list
function renderSharesList() {
    if (currentShares.length === 0) {
        elements.sharesList.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">暂无分享链接</p>';
        return;
    }
    
    elements.sharesList.innerHTML = currentShares.map(share => {
        const isExpired = share.is_expired;
        const permissionText = {
            'public': '🔓 公开',
            'password': '🔐 密码',
            'private': '🔒 私密'
        }[share.permission] || share.permission;
        
        const expiresText = share.expires_at 
            ? new Date(share.expires_at).toLocaleDateString('zh-CN')
            : '永不过期';
        
        return `
            <div class="share-item ${isExpired ? 'expired' : ''}">
                <div class="share-item-info">
                    <div class="share-item-url">${share.share_url}</div>
                    <div class="share-item-meta">
                        <span class="share-badge ${share.permission} ${isExpired ? 'expired' : ''}">${permissionText}</span>
                        <span>过期: ${expiresText}</span>
                        <span>访问: ${share.access_count}次</span>
                    </div>
                </div>
                <div class="share-item-actions">
                    <button class="share-item-btn copy-btn" data-token="${share.share_token}" title="复制链接">📋</button>
                    <button class="share-item-btn delete-btn" data-token="${share.share_token}" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
    
    // Add event listeners
    document.querySelectorAll('.share-item-btn.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const share = currentShares.find(s => s.share_token === btn.dataset.token);
            if (share) {
                copyToClipboard(share.share_url);
                showToast('链接已复制');
            }
        });
    });
    
    document.querySelectorAll('.share-item-btn.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteShare(btn.dataset.token));
    });
}

// Create share
async function createShare() {
    if (!currentNote) return;
    
    const permission = elements.sharePermission.value;
    const password = elements.sharePassword.value;
    const expiresDays = elements.shareExpires.value ? parseInt(elements.shareExpires.value) : null;
    
    // Validate password for password-protected shares
    if (permission === 'password' && (!password || password.length < 4)) {
        showToast('请输入至少4位密码', 'error');
        elements.sharePassword.focus();
        return;
    }
    
    elements.createShareBtn.innerHTML = '<span class="spinner"></span> 创建中...';
    elements.createShareBtn.disabled = true;
    
    try {
        const result = await api.post('/api/shares', {
            note_id: currentNote.id,
            permission: permission,
            password: password || null,
            expires_days: expiresDays
        });
        
        // Show result
        elements.createShareForm.classList.add('hidden');
        elements.shareResult.classList.remove('hidden');
        elements.existingShares.classList.add('hidden');
        
        // Fill result
        elements.shareUrlInput.value = result.share_url;
        
        const permissionLabels = {
            'public': '🔓 公开访问',
            'password': '🔐 密码保护',
            'private': '🔒 私密（仅自己）'
        };
        elements.shareInfoPermission.textContent = permissionLabels[result.permission] || result.permission;
        
        elements.shareInfoExpires.textContent = result.expires_at 
            ? new Date(result.expires_at).toLocaleString('zh-CN')
            : '永不过期';
        
        showToast('分享链接创建成功');
    } catch (error) {
        showToast('创建分享失败: ' + error.message, 'error');
    } finally {
        elements.createShareBtn.innerHTML = '创建分享';
        elements.createShareBtn.disabled = false;
    }
}

// Delete share
async function deleteShare(shareToken) {
    if (!confirm('确定要删除这个分享链接吗？')) return;
    
    try {
        await api.delete(`/api/shares/${shareToken}`);
        showToast('分享链接已删除');
        loadNoteShares(); // Refresh list
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

// Reset share modal
function resetShareModal() {
    elements.sharePermission.value = 'public';
    elements.sharePassword.value = '';
    elements.shareExpires.value = '7';
    elements.passwordGroup.style.display = 'none';
    elements.createShareForm.classList.remove('hidden');
    elements.shareResult.classList.add('hidden');
    elements.existingShares.classList.remove('hidden');
}

// Share event listeners
elements.shareBtn.addEventListener('click', openShareModal);

elements.sharePermission.addEventListener('change', () => {
    const showPassword = elements.sharePermission.value === 'password';
    elements.passwordGroup.style.display = showPassword ? 'block' : 'none';
    if (showPassword) {
        elements.sharePassword.focus();
    }
});

elements.createShareBtn.addEventListener('click', createShare);

elements.copyShareUrlBtn.addEventListener('click', () => {
    copyToClipboard(elements.shareUrlInput.value);
    showToast('链接已复制到剪贴板');
});

elements.createNewShareBtn.addEventListener('click', resetShareModal);

elements.closeShareBtn.addEventListener('click', () => {
    toggleModal(elements.shareModal, false);
});

// Close share modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === elements.shareModal) {
        toggleModal(elements.shareModal, false);
    }
});

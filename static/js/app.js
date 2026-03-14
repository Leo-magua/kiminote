/**
 * AI Notes - Frontend Application
 * Integrated with TipTap Rich Text Editor
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
let collaboratedNotes = [];  // Notes user collaborates on

// Rich Text Editor state
let richTextEditor = null;
let currentAttachments = [];
let isEditorReady = false;
let currentTab = 'edit'; // 'edit', 'preview', 'markdown'

// Turndown instance for HTML to Markdown conversion
let turndownService = null;

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
    markdownContent: document.getElementById('markdownContent'),  // Markdown textarea
    previewContent: document.getElementById('previewContent'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    editTab: document.getElementById('editTab'),
    previewTab: document.getElementById('previewTab'),
    markdownTab: document.getElementById('markdownTab'),
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
    shareBtn: document.getElementById('shareBtn'),
    
    // Stats Modal
    statsModal: document.getElementById('statsModal'),
    statsBtn: document.getElementById('statsBtn'),
    
    // Collaboration
    collaborationBtn: document.getElementById('collaborationBtn'),
    versionsBtn: document.getElementById('versionsBtn'),
    collaborationModal: document.getElementById('collaborationModal'),
    versionsModal: document.getElementById('versionsModal'),
    collaboratorUsername: document.getElementById('collaboratorUsername'),
    collaboratorPermission: document.getElementById('collaboratorPermission'),
    addCollaboratorBtn: document.getElementById('addCollaboratorBtn'),
    
    // Upload Modals
    imageUploadModal: document.getElementById('imageUploadModal'),
    attachmentUploadModal: document.getElementById('attachmentUploadModal'),
    tableInsertModal: document.getElementById('tableInsertModal'),
    linkInsertModal: document.getElementById('linkInsertModal'),
    
    // Markdown Import/Export buttons
    mdImportBtn: document.getElementById('mdImportBtn'),
    mdExportBtn: document.getElementById('mdExportBtn')
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
    },
    
    async uploadFile(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        return response.json();
    }
};

// Initialize Turndown service for HTML to Markdown conversion
function initTurndown() {
    if (typeof TurndownService !== 'undefined' && !turndownService) {
        turndownService = new TurndownService({
            headingStyle: 'atx',
            codeBlockStyle: 'fenced',
            bulletListMarker: '-'
        });
        
        // Configure task list handling
        turndownService.addRule('taskListItem', {
            filter: function(node) {
                return node.type === 'checkbox' && 
                       node.parentNode && 
                       node.parentNode.nodeName === 'LI';
            },
            replacement: function(content, node) {
                return (node.checked ? '[x]' : '[ ]') + ' ';
            }
        });
        
        // Handle strike through
        turndownService.addRule('strikethrough', {
            filter: ['del', 's', 'strike'],
            replacement: function(content) {
                return '~~' + content + '~~';
            }
        });
        
        // Handle highlight
        turndownService.addRule('highlight', {
            filter: 'mark',
            replacement: function(content) {
                return '==' + content + '==';
            }
        });
    }
}

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
            <div class="note-summary">${escapeHtml(note.summary || stripHtml(note.content).substring(0, 150) + '...')}</div>
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

// Strip HTML tags
function stripHtml(html) {
    if (!html) return '';
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
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

// ========== Table Context Menu ==========

// Setup table context menu
function setupTableContextMenu() {
    const editor = document.getElementById('editor');
    if (!editor) return;
    
    // Create context menu element
    let contextMenu = document.getElementById('tableContextMenu');
    if (!contextMenu) {
        contextMenu = document.createElement('div');
        contextMenu.id = 'tableContextMenu';
        contextMenu.className = 'table-context-menu hidden';
        contextMenu.innerHTML = `
            <div class="context-menu-item" data-action="addRowBefore">在上方添加行</div>
            <div class="context-menu-item" data-action="addRowAfter">在下方添加行</div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" data-action="addColumnBefore">在左侧添加列</div>
            <div class="context-menu-item" data-action="addColumnAfter">在右侧添加列</div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" data-action="deleteRow">删除当前行</div>
            <div class="context-menu-item" data-action="deleteColumn">删除当前列</div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" data-action="toggleHeader">切换表头</div>
            <div class="context-menu-item danger" data-action="deleteTable">删除表格</div>
        `;
        document.body.appendChild(contextMenu);
        
        // Add click handlers
        contextMenu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', handleTableContextMenuAction);
        });
    }
    
    // Show context menu on right-click in table
    editor.addEventListener('contextmenu', (e) => {
        const cell = e.target.closest('td, th');
        if (cell && richTextEditor && richTextEditor.isInTable()) {
            e.preventDefault();
            showTableContextMenu(e.clientX, e.clientY);
        }
    });
    
    // Hide context menu on click elsewhere
    document.addEventListener('click', (e) => {
        if (!contextMenu.contains(e.target)) {
            contextMenu.classList.add('hidden');
        }
    });
}

// Show table context menu
function showTableContextMenu(x, y) {
    const menu = document.getElementById('tableContextMenu');
    if (!menu) return;
    
    // Position menu
    const rect = document.documentElement.getBoundingClientRect();
    menu.style.left = Math.min(x, rect.width - 200) + 'px';
    menu.style.top = Math.min(y, rect.height - 250) + 'px';
    menu.classList.remove('hidden');
}

// Handle table context menu action
function handleTableContextMenuAction(e) {
    const action = e.target.dataset.action;
    if (!action || !richTextEditor) return;
    
    switch (action) {
        case 'addRowBefore':
            richTextEditor.addTableRow('before');
            break;
        case 'addRowAfter':
            richTextEditor.addTableRow('after');
            break;
        case 'addColumnBefore':
            richTextEditor.addTableColumn('before');
            break;
        case 'addColumnAfter':
            richTextEditor.addTableColumn('after');
            break;
        case 'deleteRow':
            richTextEditor.deleteTableRow();
            break;
        case 'deleteColumn':
            richTextEditor.deleteTableColumn();
            break;
        case 'toggleHeader':
            richTextEditor.toggleTableHeader();
            break;
        case 'deleteTable':
            if (confirm('确定要删除此表格吗？')) {
                richTextEditor.deleteTable();
            }
            break;
    }
    
    // Hide menu
    document.getElementById('tableContextMenu').classList.add('hidden');
}

// ========== Editor Functions ==========

// Initialize Rich Text Editor
function initRichTextEditor() {
    if (richTextEditor) {
        richTextEditor.destroy();
    }
    
    // Initialize Turndown first
    initTurndown();
    
    richTextEditor = new RichTextEditor({
        element: document.getElementById('editor'),
        onChange: (html) => {
            // Sync HTML to Markdown textarea when editor content changes
            if (currentTab === 'edit' && turndownService) {
                const markdown = turndownService.turndown(html);
                elements.markdownContent.value = markdown;
            }
        },
        onImageUpload: async (file) => {
            return await uploadImage(file);
        },
        onAttachmentUpload: async (file) => {
            return await uploadAttachment(file);
        }
    });
    
    isEditorReady = true;
    
    // Setup table context menu
    setupTableContextMenu();
}

// Upload image
async function uploadImage(file) {
    try {
        const result = await api.uploadFile('/api/upload/image', file);
        return result.url;
    } catch (error) {
        console.error('Image upload error:', error);
        throw new Error('图片上传失败: ' + error.message);
    }
}

// Upload attachment
async function uploadAttachment(file) {
    try {
        const result = await api.uploadFile('/api/upload/attachment', file);
        currentAttachments.push(result);
        return result;
    } catch (error) {
        console.error('Attachment upload error:', error);
        throw new Error('附件上传失败: ' + error.message);
    }
}

// Get current content (Markdown)
function getCurrentContent() {
    if (currentTab === 'markdown') {
        // If in markdown tab, return textarea content
        return elements.markdownContent.value;
    } else {
        // Otherwise, convert editor HTML to markdown
        if (richTextEditor && turndownService) {
            const html = richTextEditor.getHTML();
            return turndownService.turndown(html);
        }
        return elements.markdownContent.value;
    }
}

// Set content to editor
function setEditorContent(markdown) {
    elements.markdownContent.value = markdown;
    
    if (richTextEditor) {
        // Convert markdown to HTML using marked, then set to editor
        const html = marked.parse(markdown);
        richTextEditor.setHTML(html);
    }
}

// Switch tab
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content visibility
    elements.editTab.classList.toggle('active', tabName === 'edit');
    elements.previewTab.classList.toggle('active', tabName === 'preview');
    elements.markdownTab.classList.toggle('active', tabName === 'markdown');
    
    // Handle content sync between tabs
    if (tabName === 'preview') {
        updatePreview();
    } else if (tabName === 'markdown') {
        // Sync from editor to textarea
        if (richTextEditor && turndownService) {
            const html = richTextEditor.getHTML();
            elements.markdownContent.value = turndownService.turndown(html);
        }
    } else if (tabName === 'edit') {
        // Sync from textarea to editor
        if (richTextEditor && elements.markdownContent.value) {
            const html = marked.parse(elements.markdownContent.value);
            richTextEditor.setHTML(html);
        }
    }
}

// Update markdown preview
function updatePreview() {
    const content = getCurrentContent();
    
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

// ========== Collaboration Functions ==========

// Open collaboration modal
function openCollaborationModal() {
    if (!currentNote) {
        showToast('请先保存笔记', 'error');
        return;
    }
    
    // Load collaborators
    loadCollaborators();
    
    // Connect to collaboration WebSocket
    if (window.collaborationManager) {
        window.collaborationManager.connect(currentNote.id);
    }
    
    toggleModal(elements.collaborationModal, true);
}

// Load collaborators for current note
async function loadCollaborators() {
    if (!currentNote) return;
    
    try {
        const result = await api.get(`/api/notes/${currentNote.id}/collaborators`);
        if (window.collaboratorsManager) {
            window.collaboratorsManager.collaborators = result.collaborators;
            window.collaboratorsManager.currentNoteId = currentNote.id;
            window.collaboratorsManager.renderCollaboratorsList();
        }
    } catch (error) {
        console.error('Failed to load collaborators:', error);
        showToast('加载协作者失败', 'error');
    }
}

// Add collaborator
async function addCollaborator() {
    const username = elements.collaboratorUsername.value.trim();
    const permission = elements.collaboratorPermission.value;
    
    if (!username) {
        showToast('请输入用户名', 'error');
        return;
    }
    
    try {
        if (window.collaboratorsManager) {
            await window.collaboratorsManager.addCollaborator(username, permission);
            elements.collaboratorUsername.value = '';
            await loadCollaborators();
        }
    } catch (error) {
        console.error('Error adding collaborator:', error);
    }
}

// Open versions modal
async function openVersionsModal() {
    if (!currentNote) {
        showToast('请先保存笔记', 'error');
        return;
    }
    
    toggleModal(elements.versionsModal, true);
    
    try {
        if (window.versionHistoryManager) {
            await window.versionHistoryManager.loadVersions(currentNote.id);
            window.versionHistoryManager.renderVersionsList();
        }
    } catch (error) {
        console.error('Failed to load versions:', error);
        showToast('加载版本历史失败', 'error');
    }
}

// Open note for editing
async function openNote(id) {
    try {
        // Disable auto-save for previous note
        if (richTextEditor) {
            richTextEditor.disableAutoSave();
        }
        
        currentNote = await api.get(`/api/notes/${id}`);
        
        elements.noteTitle.value = currentNote.title;
        
        // Check for auto-saved data
        if (richTextEditor && richTextEditor.hasAutoSavedData(currentNote.id)) {
            const autoSaveData = richTextEditor.getAutoSavedData(currentNote.id);
            const savedTime = new Date(autoSaveData.timestamp).toLocaleString('zh-CN');
            
            if (confirm(`检测到未保存的编辑内容（${savedTime}）\n是否恢复？`)) {
                richTextEditor.restoreFromAutoSave(currentNote.id);
            } else {
                // Set content from server
                setEditorContent(currentNote.content);
                richTextEditor.clearAutoSave(currentNote.id);
            }
        } else {
            // Set content to editor
            setEditorContent(currentNote.content);
        }
        
        // Enable auto-save for this note
        if (richTextEditor) {
            richTextEditor.enableAutoSave(currentNote.id);
        }
        
        // Load attachments
        await renderAttachmentList();
        
        renderNoteMeta();
        
        // Show AI actions if available
        elements.aiActions.style.display = isAiAvailable ? 'flex' : 'none';
        elements.aiEnhanceBtn.style.display = isAiAvailable ? 'inline-block' : 'none';
        
        // Show share button
        elements.shareBtn.style.display = 'inline-block';
        
        // Reset to edit tab
        switchTab('edit');
        
        showView('edit');
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
    // Disable auto-save for previous note
    if (richTextEditor) {
        richTextEditor.disableAutoSave();
    }
    
    currentNote = null;
    currentAttachments = [];
    elements.noteTitle.value = '';
    elements.markdownContent.value = '';
    
    // Clear editor
    if (richTextEditor) {
        richTextEditor.setHTML('');
    }
    
    // Clear attachment list
    await renderAttachmentList();
    
    elements.noteTags.innerHTML = '';
    elements.noteSummary.innerHTML = '';
    elements.noteDates.innerHTML = '';
    elements.aiActions.style.display = isAiAvailable ? 'flex' : 'none';
    elements.aiEnhanceBtn.style.display = isAiAvailable ? 'inline-block' : 'none';
    
    // Hide share button for new notes
    elements.shareBtn.style.display = 'none';
    
    // Reset to edit tab
    switchTab('edit');
    
    showView('edit');
    elements.noteTitle.focus();
}

// Save note
async function saveNote() {
    const title = elements.noteTitle.value.trim();
    const content = getCurrentContent().trim();
    
    if (!title) {
        showToast('请输入标题', 'error');
        return;
    }
    
    try {
        if (currentNote) {
            // Update existing
            const result = await api.put(`/api/notes/${currentNote.id}`, { title, content });
            currentNote = result;
            
            // Update attachment associations
            await updateNoteAttachments(currentNote.id);
            
            // Clear auto-save data
            if (richTextEditor) {
                richTextEditor.clearAutoSave(currentNote.id);
            }
            
            showToast('笔记已更新');
        } else {
            // Create new
            const result = await api.post('/api/notes', { title, content });
            currentNote = result;
            
            // Update attachment associations
            await updateNoteAttachments(currentNote.id);
            
            // Enable auto-save for the new note
            if (richTextEditor) {
                richTextEditor.enableAutoSave(currentNote.id);
            }
            
            showToast('笔记已创建');
            
            // Show share button after creation
            elements.shareBtn.style.display = 'inline-block';
        }
        
        // Reload notes
        await loadNotes();
        renderNoteMeta();
        await renderAttachmentList();
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
}

// Update attachment associations for current note
async function updateNoteAttachments(noteId) {
    if (!currentAttachments || currentAttachments.length === 0) return;
    
    try {
        const attachmentIds = currentAttachments.map(att => att.id);
        await api.put(`/api/notes/${noteId}/attachments`, attachmentIds);
    } catch (error) {
        console.error('Failed to update attachments:', error);
    }
}

// Render attachment list
async function renderAttachmentList() {
    const container = document.getElementById('attachmentList');
    if (!container) return;
    
    if (!currentNote || !currentAttachments || currentAttachments.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    // Fetch attachments from server
    try {
        const result = await api.get(`/api/notes/${currentNote.id}/attachments`);
        currentAttachments = result.attachments || [];
    } catch (error) {
        console.error('Failed to load attachments:', error);
    }
    
    if (currentAttachments.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <div class="attachment-section">
            <h4>📎 附件 (${currentAttachments.length})</h4>
            <div class="attachment-items">
                ${currentAttachments.map(att => `
                    <div class="attachment-item" data-id="${att.id}">
                        <span class="attachment-icon">${getFileIcon(att.original_filename || att.filename)}</span>
                        <a href="${att.url}" target="_blank" class="attachment-name">${escapeHtml(att.original_filename || att.filename)}</a>
                        <span class="attachment-size">${formatFileSize(att.file_size)}</span>
                        <button class="attachment-remove" data-id="${att.id}" title="删除">×</button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Add remove handlers
    container.querySelectorAll('.attachment-remove').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = parseInt(btn.dataset.id);
            if (confirm('确定要删除这个附件吗？')) {
                try {
                    await api.delete(`/api/attachments/${id}`);
                    currentAttachments = currentAttachments.filter(a => a.id !== id);
                    renderAttachmentList();
                    showToast('附件已删除');
                } catch (error) {
                    showToast('删除附件失败: ' + error.message, 'error');
                }
            }
        });
    });
}

// Get file icon based on extension
function getFileIcon(filename) {
    const ext = (filename || '').split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄',
        'doc': '📝', 'docx': '📝',
        'xls': '📊', 'xlsx': '📊',
        'ppt': '📈', 'pptx': '📈',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'webp': '🖼️', 'svg': '🖼️',
        'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
        'mp3': '🎵', 'wav': '🎵',
        'zip': '📦', 'rar': '📦', '7z': '📦',
        'txt': '📃', 'md': '📃',
        'json': '⚙️', 'js': '⚙️', 'py': '⚙️', 'html': '⚙️', 'css': '⚙️'
    };
    return icons[ext] || '📎';
}

// Format file size
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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

// Load collaborated notes
async function loadCollaboratedNotes() {
    try {
        const result = await api.get('/api/collaborated-notes');
        collaboratedNotes = result;
        renderCollaboratedNotes();
    } catch (error) {
        console.error('Failed to load collaborated notes:', error);
    }
}

// Render collaborated notes in sidebar
function renderCollaboratedNotes() {
    // Check if section exists, if not create it
    let section = document.getElementById('collaboratedSection');
    if (!section) {
        section = document.createElement('div');
        section.id = 'collaboratedSection';
        section.className = 'collaborated-section';
        
        // Insert before stats section
        const statsSection = document.querySelector('.stats-section-sidebar');
        if (statsSection) {
            statsSection.parentNode.insertBefore(section, statsSection);
        } else {
            document.querySelector('.sidebar').appendChild(section);
        }
    }
    
    if (collaboratedNotes.length === 0) {
        section.innerHTML = '';
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    section.innerHTML = `
        <h3>👥 协作笔记 <span class="collaborated-count">(${collaboratedNotes.length})</span></h3>
        <div class="collaborated-list">
            ${collaboratedNotes.map(note => `
                <div class="collaborated-item" data-id="${note.id}">
                    <span class="collaborated-title">${escapeHtml(note.title)}</span>
                </div>
            `).join('')}
        </div>
    `;
    
    // Add click handlers
    section.querySelectorAll('.collaborated-item').forEach(item => {
        item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            openNote(id);
        });
    });
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
    const content = getCurrentContent().trim();
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
            setEditorContent(result.enhanced);
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
            <div class="share-item ${isExpired ? 'expired' : ''}" data-token="${share.token}">
                <div class="share-item-info">
                    <div class="share-item-permission">${permissionText}</div>
                    <div class="share-item-meta">
                        访问次数: ${share.access_count} | 过期: ${expiresText} ${isExpired ? '(已过期)' : ''}
                    </div>
                </div>
                <div class="share-item-actions">
                    <button class="btn-icon share-copy-btn" data-token="${share.token}" title="复制链接">📋</button>
                    <button class="btn-icon share-delete-btn" data-token="${share.token}" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
    
    // Add event handlers
    document.querySelectorAll('.share-copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const token = btn.dataset.token;
            const shareUrl = `${window.location.origin}/s/${token}`;
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast('链接已复制');
            });
        });
    });
    
    document.querySelectorAll('.share-delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const token = btn.dataset.token;
            if (confirm('确定要删除这个分享链接吗？')) {
                try {
                    await api.delete(`/api/shares/${token}`);
                    showToast('分享链接已删除');
                    loadNoteShares();
                } catch (error) {
                    showToast('删除失败: ' + error.message, 'error');
                }
            }
        });
    });
}

// Create share
async function createShare() {
    if (!currentNote) return;
    
    const permission = elements.sharePermission.value;
    const password = elements.sharePassword.value;
    const expiresDays = elements.shareExpires.value ? parseInt(elements.shareExpires.value) : null;
    
    if (permission === 'password' && !password) {
        showToast('请设置访问密码', 'error');
        return;
    }
    
    elements.createShareBtn.innerHTML = '<span class="spinner"></span>';
    elements.createShareBtn.disabled = true;
    
    try {
        const result = await api.post('/api/shares', {
            note_id: currentNote.id,
            permission: permission,
            password: password || null,
            expires_days: expiresDays
        });
        
        // Show result
        elements.shareUrlInput.value = result.share_url;
        elements.shareInfoPermission.textContent = {
            'public': '🔓 公开 - 任何人都可以访问',
            'password': '🔐 密码保护 - 需要密码才能访问',
            'private': '🔒 私密 - 仅自己可见'
        }[result.permission];
        elements.shareInfoExpires.textContent = result.expires_at 
            ? new Date(result.expires_at).toLocaleString('zh-CN')
            : '永不过期';
        
        elements.createShareForm.classList.add('hidden');
        elements.shareResult.classList.remove('hidden');
        
        // Refresh shares list
        loadNoteShares();
        
        showToast('分享链接创建成功');
    } catch (error) {
        showToast('创建分享失败: ' + error.message, 'error');
    } finally {
        elements.createShareBtn.innerHTML = '创建分享';
        elements.createShareBtn.disabled = false;
    }
}

// ========== Stats Functions ==========

// Open stats modal
async function openStatsModal() {
    toggleModal(elements.statsModal, true);
    
    try {
        const stats = await api.get('/api/stats/detailed');
        
        // Update stats display
        document.getElementById('statTotalNotes').textContent = stats.total_notes;
        document.getElementById('statTotalWords').textContent = stats.total_words.toLocaleString();
        document.getElementById('statTotalChars').textContent = stats.total_characters.toLocaleString();
        document.getElementById('statCurrentStreak').textContent = stats.current_streak;
        document.getElementById('statWeekNotes').textContent = stats.notes_this_week;
        document.getElementById('statMonthNotes').textContent = stats.notes_this_month;
        document.getElementById('statAvgWords').textContent = stats.avg_words_per_note;
        document.getElementById('statAvgChars').textContent = stats.avg_characters_per_note;
        
        // Render charts
        renderHourlyChart(stats.hourly_distribution);
        renderWeekdayChart(stats.weekday_distribution);
        renderActivityChart(stats.activity_by_date);
    } catch (error) {
        console.error('Failed to load stats:', error);
        showToast('加载统计数据失败', 'error');
    }
}

// Render hourly distribution chart
function renderHourlyChart(data) {
    const chart = document.getElementById('hourlyChart');
    const maxCount = Math.max(...data.map(d => d.count));
    
    chart.innerHTML = `
        <div class="bar-chart">
            ${data.map(d => `
                <div class="bar-item" title="${d.hour}:00 - ${d.count} 篇">
                    <div class="bar" style="height: ${maxCount > 0 ? (d.count / maxCount * 100) : 0}%"></div>
                    <div class="bar-label">${d.hour}</div>
                </div>
            `).join('')}
        </div>
    `;
}

// Render weekday distribution chart
function renderWeekdayChart(data) {
    const chart = document.getElementById('weekdayChart');
    const maxCount = Math.max(...data.map(d => d.count));
    
    chart.innerHTML = `
        <div class="bar-chart horizontal">
            ${data.map(d => `
                <div class="bar-row">
                    <div class="bar-label">${d.day}</div>
                    <div class="bar-wrapper">
                        <div class="bar" style="width: ${maxCount > 0 ? (d.count / maxCount * 100) : 0}%"></div>
                    </div>
                    <div class="bar-value">${d.count}</div>
                </div>
            `).join('')}
        </div>
    `;
}

// Render activity chart
function renderActivityChart(data) {
    const chart = document.getElementById('activityChart');
    const maxCount = Math.max(...data.map(d => d.notes_created));
    
    chart.innerHTML = `
        <div class="activity-bars">
            ${data.map(d => {
                const date = new Date(d.date);
                const dayLabel = `${date.getMonth() + 1}/${date.getDate()}`;
                return `
                    <div class="activity-item" title="${d.date}: ${d.notes_created} 篇笔记, ${d.characters_written} 字符">
                        <div class="activity-bar ${d.notes_created > 0 ? 'has-activity' : ''}" 
                             style="height: ${maxCount > 0 && d.notes_created > 0 ? Math.max(20, d.notes_created / maxCount * 100) : 4}px">
                        </div>
                        <div class="activity-label">${dayLabel}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// ========== Toolbar Handlers ==========

// Handle toolbar button clicks for table
function handleInsertTable() {
    const rows = parseInt(document.getElementById('tableRows').value) || 3;
    const cols = parseInt(document.getElementById('tableCols').value) || 3;
    const withHeader = document.getElementById('tableHeader').checked;
    
    if (richTextEditor && richTextEditor.editor) {
        richTextEditor.editor.chain().focus().insertTable({ rows, cols, withHeaderRow: withHeader }).run();
    }
    
    toggleModal(elements.tableInsertModal, false);
}

// Handle link insert
function handleInsertLink() {
    const url = document.getElementById('linkUrl').value.trim();
    const text = document.getElementById('linkText').value.trim();
    
    if (!url) {
        showToast('请输入链接地址', 'error');
        return;
    }
    
    if (richTextEditor && richTextEditor.editor) {
        const { editor } = richTextEditor;
        
        if (text) {
            // Insert link with custom text
            editor.chain().focus().insertContent({
                type: 'text',
                text: text,
                marks: [{
                    type: 'link',
                    attrs: { href: url }
                }]
            }).run();
        } else {
            // Set link on selection or insert with URL as text
            editor.chain().focus().setLink({ href: url }).run();
        }
    }
    
    toggleModal(elements.linkInsertModal, false);
    document.getElementById('linkUrl').value = '';
    document.getElementById('linkText').value = '';
}

// Handle image insert
async function handleInsertImage() {
    const activeTab = document.querySelector('.upload-tab-btn.active');
    const tabName = activeTab ? activeTab.dataset.tab : 'upload';
    
    if (tabName === 'upload') {
        const fileInput = document.getElementById('imageFile');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            try {
                showToast('正在上传图片...');
                const url = await uploadImage(file);
                
                if (richTextEditor && richTextEditor.editor) {
                    richTextEditor.editor.chain().focus().setImage({ src: url, alt: file.name }).run();
                }
                
                showToast('图片插入成功');
                toggleModal(elements.imageUploadModal, false);
                fileInput.value = '';
            } catch (error) {
                showToast('图片上传失败: ' + error.message, 'error');
            }
        } else {
            showToast('请选择图片文件', 'error');
        }
    } else {
        const url = document.getElementById('imageUrl').value.trim();
        if (url) {
            if (richTextEditor && richTextEditor.editor) {
                richTextEditor.editor.chain().focus().setImage({ src: url }).run();
            }
            toggleModal(elements.imageUploadModal, false);
            document.getElementById('imageUrl').value = '';
        } else {
            showToast('请输入图片链接', 'error');
        }
    }
}

// Handle attachment upload
async function handleUploadAttachment() {
    const fileInput = document.getElementById('attachmentFile');
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        try {
            showToast('正在上传附件...');
            const result = await uploadAttachment(file);
            
            // Insert attachment link in editor
            if (richTextEditor && richTextEditor.editor) {
                richTextEditor.editor.chain().focus().insertContent({
                    type: 'paragraph',
                    content: [{
                        type: 'text',
                        text: `📎 ${result.original_filename}`,
                        marks: [{
                            type: 'link',
                            attrs: { 
                                href: result.url,
                                'data-attachment': 'true'
                            }
                        }]
                    }]
                }).run();
            }
            
            showToast('附件上传成功');
            toggleModal(elements.attachmentUploadModal, false);
            fileInput.value = '';
        } catch (error) {
            showToast('附件上传失败: ' + error.message, 'error');
        }
    } else {
        showToast('请选择附件文件', 'error');
    }
}

// Handle Markdown export
function handleMarkdownExport() {
    const content = getCurrentContent();
    const title = elements.noteTitle.value || '未命名笔记';
    
    const blob = new Blob([`# ${title}\n\n${content}`], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/[^\w\u4e00-\u9fa5]/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Markdown 导出成功');
}

// Handle Markdown import
function handleMarkdownImport() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.md,.markdown,.txt';
    
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                
                // Try to extract title from first heading
                const titleMatch = content.match(/^#\s+(.+)$/m);
                if (titleMatch && !elements.noteTitle.value) {
                    elements.noteTitle.value = titleMatch[1].trim();
                }
                
                // Set content
                setEditorContent(content);
                showToast('Markdown 导入成功');
            };
            reader.readAsText(file);
        }
    };
    
    input.click();
}

// ========== Event Listeners ==========

// Main buttons
elements.newNoteBtn.addEventListener('click', createNewNote);
elements.backBtn.addEventListener('click', () => showView('list'));
elements.saveBtn.addEventListener('click', saveNote);
elements.deleteBtn.addEventListener('click', deleteNote);

// Search and filter
elements.searchInput.addEventListener('input', filterNotes);
elements.sortSelect.addEventListener('change', filterNotes);

// Tab switching
elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        switchTab(btn.dataset.tab);
    });
});

// AI actions
elements.generateSummaryBtn.addEventListener('click', generateSummary);
elements.generateTagsBtn.addEventListener('click', generateTags);

// Smart search
elements.smartSearchBtn.addEventListener('click', () => {
    elements.smartSearchInput.value = '';
    toggleModal(elements.smartSearchModal, true);
});

elements.closeSearchBtn.addEventListener('click', () => showView('list'));

elements.doSmartSearch.addEventListener('click', performSmartSearch);
elements.smartSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSmartSearch();
});

// Preview button
elements.previewBtn.addEventListener('click', () => {
    switchTab('preview');
});

// AI enhance
elements.aiEnhanceBtn.addEventListener('click', () => {
    elements.enhanceResult.classList.remove('show');
    toggleModal(elements.aiEnhanceModal, true);
});

elements.doEnhance.addEventListener('click', enhanceText);

// Modal close buttons
elements.modalCloseBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const modal = btn.closest('.modal');
        if (modal) toggleModal(modal, false);
    });
});

// Export
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

// Share
elements.shareBtn.addEventListener('click', openShareModal);
elements.sharePermission.addEventListener('change', () => {
    elements.passwordGroup.style.display = 
        elements.sharePermission.value === 'password' ? 'block' : 'none';
});
elements.createShareBtn.addEventListener('click', createShare);
elements.copyShareUrlBtn.addEventListener('click', () => {
    elements.shareUrlInput.select();
    document.execCommand('copy');
    showToast('链接已复制');
});
elements.createNewShareBtn.addEventListener('click', () => {
    elements.createShareForm.classList.remove('hidden');
    elements.shareResult.classList.add('hidden');
});
elements.closeShareBtn.addEventListener('click', () => {
    toggleModal(elements.shareModal, false);
});

// Stats
elements.statsBtn.addEventListener('click', openStatsModal);

// Collaboration
elements.collaborationBtn.addEventListener('click', openCollaborationModal);
elements.versionsBtn.addEventListener('click', openVersionsModal);
elements.addCollaboratorBtn.addEventListener('click', addCollaborator);

// Toolbar buttons for table, link, image, attachment
document.getElementById('insertTableBtn')?.addEventListener('click', handleInsertTable);
document.getElementById('insertLinkBtn')?.addEventListener('click', handleInsertLink);
document.getElementById('insertImageBtn')?.addEventListener('click', handleInsertImage);
document.getElementById('uploadAttachmentBtn')?.addEventListener('click', handleUploadAttachment);

// Markdown import/export
document.getElementById('mdExportBtn')?.addEventListener('click', handleMarkdownExport);
document.getElementById('mdImportBtn')?.addEventListener('click', handleMarkdownImport);

// Upload tabs
document.querySelectorAll('.upload-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.upload-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.upload-tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tab + 'Tab');
        });
    });
});

// Logout button
document.getElementById('logoutBtn').addEventListener('click', async () => {
    try {
        await api.post('/api/auth/logout', {});
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/login';
    }
});

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
        const openModal = document.querySelector('.modal:not(.hidden)');
        if (openModal) {
            toggleModal(openModal, false);
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
    await loadCollaboratedNotes();
    
    // Initialize rich text editor
    initRichTextEditor();
}

// Start the app
init();

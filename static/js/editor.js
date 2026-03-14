/**
 * TipTap Rich Text Editor Integration for AI Notes
 * Supports: formatting, images, attachments, undo/redo, tables, task lists
 * Version: 2.0
 */

class RichTextEditor {
    constructor(options = {}) {
        this.element = options.element || document.getElementById('editor');
        this.onChange = options.onChange || (() => {});
        this.onImageUpload = options.onImageUpload || null;
        this.onAttachmentUpload = options.onAttachmentUpload || null;
        this.editor = null;
        this.attachments = [];
        this.historyStack = [];
        this.historyIndex = -1;
        this.maxHistorySize = 100;
        this.isInitialized = false;
        
        this.init();
    }

    init() {
        if (!this.element) {
            console.warn('Editor element not found');
            return;
        }

        // Check if all required TipTap extensions are available (from CDN)
        const requiredLibs = [
            'tiptap', 'tiptapStarterKit', 'tiptapImage', 'tiptapTable',
            'tiptapTableRow', 'tiptapTableCell', 'tiptapTableHeader',
            'tiptapLink', 'tiptapTaskList', 'tiptapTaskItem', 
            'tiptapHighlight', 'tiptapTypography', 'tiptapHorizontalRule',
            'tiptapPlaceholder'
        ];
        
        const missingLibs = requiredLibs.filter(lib => typeof window[lib] === 'undefined');
        
        if (missingLibs.length > 0) {
            console.warn(`TipTap libraries not fully loaded yet (missing: ${missingLibs.join(', ')}), will retry...`);
            setTimeout(() => this.init(), 200);
            return;
        }

        this.setupExtensions();
    }

    setupExtensions() {
        const { Editor } = window.tiptap;
        const { StarterKit } = window.tiptapStarterKit;
        const { Image } = window.tiptapImage;
        const { Table } = window.tiptapTable;
        const { TableRow } = window.tiptapTableRow;
        const { TableCell } = window.tiptapTableCell;
        const { TableHeader } = window.tiptapTableHeader;
        const { Link } = window.tiptapLink;
        const { TaskList } = window.tiptapTaskList;
        const { TaskItem } = window.tiptapTaskItem;
        const { Highlight } = window.tiptapHighlight;
        const { Typography } = window.tiptapTypography;
        const { HorizontalRule } = window.tiptapHorizontalRule;
        const { Placeholder } = window.tiptapPlaceholder;

        try {
            this.editor = new Editor({
                element: this.element,
                extensions: [
                    StarterKit.configure({
                        heading: {
                            levels: [1, 2, 3, 4, 5, 6]
                        },
                        bulletList: {},
                        orderedList: {},
                        listItem: {},
                        blockquote: {},
                        codeBlock: {},
                        code: {},
                        bold: {},
                        italic: {},
                        strike: {},
                        dropcursor: false,
                        gapcursor: false,
                        history: {
                            depth: 100,
                            newGroupDelay: 500
                        }
                    }),
                    Placeholder.configure({
                        placeholder: '开始编写笔记内容...'
                    }),
                    Image.configure({
                        inline: false,
                        allowBase64: true,
                        HTMLAttributes: {
                            class: 'editor-image'
                        }
                    }),
                    Link.configure({
                        openOnClick: false,
                        HTMLAttributes: {
                            rel: 'noopener noreferrer',
                            target: '_blank'
                        }
                    }),
                    Table.configure({
                        resizable: true,
                        HTMLAttributes: {
                            class: 'editor-table'
                        }
                    }),
                    TableRow,
                    TableHeader,
                    TableCell,
                    TaskList,
                    TaskItem.configure({
                        nested: true
                    }),
                    Highlight,
                    Typography,
                    HorizontalRule
                ],
                content: '',
                onUpdate: ({ editor }) => {
                    const html = editor.getHTML();
                    this.onChange(html);
                    this.updateToolbarState();
                    this.saveToHistory(html);
                    this.updateStats();
                },
                onSelectionUpdate: () => {
                    this.updateToolbarState();
                },
                onCreate: () => {
                    this.isInitialized = true;
                    console.log('TipTap editor initialized successfully');
                }
            });

            this.setupToolbarHandlers();
            this.setupKeyboardShortcuts();
            this.setupDragAndDrop();
            this.setupContextMenu();
            
        } catch (error) {
            console.error('Failed to initialize TipTap editor:', error);
        }
    }

    // Toolbar Actions
    setupToolbarHandlers() {
        document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const command = btn.dataset.command;
                this.executeCommand(command, btn);
            });
        });
    }

    executeCommand(command, btn) {
        if (!this.editor) return;

        const editor = this.editor;

        switch (command) {
            case 'undo':
                editor.commands.undo();
                break;
            case 'redo':
                editor.commands.redo();
                break;
            case 'bold':
                editor.commands.toggleBold();
                break;
            case 'italic':
                editor.commands.toggleItalic();
                break;
            case 'strike':
                editor.commands.toggleStrike();
                break;
            case 'highlight':
                editor.commands.toggleHighlight();
                break;
            case 'heading':
                this.toggleHeading();
                break;
            case 'bulletList':
                editor.commands.toggleBulletList();
                break;
            case 'orderedList':
                editor.commands.toggleOrderedList();
                break;
            case 'taskList':
                editor.commands.toggleTaskList();
                break;
            case 'code':
                editor.commands.toggleCode();
                break;
            case 'codeBlock':
                editor.commands.toggleCodeBlock();
                break;
            case 'blockquote':
                editor.commands.toggleBlockquote();
                break;
            case 'horizontalRule':
                editor.commands.setHorizontalRule();
                break;
            case 'link':
                this.promptLink();
                break;
            case 'image':
                this.promptImage();
                break;
            case 'table':
                this.showTableModal();
                break;
            case 'attachment':
                this.promptAttachment();
                break;
            default:
                console.log('Unknown command:', command);
        }

        this.updateToolbarState();
    }

    toggleHeading() {
        if (!this.editor) return;
        
        const editor = this.editor;
        const isH1 = editor.isActive('heading', { level: 1 });
        const isH2 = editor.isActive('heading', { level: 2 });
        
        if (isH1) {
            editor.commands.toggleHeading({ level: 2 });
        } else if (isH2) {
            editor.commands.setParagraph();
        } else {
            editor.commands.toggleHeading({ level: 1 });
        }
    }

    updateToolbarState() {
        if (!this.editor) return;

        const editor = this.editor;
        const isActive = (name, attrs = {}) => editor.isActive(name, attrs);

        // Update button states
        document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
            const command = btn.dataset.command;
            let active = false;

            switch (command) {
                case 'bold':
                    active = isActive('bold');
                    break;
                case 'italic':
                    active = isActive('italic');
                    break;
                case 'strike':
                    active = isActive('strike');
                    break;
                case 'highlight':
                    active = isActive('highlight');
                    break;
                case 'heading':
                    active = isActive('heading');
                    break;
                case 'bulletList':
                    active = isActive('bulletList');
                    break;
                case 'orderedList':
                    active = isActive('orderedList');
                    break;
                case 'taskList':
                    active = isActive('taskList');
                    break;
                case 'code':
                    active = isActive('code');
                    break;
                case 'codeBlock':
                    active = isActive('codeBlock');
                    break;
                case 'blockquote':
                    active = isActive('blockquote');
                    break;
            }

            btn.classList.toggle('active', active);
        });

        // Update undo/redo state
        const undoBtn = document.querySelector('.toolbar-btn[data-command="undo"]');
        const redoBtn = document.querySelector('.toolbar-btn[data-command="redo"]');
        if (undoBtn) undoBtn.disabled = !editor.can().undo();
        if (redoBtn) redoBtn.disabled = !editor.can().redo();
    }

    // Link handling
    promptLink() {
        if (!this.editor) return;

        const previousUrl = this.editor.getAttributes('link').href;
        const url = window.prompt('输入链接 URL:', previousUrl || 'https://');

        if (url === null) return;

        if (url === '') {
            this.editor.chain().focus().unsetLink().run();
        } else {
            this.editor.chain().focus().setLink({ href: url }).run();
        }
    }

    showTableModal() {
        // Show table insert modal
        const modal = document.getElementById('tableInsertModal');
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            // Fallback: insert default table
            this.insertTable(3, 3, true);
        }
    }

    // Image handling
    promptImage() {
        const modal = document.getElementById('imageUploadModal');
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            // Fallback: direct file select
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    await this.insertImage(file);
                }
            };
            input.click();
        }
    }

    async insertImage(file) {
        if (!this.editor) return;

        // Show uploading indicator
        const loadingPos = this.editor.state.selection.head;
        this.editor.chain().focus().insertContent({
            type: 'paragraph',
            content: [{ type: 'text', text: '⏳ 正在上传图片...' }]
        }).run();

        try {
            if (this.onImageUpload) {
                const imageUrl = await this.onImageUpload(file);
                // Replace loading text with image
                this.editor.commands.undo();
                this.editor.chain().focus().setImage({ src: imageUrl, alt: file.name }).run();
                
                // Show success notification if showToast is available
                if (typeof showToast === 'function') {
                    showToast('图片上传成功');
                }
            } else {
                // Fallback to base64
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.editor.commands.undo();
                    this.editor.chain().focus().setImage({ 
                        src: e.target.result, 
                        alt: file.name 
                    }).run();
                };
                reader.readAsDataURL(file);
            }
        } catch (error) {
            this.editor.commands.undo();
            if (typeof showToast === 'function') {
                showToast('图片上传失败: ' + error.message, 'error');
            }
        }
    }

    // Table handling
    insertTable(rows = 3, cols = 3, withHeaderRow = true) {
        if (!this.editor) return;
        this.editor.chain().focus().insertTable({ rows, cols, withHeaderRow }).run();
    }

    // Add table column
    addTableColumn(position = 'after') {
        if (!this.editor) return;
        if (position === 'before') {
            this.editor.chain().focus().addColumnBefore().run();
        } else {
            this.editor.chain().focus().addColumnAfter().run();
        }
    }

    // Delete table column
    deleteTableColumn() {
        if (!this.editor) return;
        this.editor.chain().focus().deleteColumn().run();
    }

    // Add table row
    addTableRow(position = 'after') {
        if (!this.editor) return;
        if (position === 'before') {
            this.editor.chain().focus().addRowBefore().run();
        } else {
            this.editor.chain().focus().addRowAfter().run();
        }
    }

    // Delete table row
    deleteTableRow() {
        if (!this.editor) return;
        this.editor.chain().focus().deleteRow().run();
    }

    // Delete entire table
    deleteTable() {
        if (!this.editor) return;
        this.editor.chain().focus().deleteTable().run();
    }

    // Toggle table header
    toggleTableHeader() {
        if (!this.editor) return;
        this.editor.chain().focus().toggleHeaderRow().run();
    }

    // Check if currently in a table
    isInTable() {
        if (!this.editor) return false;
        return this.editor.isActive('table');
    }

    // Attachment handling
    promptAttachment() {
        const modal = document.getElementById('attachmentUploadModal');
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            // Fallback: direct file select
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.onchange = async (e) => {
                const files = Array.from(e.target.files);
                for (const file of files) {
                    await this.uploadAttachment(file);
                }
            };
            input.click();
        }
    }

    async uploadAttachment(file) {
        if (!this.onAttachmentUpload) {
            if (typeof showToast === 'function') {
                showToast('附件上传功能未配置', 'error');
            }
            return;
        }

        try {
            if (typeof showToast === 'function') {
                showToast(`正在上传 ${file.name}...`);
            }
            const attachment = await this.onAttachmentUpload(file);
            this.attachments.push(attachment);
            this.insertAttachmentLink(attachment);
            if (typeof showToast === 'function') {
                showToast('附件上传成功');
            }
        } catch (error) {
            if (typeof showToast === 'function') {
                showToast('附件上传失败: ' + error.message, 'error');
            }
        }
    }

    insertAttachmentLink(attachment) {
        if (!this.editor) return;
        
        this.editor.chain().focus().insertContent({
            type: 'paragraph',
            content: [{
                type: 'text',
                text: `📎 ${attachment.original_filename || attachment.filename}`,
                marks: [{
                    type: 'link',
                    attrs: { 
                        href: attachment.url,
                        'data-attachment': 'true',
                        'data-attachment-id': attachment.id
                    }
                }]
            }]
        }).run();
    }

    renderAttachments() {
        const container = document.getElementById('attachmentList');
        if (!container) return;

        if (this.attachments.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        container.innerHTML = `
            <div class="attachment-section">
                <h4>📎 附件 (${this.attachments.length})</h4>
                <div class="attachment-items">
                    ${this.attachments.map(att => `
                        <div class="attachment-item" data-id="${att.id}">
                            <span class="attachment-icon">${this.getFileIcon(att.filename || att.original_filename)}</span>
                            <span class="attachment-name">${this.escapeHtml(att.original_filename || att.filename)}</span>
                            <span class="attachment-size">${this.formatFileSize(att.file_size || att.size)}</span>
                            <button class="attachment-remove" data-id="${att.id}" title="删除">×</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Add remove handlers
        container.querySelectorAll('.attachment-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = parseInt(btn.dataset.id);
                this.attachments = this.attachments.filter(a => a.id !== id);
                this.renderAttachments();
            });
        });
    }

    getFileIcon(filename) {
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

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Drag and drop for images and files
    setupDragAndDrop() {
        if (!this.element) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.element.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        this.element.addEventListener('dragenter', () => {
            this.element.classList.add('drag-over');
        });

        this.element.addEventListener('dragleave', (e) => {
            if (e.relatedTarget && !this.element.contains(e.relatedTarget)) {
                this.element.classList.remove('drag-over');
            }
        });

        this.element.addEventListener('drop', async (e) => {
            this.element.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files);
            const images = files.filter(f => f.type.startsWith('image/'));
            const others = files.filter(f => !f.type.startsWith('image/'));

            for (const file of images) {
                await this.insertImage(file);
            }

            for (const file of others) {
                await this.uploadAttachment(file);
            }
        });
    }

    // Context menu for table operations
    setupContextMenu() {
        // Right-click on table cells
        this.element?.addEventListener('contextmenu', (e) => {
            const cell = e.target.closest('td, th');
            if (cell && this.editor) {
                // Could show custom context menu here
                // For now, we rely on the toolbar buttons
            }
        });
    }

    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        if (!this.element) return;

        this.element.addEventListener('keydown', (e) => {
            // Custom shortcuts are mostly handled by TipTap's StarterKit
            // But we can add custom ones here if needed
            
            // Ctrl/Cmd + K for link
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.promptLink();
            }
        });
    }

    // History management for custom undo/redo (in addition to TipTap's built-in)
    saveToHistory(content) {
        // Remove any future history if we're not at the end
        if (this.historyIndex < this.historyStack.length - 1) {
            this.historyStack = this.historyStack.slice(0, this.historyIndex + 1);
        }
        
        // Add new state
        this.historyStack.push(content);
        this.historyIndex++;
        
        // Limit history size
        if (this.historyStack.length > this.maxHistorySize) {
            this.historyStack.shift();
            this.historyIndex--;
        }
    }

    customUndo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const content = this.historyStack[this.historyIndex];
            this.setHTML(content);
        }
    }

    customRedo() {
        if (this.historyIndex < this.historyStack.length - 1) {
            this.historyIndex++;
            const content = this.historyStack[this.historyIndex];
            this.setHTML(content);
        }
    }

    // Content getters/setters
    getHTML() {
        if (this.editor && typeof this.editor.getHTML === 'function') {
            try {
                return this.editor.getHTML();
            } catch (e) {
                console.error('Error getting HTML from editor:', e);
                return '';
            }
        }
        return '';
    }

    // Update word and character count display
    updateStats() {
        const wordCount = this.getWordCount();
        const charCount = this.getCharacterCount();
        
        // Dispatch custom event for stats update
        const event = new CustomEvent('editorStatsUpdate', { 
            detail: { wordCount, charCount }
        });
        document.dispatchEvent(event);
    }

    getMarkdown() {
        if (!this.editor) return '';
        
        // Convert HTML to Markdown using Turndown
        if (typeof TurndownService !== 'undefined') {
            const turndown = new TurndownService({
                headingStyle: 'atx',
                codeBlockStyle: 'fenced'
            });
            
            // Add rule for task lists
            turndown.addRule('taskList', {
                filter: function (node) {
                    return node.type === 'checkbox' && node.parentNode?.nodeName === 'LI';
                },
                replacement: function (content, node) {
                    return (node.checked ? '[x]' : '[ ]') + ' ';
                }
            });
            
            // Add rule for highlight
            turndown.addRule('highlight', {
                filter: 'mark',
                replacement: function(content) {
                    return '==' + content + '==';
                }
            });
            
            return turndown.turndown(this.editor.getHTML());
        }
        return this.editor.getHTML();
    }

    setHTML(html) {
        if (this.editor && typeof this.editor.commands?.setContent === 'function') {
            try {
                this.editor.commands.setContent(html);
                // Save initial state to history
                if (this.historyStack.length === 0) {
                    this.saveToHistory(html);
                }
            } catch (e) {
                console.error('Error setting HTML to editor:', e);
            }
        }
    }

    setMarkdown(markdown) {
        // Convert Markdown to HTML using marked, then set
        if (typeof marked !== 'undefined') {
            const html = marked.parse(markdown);
            this.setHTML(html);
        } else {
            this.setHTML(markdown);
        }
    }

    focus() {
        if (this.editor && typeof this.editor.commands?.focus === 'function') {
            try {
                this.editor.commands.focus();
            } catch (e) {
                console.error('Error focusing editor:', e);
            }
        }
    }

    destroy() {
        if (this.editor && typeof this.editor.destroy === 'function') {
            try {
                this.editor.destroy();
            } catch (e) {
                console.error('Error destroying editor:', e);
            }
        }
        this.editor = null;
        this.isInitialized = false;
    }

    // Auto-save to localStorage
    enableAutoSave(noteId, interval = 30000) {
        if (!noteId) return;
        
        this.autoSaveKey = `autosave_${noteId}`;
        this.autoSaveInterval = setInterval(() => {
            if (this.editor && this.isInitialized) {
                const content = this.getHTML();
                const title = document.getElementById('noteTitle')?.value || '';
                const data = {
                    content,
                    title,
                    timestamp: Date.now()
                };
                localStorage.setItem(this.autoSaveKey, JSON.stringify(data));
            }
        }, interval);
    }

    // Disable auto-save
    disableAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }

    // Clear auto-saved data
    clearAutoSave(noteId) {
        if (noteId) {
            localStorage.removeItem(`autosave_${noteId}`);
        } else if (this.autoSaveKey) {
            localStorage.removeItem(this.autoSaveKey);
        }
    }

    // Get auto-saved data
    getAutoSavedData(noteId) {
        const key = noteId ? `autosave_${noteId}` : this.autoSaveKey;
        if (!key) return null;
        
        const data = localStorage.getItem(key);
        if (data) {
            try {
                return JSON.parse(data);
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    // Check if there's auto-saved data
    hasAutoSavedData(noteId) {
        return this.getAutoSavedData(noteId) !== null;
    }

    // Restore from auto-save
    restoreFromAutoSave(noteId) {
        const data = this.getAutoSavedData(noteId);
        if (data && data.content) {
            this.setHTML(data.content);
            if (data.title && document.getElementById('noteTitle')) {
                document.getElementById('noteTitle').value = data.title;
            }
            return true;
        }
        return false;
    }

    // Get word count
    getWordCount() {
        if (!this.editor) return 0;
        const text = this.editor.state.doc.textContent;
        return text.split(/\s+/).filter(word => word.length > 0).length;
    }

    // Get character count
    getCharacterCount() {
        if (!this.editor) return 0;
        return this.editor.state.doc.textContent.length;
    }

    // Check if editor is ready
    isReady() {
        return this.isInitialized && this.editor !== null && typeof this.editor.getHTML === 'function';
    }

    // Get attachments
    getAttachments() {
        return this.attachments;
    }

    // Set attachments (when loading existing note)
    setAttachments(attachments) {
        this.attachments = attachments || [];
        this.renderAttachments();
    }

    // Insert content at cursor
    insertContent(content) {
        if (this.editor) {
            this.editor.chain().focus().insertContent(content).run();
        }
    }

    // Get selected text
    getSelectedText() {
        if (!this.editor) return '';
        const { from, to } = this.editor.state.selection;
        return this.editor.state.doc.textBetween(from, to);
    }

    // Replace selection with content
    replaceSelection(content) {
        if (this.editor) {
            this.editor.chain().focus().insertContent(content).run();
        }
    }
}

// Global editor instance
window.RichTextEditor = RichTextEditor;

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RichTextEditor };
}

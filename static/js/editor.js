/**
 * TipTap Rich Text Editor Integration for AI Notes
 * Supports: formatting, images, attachments, undo/redo, tables, task lists
 */

class RichTextEditor {
    constructor(options = {}) {
        this.element = options.element || document.getElementById('editor');
        this.onChange = options.onChange || (() => {});
        this.onImageUpload = options.onImageUpload || null;
        this.onAttachmentUpload = options.onAttachmentUpload || null;
        this.editor = null;
        this.attachments = [];
        this.init();
    }

    init() {
        if (!this.element || typeof tiptap === 'undefined') {
            console.warn('TipTap not available');
            return;
        }

        const { Editor } = tiptap;
        const { StarterKit } = tiptapStarterKit;
        const { Image } = tiptapImage;
        const { Table } = tiptapTable;
        const { TableRow } = tiptapTableRow;
        const { TableCell } = tiptapTableCell;
        const { TableHeader } = tiptapTableHeader;
        const { Link } = tiptapLink;
        const { TaskList } = tiptapTaskList;
        const { TaskItem } = tiptapTaskItem;
        const { Highlight } = tiptapHighlight;
        const { Typography } = tiptapTypography;
        const { HorizontalRule } = tiptapHorizontalRule;
        const { Placeholder } = tiptapPlaceholder;

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
                    gapcursor: false
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
                this.onChange(editor.getHTML());
                this.updateToolbarState();
            },
            onSelectionUpdate: () => {
                this.updateToolbarState();
            }
        });

        this.setupToolbarHandlers();
        this.setupKeyboardShortcuts();
        this.setupDragAndDrop();
    }

    // Toolbar Actions
    setupToolbarHandlers() {
        document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const command = btn.dataset.command;
                this.executeCommand(command, btn);
            });
        });
    }

    executeCommand(command, btn) {
        if (!this.editor) return;

        const editor = this.editor;
        const chain = editor.chain().focus();

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
                const level = editor.isActive('heading', { level: 1 }) ? 0 :
                              editor.isActive('heading', { level: 2 }) ? 0 : 1;
                if (level === 1) {
                    editor.commands.toggleHeading({ level: 1 });
                } else {
                    editor.commands.setParagraph();
                }
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
                this.insertTable();
                break;
            case 'attachment':
                this.promptAttachment();
                break;
            default:
                console.log('Unknown command:', command);
        }

        this.updateToolbarState();
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

    // Image handling
    promptImage() {
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

    async insertImage(file) {
        if (!this.editor) return;

        // Show uploading indicator
        const loadingId = 'upload-' + Date.now();
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
            showToast('图片上传失败: ' + error.message, 'error');
        }
    }

    // Table handling
    insertTable() {
        if (!this.editor) return;
        this.editor.chain().focus().insertTable({ rows: 3, cols: 3 }).run();
    }

    // Attachment handling
    promptAttachment() {
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

    async uploadAttachment(file) {
        if (!this.onAttachmentUpload) {
            showToast('附件上传功能未配置', 'error');
            return;
        }

        try {
            const attachment = await this.onAttachmentUpload(file);
            this.attachments.push(attachment);
            this.renderAttachments();
            showToast('附件上传成功');
        } catch (error) {
            showToast('附件上传失败: ' + error.message, 'error');
        }
    }

    renderAttachments() {
        const container = document.getElementById('attachmentList');
        if (!container) return;

        if (this.attachments.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <h4>📎 附件 (${this.attachments.length})</h4>
            ${this.attachments.map(att => `
                <div class="attachment-item" data-id="${att.id}">
                    <div class="attachment-icon">${this.getFileIcon(att.filename)}</div>
                    <div class="attachment-info">
                        <div class="attachment-name">${escapeHtml(att.filename)}</div>
                        <div class="attachment-meta">${this.formatFileSize(att.size)}</div>
                    </div>
                    <div class="attachment-actions">
                        <button class="attachment-btn" onclick="editor.downloadAttachment('${att.id}')" title="下载">⬇️</button>
                        <button class="attachment-btn delete" onclick="editor.deleteAttachment('${att.id}')" title="删除">🗑️</button>
                    </div>
                </div>
            `).join('')}
        `;
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'pdf': '📄',
            'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'ppt': '📈', 'pptx': '📈',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
            'mp3': '🎵', 'wav': '🎵',
            'zip': '📦', 'rar': '📦', '7z': '📦'
        };
        return icons[ext] || '📎';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async downloadAttachment(id) {
        const attachment = this.attachments.find(a => a.id === id);
        if (attachment && attachment.url) {
            window.open(attachment.url, '_blank');
        }
    }

    async deleteAttachment(id) {
        if (!confirm('确定要删除这个附件吗？')) return;
        this.attachments = this.attachments.filter(a => a.id !== id);
        this.renderAttachments();
    }

    // Drag and drop for images
    setupDragAndDrop() {
        if (!this.element) return;

        this.element.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.element.classList.add('drag-over');
        });

        this.element.addEventListener('dragleave', () => {
            this.element.classList.remove('drag-over');
        });

        this.element.addEventListener('drop', async (e) => {
            e.preventDefault();
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

    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        if (!this.element) return;

        this.element.addEventListener('keydown', (e) => {
            // Custom shortcuts
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'z':
                        if (e.shiftKey) {
                            e.preventDefault();
                            this.editor?.commands.redo();
                        }
                        break;
                    case 'y':
                        e.preventDefault();
                        this.editor?.commands.redo();
                        break;
                }
            }
        });
    }

    // Content getters/setters
    getHTML() {
        return this.editor ? this.editor.getHTML() : '';
    }

    getMarkdown() {
        if (!this.editor) return '';
        // Convert HTML to Markdown using Turndown
        if (typeof TurndownService !== 'undefined') {
            const turndown = new TurndownService({
                headingStyle: 'atx',
                codeBlockStyle: 'fenced'
            });
            return turndown.turndown(this.editor.getHTML());
        }
        return this.editor.getHTML();
    }

    setHTML(html) {
        if (this.editor) {
            this.editor.commands.setContent(html);
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
        this.editor?.commands.focus();
    }

    destroy() {
        this.editor?.destroy();
        this.editor = null;
    }

    // Check if editor is ready
    isReady() {
        return !!this.editor;
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
}

// Helper function for HTML escaping
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global editor instance
let editor = null;

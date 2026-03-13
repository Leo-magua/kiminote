/**
 * AI Notes - Collaboration Module
 * Handles real-time collaboration, version history, and conflict resolution
 */

class CollaborationManager {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.noteId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.activeUsers = [];
        this.userCursors = new Map();
        this.isCollaborating = false;
        this.localVersion = 0;
        this.pendingChanges = [];
        this.typingTimeout = null;
    }

    // Initialize WebSocket connection for a note
    async connect(noteId) {
        if (this.ws && this.isConnected) {
            if (this.noteId === noteId) {
                return; // Already connected to this note
            }
            this.disconnect();
        }

        this.noteId = noteId;
        
        // Get auth token from cookie
        const token = this.getCookie('session_token');
        if (!token) {
            console.error('No auth token found');
            return;
        }

        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/collaborate/${noteId}?token=${token}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupWebSocketHandlers();
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }

    setupWebSocketHandlers() {
        this.ws.onopen = () => {
            console.log('Collaboration WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.isCollaborating = true;
            this.showCollaborationStatus('已连接', 'connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onclose = () => {
            console.log('Collaboration WebSocket closed');
            this.isConnected = false;
            this.isCollaborating = false;
            this.showCollaborationStatus('已断开', 'disconnected');
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showCollaborationStatus('连接错误', 'error');
        };
    }

    handleMessage(message) {
        const { type, data, sender_session } = message;

        switch (type) {
            case 'connected':
                this.sessionId = data.session_id;
                this.localVersion = data.current_version || 0;
                break;

            case 'active_users':
                this.activeUsers = data.users || [];
                this.updateActiveUsersUI();
                break;

            case 'user_joined':
                this.handleUserJoined(data);
                break;

            case 'user_left':
                this.handleUserLeft(data);
                break;

            case 'user_typing':
                this.handleUserTyping(data);
                break;

            case 'content_change':
                if (sender_session !== this.sessionId) {
                    this.handleRemoteChange(data);
                }
                break;

            case 'cursor_update':
                if (sender_session !== this.sessionId) {
                    this.handleCursorUpdate(data);
                }
                break;

            case 'selection_update':
                if (sender_session !== this.sessionId) {
                    this.handleSelectionUpdate(data);
                }
                break;

            case 'save_requested':
                this.handleRemoteSaveRequest(data);
                break;

            case 'pong':
                // Heartbeat response
                break;
        }
    }

    // Send message to server
    send(type, data) {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify({ type, data }));
        }
    }

    // Content change operations
    sendContentChange(operation) {
        this.send('content_change', { operation });
    }

    sendCursorUpdate(position, selectionStart = null, selectionEnd = null) {
        this.send('cursor_update', {
            position,
            selection_start: selectionStart,
            selection_end: selectionEnd
        });
    }

    sendTypingStart() {
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        this.send('typing_start', {});
        this.typingTimeout = setTimeout(() => {
            this.send('typing_end', {});
        }, 3000);
    }

    // Handle remote changes
    handleRemoteChange(data) {
        const { operation, sender_name } = data;
        
        // Apply operation to editor (operational transformation)
        if (window.editor && operation) {
            this.applyRemoteOperation(operation);
            this.showRemoteChangeIndicator(sender_name);
        }
    }

    applyRemoteOperation(operation) {
        // This is a simplified implementation
        // Full OT would require more complex handling
        const { type, position, content, length } = operation;
        
        // Broadcast to editor if it has collaboration support
        if (window.editor && window.editor.chain) {
            const { state } = window.editor;
            const { doc } = state;
            
            if (type === 'insert' && content) {
                // Insert text at position
                window.editor.commands.insertContentAt(position, content);
            } else if (type === 'delete' && length) {
                // Delete text at position
                window.editor.commands.deleteRange({ from: position, to: position + length });
            }
        }
    }

    // User presence handling
    handleUserJoined(data) {
        const { user_id, username } = data;
        if (!this.activeUsers.find(u => u.user_id === user_id)) {
            this.activeUsers.push({ user_id, username });
            this.updateActiveUsersUI();
            showToast(`${username} 加入协作`, 'info');
        }
    }

    handleUserLeft(data) {
        const { user_id, username } = data;
        this.activeUsers = this.activeUsers.filter(u => u.user_id !== user_id);
        this.userCursors.delete(user_id);
        this.updateActiveUsersUI();
        this.removeUserCursor(user_id);
        showToast(`${username} 离开协作`, 'info');
    }

    handleUserTyping(data) {
        const { user_id, username, is_typing } = data;
        this.updateUserTypingStatus(user_id, username, is_typing);
    }

    // Cursor handling
    handleCursorUpdate(data) {
        const { cursor, sender_name } = data;
        const user = this.activeUsers.find(u => u.username === sender_name);
        if (user) {
            this.updateUserCursor(user.user_id, sender_name, cursor);
        }
    }

    handleSelectionUpdate(data) {
        const { selection, sender_name } = data;
        const user = this.activeUsers.find(u => u.username === sender_name);
        if (user) {
            this.updateUserSelection(user.user_id, sender_name, selection);
        }
    }

    updateUserCursor(userId, username, cursor) {
        this.userCursors.set(userId, { username, cursor });
        this.renderUserCursor(userId, username, cursor);
    }

    updateUserSelection(userId, username, selection) {
        this.userCursors.set(userId, { username, selection });
        this.renderUserSelection(userId, username, selection);
    }

    renderUserCursor(userId, username, cursor) {
        // Implementation would render a colored cursor with username
        // This depends on the editor implementation
        const cursorElement = document.getElementById(`cursor-${userId}`);
        if (cursorElement) {
            cursorElement.style.display = 'block';
        }
    }

    removeUserCursor(userId) {
        const cursorElement = document.getElementById(`cursor-${userId}`);
        if (cursorElement) {
            cursorElement.remove();
        }
    }

    renderUserSelection(userId, username, selection) {
        // Render selection highlight for remote user
    }

    // UI Updates
    updateActiveUsersUI() {
        const container = document.getElementById('activeCollaborators');
        if (!container) return;

        if (this.activeUsers.length === 0) {
            container.innerHTML = '<span class="no-collaborators">暂无协作者</span>';
            return;
        }

        container.innerHTML = this.activeUsers.map(user => `
            <div class="collaborator-item" data-user-id="${user.user_id}">
                <span class="collaborator-avatar">${user.username.charAt(0).toUpperCase()}</span>
                <span class="collaborator-name">${escapeHtml(user.username)}</span>
                <span class="collaborator-status online"></span>
            </div>
        `).join('');
    }

    updateUserTypingStatus(userId, username, isTyping) {
        const item = document.querySelector(`.collaborator-item[data-user-id="${userId}"]`);
        if (item) {
            const statusEl = item.querySelector('.collaborator-status');
            if (statusEl) {
                statusEl.className = `collaborator-status ${isTyping ? 'typing' : 'online'}`;
            }
        }
    }

    showRemoteChangeIndicator(username) {
        const indicator = document.getElementById('remoteChangeIndicator');
        if (indicator) {
            indicator.textContent = `${username} 正在编辑...`;
            indicator.classList.add('show');
            setTimeout(() => indicator.classList.remove('show'), 3000);
        }
    }

    showCollaborationStatus(status, type) {
        const indicator = document.getElementById('collaborationStatus');
        if (indicator) {
            indicator.textContent = `协作状态: ${status}`;
            indicator.className = `collaboration-status ${type}`;
        }
    }

    // Reconnection handling
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.showCollaborationStatus('重连失败', 'error');
            return;
        }

        this.reconnectAttempts++;
        this.showCollaborationStatus(`重连中 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'reconnecting');

        setTimeout(() => {
            if (this.noteId) {
                this.connect(this.noteId);
            }
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    // Disconnection
    disconnect() {
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.isCollaborating = false;
        this.sessionId = null;
        this.activeUsers = [];
        this.userCursors.clear();
    }

    // Utility functions
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    handleRemoteSaveRequest(data) {
        showToast(`${data.sender_name} 请求保存`, 'info');
        // Optionally trigger auto-save
    }
}

// Version History Manager
class VersionHistoryManager {
    constructor() {
        this.currentNoteId = null;
        this.versions = [];
    }

    async loadVersions(noteId) {
        try {
            const response = await fetch(`/api/notes/${noteId}/versions`);
            if (!response.ok) throw new Error('Failed to load versions');
            
            const data = await response.json();
            this.versions = data.versions;
            this.currentNoteId = noteId;
            return data;
        } catch (error) {
            console.error('Error loading versions:', error);
            showToast('加载版本历史失败', 'error');
            return null;
        }
    }

    renderVersionsList() {
        const container = document.getElementById('versionsList');
        if (!container) return;

        if (this.versions.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无版本历史</div>';
            return;
        }

        container.innerHTML = this.versions.map((version, index) => `
            <div class="version-item" data-version-id="${version.id}">
                <div class="version-header">
                    <span class="version-number">版本 ${version.version_number}</span>
                    <span class="version-type ${version.change_type}">${this.getChangeTypeLabel(version.change_type)}</span>
                </div>
                <div class="version-meta">
                    <span class="version-date">${formatDate(version.created_at)}</span>
                    ${version.change_summary ? `<span class="version-summary">${escapeHtml(version.change_summary)}</span>` : ''}
                </div>
                <div class="version-actions">
                    <button class="btn-text view-version" data-version-id="${version.id}">查看</button>
                    ${index > 0 ? `<button class="btn-text restore-version" data-version-id="${version.id}">恢复</button>` : ''}
                </div>
            </div>
        `).join('');

        // Add event listeners
        container.querySelectorAll('.view-version').forEach(btn => {
            btn.addEventListener('click', (e) => this.viewVersion(parseInt(e.target.dataset.versionId)));
        });

        container.querySelectorAll('.restore-version').forEach(btn => {
            btn.addEventListener('click', (e) => this.restoreVersion(parseInt(e.target.dataset.versionId)));
        });
    }

    getChangeTypeLabel(type) {
        const labels = {
            'create': '创建',
            'edit': '编辑',
            'restore': '恢复',
            'merge': '合并',
            'delete': '删除'
        };
        return labels[type] || type;
    }

    async viewVersion(versionId) {
        try {
            const response = await fetch(`/api/notes/${this.currentNoteId}/versions/${versionId}`);
            if (!response.ok) throw new Error('Failed to load version');
            
            const version = await response.json();
            this.showVersionPreview(version);
        } catch (error) {
            console.error('Error loading version:', error);
            showToast('加载版本失败', 'error');
        }
    }

    showVersionPreview(version) {
        const modal = document.getElementById('versionPreviewModal');
        const titleEl = document.getElementById('versionPreviewTitle');
        const contentEl = document.getElementById('versionPreviewContent');
        const metaEl = document.getElementById('versionPreviewMeta');

        if (titleEl) titleEl.textContent = version.title;
        if (contentEl) contentEl.innerHTML = DOMPurify.sanitize(marked.parse(version.content));
        if (metaEl) {
            metaEl.innerHTML = `
                <span>版本 ${version.version_number}</span>
                <span>类型: ${this.getChangeTypeLabel(version.change_type)}</span>
                <span>时间: ${formatDate(version.created_at)}</span>
            `;
        }

        if (modal) toggleModal(modal, true);
    }

    async restoreVersion(versionId) {
        if (!confirm('确定要恢复到这个版本吗？当前内容将被保存为新版本。')) {
            return;
        }

        try {
            const response = await fetch(`/api/notes/${this.currentNoteId}/versions/${versionId}/restore`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error('Failed to restore version');
            
            const note = await response.json();
            showToast('版本恢复成功', 'success');
            
            // Reload the note
            if (window.openNote) {
                window.openNote(note.id);
            }
            
            // Reload versions
            await this.loadVersions(this.currentNoteId);
            this.renderVersionsList();
        } catch (error) {
            console.error('Error restoring version:', error);
            showToast('恢复版本失败', 'error');
        }
    }
}

// Collaborators Manager
class CollaboratorsManager {
    constructor() {
        this.currentNoteId = null;
        this.collaborators = [];
    }

    async loadCollaborators(noteId) {
        try {
            const response = await fetch(`/api/notes/${noteId}/collaborators`);
            if (!response.ok) throw new Error('Failed to load collaborators');
            
            const data = await response.json();
            this.collaborators = data.collaborators;
            this.currentNoteId = noteId;
            return data;
        } catch (error) {
            console.error('Error loading collaborators:', error);
            showToast('加载协作者失败', 'error');
            return null;
        }
    }

    renderCollaboratorsList() {
        const container = document.getElementById('collaboratorsList');
        if (!container) return;

        if (this.collaborators.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无协作者</div>';
            return;
        }

        container.innerHTML = this.collaborators.map(collab => `
            <div class="collaborator-item" data-user-id="${collab.user_id}">
                <div class="collaborator-info">
                    <span class="collaborator-avatar">${collab.username ? collab.username.charAt(0).toUpperCase() : '?'}</span>
                    <div class="collaborator-details">
                        <span class="collaborator-name">${escapeHtml(collab.username || 'Unknown')}</span>
                        <span class="collaborator-permission ${collab.permission}">${this.getPermissionLabel(collab.permission)}</span>
                    </div>
                </div>
                <button class="btn-icon remove-collaborator" data-user-id="${collab.user_id}" title="移除协作者">×</button>
            </div>
        `).join('');

        // Add event listeners
        container.querySelectorAll('.remove-collaborator').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = parseInt(e.target.dataset.userId);
                this.removeCollaborator(userId);
            });
        });
    }

    getPermissionLabel(permission) {
        const labels = {
            'read': '只读',
            'write': '读写',
            'admin': '管理员'
        };
        return labels[permission] || permission;
    }

    async addCollaborator(username, permission = 'write') {
        try {
            const response = await fetch(`/api/notes/${this.currentNoteId}/collaborators`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, permission })
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error);
            }
            
            showToast('协作者添加成功', 'success');
            
            // Reload collaborators
            await this.loadCollaborators(this.currentNoteId);
            this.renderCollaboratorsList();
        } catch (error) {
            console.error('Error adding collaborator:', error);
            showToast('添加协作者失败: ' + error.message, 'error');
        }
    }

    async removeCollaborator(userId) {
        if (!confirm('确定要移除这个协作者吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/notes/${this.currentNoteId}/collaborators/${userId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to remove collaborator');
            
            showToast('协作者已移除', 'success');
            
            // Reload collaborators
            await this.loadCollaborators(this.currentNoteId);
            this.renderCollaboratorsList();
        } catch (error) {
            console.error('Error removing collaborator:', error);
            showToast('移除协作者失败', 'error');
        }
    }
}

// Conflict Resolution Manager
class ConflictResolutionManager {
    constructor() {
        this.currentConflict = null;
    }

    async detectConflict(noteId, baseVersion) {
        try {
            const response = await fetch(`/api/notes/${noteId}/conflict/detect?base_version=${baseVersion}`);
            if (!response.ok) throw new Error('Failed to detect conflict');
            
            return await response.json();
        } catch (error) {
            console.error('Error detecting conflict:', error);
            return { has_conflict: false };
        }
    }

    showConflictModal(conflictData, onResolve) {
        const modal = document.getElementById('conflictResolutionModal');
        if (!modal) return;

        this.currentConflict = conflictData;

        // Show conflict details
        const container = document.getElementById('conflictContent');
        if (container) {
            container.innerHTML = `
                <div class="conflict-section">
                    <h4>基础版本 (版本 ${conflictData.base_version?.version_number})</h4>
                    <div class="version-content">${escapeHtml(conflictData.base_version?.content?.substring(0, 500) || '')}...</div>
                </div>
                <div class="conflict-section">
                    <h4>当前服务器版本 (版本 ${conflictData.current_version?.version_number})</h4>
                    <div class="version-content ${conflictData.content_changed ? 'changed' : ''}">
                        ${escapeHtml(conflictData.current_version?.content?.substring(0, 500) || '')}...
                    </div>
                </div>
            `;
        }

        toggleModal(modal, true);

        // Setup resolution buttons
        const mineBtn = document.getElementById('resolveMineBtn');
        const theirsBtn = document.getElementById('resolveTheirsBtn');
        const mergeBtn = document.getElementById('resolveMergeBtn');

        if (mineBtn) {
            mineBtn.onclick = () => this.resolveConflict('mine', onResolve);
        }
        if (theirsBtn) {
            theirsBtn.onclick = () => this.resolveConflict('theirs', onResolve);
        }
        if (mergeBtn) {
            mergeBtn.onclick = () => this.showMergeEditor(onResolve);
        }
    }

    async resolveConflict(resolution, onResolve) {
        const noteId = this.currentConflict?.current_version?.note_id;
        
        try {
            const response = await fetch(`/api/notes/${noteId}/conflict/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    base_version: this.currentConflict.base_version?.version_number,
                    resolution: resolution
                })
            });

            if (!response.ok) throw new Error('Failed to resolve conflict');
            
            const result = await response.json();
            showToast('冲突已解决', 'success');
            
            // Close modal
            const modal = document.getElementById('conflictResolutionModal');
            if (modal) toggleModal(modal, false);
            
            if (onResolve) onResolve(result);
        } catch (error) {
            console.error('Error resolving conflict:', error);
            showToast('解决冲突失败', 'error');
        }
    }

    showMergeEditor(onResolve) {
        // Show a diff/merge editor for manual merging
        // This is a simplified implementation
        alert('请复制需要保留的内容，保存后重新提交。');
    }
}

// Initialize global instances
window.collaborationManager = new CollaborationManager();
window.versionHistoryManager = new VersionHistoryManager();
window.collaboratorsManager = new CollaboratorsManager();
window.conflictResolutionManager = new ConflictResolutionManager();

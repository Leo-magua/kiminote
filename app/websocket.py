"""
WebSocket handling for real-time collaboration in AI Notes
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import (
    get_db, get_note, get_user_by_id, get_user_by_username,
    create_collaboration_session, get_collaboration_session,
    update_collaboration_session, deactivate_collaboration_session,
    get_active_collaborators, create_note_version,
    check_collaborator_permission, is_note_owner_or_collaborator,
    NoteCollaborator, CollaborationSession
)
from app.auth import get_token_from_request, decode_token


class CollaborationManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        # Map: note_id -> {session_id -> WebSocket}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        
        # Map: session_id -> {user_id, note_id, username}
        self.session_info: Dict[str, dict] = {}
        
        # Map: note_id -> set of user_ids currently editing
        self.editing_users: Dict[int, Set[int]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        note_id: int,
        token: str,
        db: Session
    ) -> Optional[str]:
        """Connect a new WebSocket client"""
        # Authenticate user
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return None
        
        user_id = int(payload.get("sub", 0))
        user = get_user_by_id(db, user_id)
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return None
        
        # Check if user has access to the note
        if not is_note_owner_or_collaborator(db, note_id, user_id):
            await websocket.close(code=4003, reason="Access denied")
            return None
        
        # Accept connection
        await websocket.accept()
        
        # Create collaboration session
        session = create_collaboration_session(db, note_id, user_id)
        session_id = session.session_id
        
        # Store connection
        if note_id not in self.active_connections:
            self.active_connections[note_id] = {}
        self.active_connections[note_id][session_id] = websocket
        
        # Store session info
        self.session_info[session_id] = {
            "user_id": user_id,
            "note_id": note_id,
            "username": user.username,
            "session_id": session_id
        }
        
        # Track editing user
        if note_id not in self.editing_users:
            self.editing_users[note_id] = set()
        self.editing_users[note_id].add(user_id)
        
        return session_id
    
    async def disconnect(self, session_id: str, db: Session):
        """Disconnect a WebSocket client"""
        if session_id not in self.session_info:
            return
        
        info = self.session_info[session_id]
        note_id = info["note_id"]
        user_id = info["user_id"]
        
        # Remove from active connections
        if note_id in self.active_connections:
            self.active_connections[note_id].pop(session_id, None)
            if not self.active_connections[note_id]:
                del self.active_connections[note_id]
        
        # Remove from editing users
        if note_id in self.editing_users:
            self.editing_users[note_id].discard(user_id)
            if not self.editing_users[note_id]:
                del self.editing_users[note_id]
        
        # Deactivate session in database
        deactivate_collaboration_session(db, session_id)
        
        # Clean up session info
        del self.session_info[session_id]
        
        # Notify other users
        await self.broadcast_user_left(note_id, user_id, info["username"])
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific client"""
        if session_id not in self.session_info:
            return
        
        info = self.session_info[session_id]
        note_id = info["note_id"]
        
        if note_id in self.active_connections:
            websocket = self.active_connections[note_id].get(session_id)
            if websocket:
                await websocket.send_json(message)
    
    async def broadcast_to_note(
        self,
        note_id: int,
        message: dict,
        exclude_session: str = None
    ):
        """Broadcast a message to all connected clients for a note"""
        if note_id not in self.active_connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Send to all connected clients
        disconnected = []
        for session_id, websocket in self.active_connections[note_id].items():
            if session_id == exclude_session:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(session_id)
        
        # Clean up disconnected clients
        for session_id in disconnected:
            await self.disconnect(session_id, next(get_db()))
    
    async def broadcast_user_joined(self, note_id: int, user_id: int, username: str):
        """Broadcast that a user joined the collaboration"""
        await self.broadcast_to_note(note_id, {
            "type": "user_joined",
            "data": {
                "user_id": user_id,
                "username": username
            }
        })
    
    async def broadcast_user_left(self, note_id: int, user_id: int, username: str):
        """Broadcast that a user left the collaboration"""
        await self.broadcast_to_note(note_id, {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "username": username
            }
        })
    
    async def broadcast_content_change(
        self,
        note_id: int,
        session_id: str,
        operation: dict,
        sender_name: str
    ):
        """Broadcast content changes to other users"""
        await self.broadcast_to_note(note_id, {
            "type": "content_change",
            "data": {
                "operation": operation,
                "sender_name": sender_name
            },
            "sender_session": session_id
        }, exclude_session=session_id)
    
    async def broadcast_cursor_update(
        self,
        note_id: int,
        session_id: str,
        cursor_data: dict,
        sender_name: str
    ):
        """Broadcast cursor position updates"""
        await self.broadcast_to_note(note_id, {
            "type": "cursor_update",
            "data": {
                "cursor": cursor_data,
                "sender_name": sender_name
            },
            "sender_session": session_id
        }, exclude_session=session_id)
    
    async def broadcast_selection_update(
        self,
        note_id: int,
        session_id: str,
        selection_data: dict,
        sender_name: str
    ):
        """Broadcast text selection updates"""
        await self.broadcast_to_note(note_id, {
            "type": "selection_update",
            "data": {
                "selection": selection_data,
                "sender_name": sender_name
            },
            "sender_session": session_id
        }, exclude_session=session_id)
    
    def get_active_users(self, note_id: int) -> List[dict]:
        """Get list of active users for a note"""
        if note_id not in self.active_connections:
            return []
        
        users = []
        for session_id in self.active_connections[note_id].keys():
            if session_id in self.session_info:
                info = self.session_info[session_id]
                users.append({
                    "user_id": info["user_id"],
                    "username": info["username"],
                    "session_id": session_id
                })
        return users
    
    def is_user_editing(self, note_id: int, user_id: int) -> bool:
        """Check if a user is currently editing a note"""
        return note_id in self.editing_users and user_id in self.editing_users[note_id]


# Global collaboration manager instance
collaboration_manager = CollaborationManager()


async def handle_websocket(websocket: WebSocket, note_id: int, db: Session):
    """Main WebSocket handler for collaboration"""
    # Get token from query parameters
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    # Connect and authenticate
    session_id = await collaboration_manager.connect(websocket, note_id, token, db)
    if not session_id:
        return
    
    session_info = collaboration_manager.session_info[session_id]
    user_id = session_info["user_id"]
    username = session_info["username"]
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "data": {
                "session_id": session_id,
                "note_id": note_id,
                "user_id": user_id,
                "username": username
            }
        })
        
        # Broadcast user joined
        await collaboration_manager.broadcast_user_joined(note_id, user_id, username)
        
        # Send list of active users
        active_users = collaboration_manager.get_active_users(note_id)
        await websocket.send_json({
            "type": "active_users",
            "data": {"users": active_users}
        })
        
        # Main message loop
        while True:
            try:
                # Receive message
                message = await websocket.receive_json()
                
                # Handle different message types
                msg_type = message.get("type")
                data = message.get("data", {})
                
                if msg_type == "cursor_update":
                    # Update cursor position
                    position = data.get("position")
                    selection_start = data.get("selection_start")
                    selection_end = data.get("selection_end")
                    
                    update_collaboration_session(
                        db, session_id,
                        cursor_position=position,
                        selection_start=selection_start,
                        selection_end=selection_end
                    )
                    
                    cursor_data = {
                        "position": position,
                        "selection_start": selection_start,
                        "selection_end": selection_end
                    }
                    await collaboration_manager.broadcast_cursor_update(
                        note_id, session_id, cursor_data, username
                    )
                
                elif msg_type == "content_change":
                    # Handle content changes (operational transformation)
                    operation = data.get("operation", {})
                    
                    # Broadcast to other users
                    await collaboration_manager.broadcast_content_change(
                        note_id, session_id, operation, username
                    )
                
                elif msg_type == "selection_update":
                    # Handle selection updates
                    selection = data.get("selection", {})
                    await collaboration_manager.broadcast_selection_update(
                        note_id, session_id, selection, username
                    )
                
                elif msg_type == "save_request":
                    # Handle save request
                    content = data.get("content")
                    title = data.get("title")
                    
                    # Save will be handled by the REST API
                    # Just broadcast that a save was requested
                    await collaboration_manager.broadcast_to_note(note_id, {
                        "type": "save_requested",
                        "data": {
                            "sender_name": username,
                            "sender_id": user_id
                        }
                    })
                
                elif msg_type == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })
                
                elif msg_type == "typing_start":
                    # User started typing
                    await collaboration_manager.broadcast_to_note(note_id, {
                        "type": "user_typing",
                        "data": {
                            "user_id": user_id,
                            "username": username,
                            "is_typing": True
                        }
                    }, exclude_session=session_id)
                
                elif msg_type == "typing_end":
                    # User stopped typing
                    await collaboration_manager.broadcast_to_note(note_id, {
                        "type": "user_typing",
                        "data": {
                            "user_id": user_id,
                            "username": username,
                            "is_typing": False
                        }
                    }, exclude_session=session_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)}
                })
    
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up on disconnect
        await collaboration_manager.disconnect(session_id, db)


# Operational Transformation helper functions
def transform_operation(op1: dict, op2: dict) -> tuple:
    """
    Transform two operations to maintain consistency.
    Implements basic operational transformation for text editing.
    """
    type1 = op1.get("type")
    type2 = op2.get("type")
    pos1 = op1.get("position", 0)
    pos2 = op2.get("position", 0)
    
    # Transform insert-insert
    if type1 == "insert" and type2 == "insert":
        if pos1 < pos2 or (pos1 == pos2 and op1.get("priority", 0) > op2.get("priority", 0)):
            # op1 comes first, op2 needs to shift
            new_op2 = op2.copy()
            new_op2["position"] = pos2 + len(op1.get("content", ""))
            return op1, new_op2
        else:
            # op2 comes first, op1 needs to shift
            new_op1 = op1.copy()
            new_op1["position"] = pos1 + len(op2.get("content", ""))
            return new_op1, op2
    
    # Transform insert-delete
    if type1 == "insert" and type2 == "delete":
        if pos1 <= pos2:
            new_op2 = op2.copy()
            new_op2["position"] = pos2 + len(op1.get("content", ""))
            return op1, new_op2
        else:
            return op1, op2
    
    if type1 == "delete" and type2 == "insert":
        if pos2 <= pos1:
            new_op1 = op1.copy()
            new_op1["position"] = pos1 + len(op2.get("content", ""))
            return new_op1, op2
        else:
            return op1, op2
    
    # Transform delete-delete (more complex, simplified here)
    if type1 == "delete" and type2 == "delete":
        # If deleting same range, second delete should be no-op
        if pos1 == pos2:
            len1 = op1.get("length", 0)
            len2 = op2.get("length", 0)
            if len1 == len2:
                return {**op1, "length": 0}, {**op2, "length": 0}
            elif len1 > len2:
                return op1, {**op2, "length": 0}
            else:
                return {**op1, "length": 0}, op2
        elif pos1 < pos2:
            if pos1 + op1.get("length", 0) <= pos2:
                return op1, op2
            else:
                # Overlapping deletes
                overlap = pos1 + op1.get("length", 0) - pos2
                new_op1 = op1.copy()
                new_op1["length"] = op1.get("length", 0) - overlap
                new_op2 = op2.copy()
                new_op2["position"] = pos1 + new_op1["length"]
                return new_op1, new_op2
        else:
            # Symmetric to above
            return transform_operation(op2, op1)[::-1]
    
    return op1, op2


def apply_operation(content: str, operation: dict) -> str:
    """Apply an operation to content"""
    op_type = operation.get("type")
    position = operation.get("position", 0)
    
    if op_type == "insert":
        text = operation.get("content", "")
        return content[:position] + text + content[position:]
    
    elif op_type == "delete":
        length = operation.get("length", 0)
        return content[:position] + content[position + length:]
    
    elif op_type == "retain":
        # No change
        return content
    
    return content

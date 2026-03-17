"""
Tests for Collaboration Features
- WebSocket real-time collaboration
- Version history
- Conflict resolution
- Collaborator management
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestCollaborationAPI:
    """Test collaboration-related API endpoints"""
    
    def test_version_history_endpoints_exist(self):
        """Test that version history endpoints are registered"""
        # These should return 401 without authentication
        response = client.get("/api/notes/1/versions")
        assert response.status_code == 401
        
        response = client.get("/api/notes/1/versions/1")
        assert response.status_code == 401
        
        response = client.post("/api/notes/1/versions/1/restore")
        assert response.status_code == 401
        
        response = client.get("/api/notes/1/versions/compare")
        assert response.status_code == 401  # Requires auth, missing query params is secondary
    
    def test_collaborator_endpoints_exist(self):
        """Test that collaborator endpoints are registered"""
        response = client.get("/api/notes/1/collaborators")
        assert response.status_code == 401
        
        response = client.post("/api/notes/1/collaborators")
        assert response.status_code == 401  # Requires auth
        
        response = client.delete("/api/notes/1/collaborators/1")
        assert response.status_code == 401
        
        response = client.get("/api/notes/1/collaborators/active")
        assert response.status_code == 401
    
    def test_conflict_endpoints_exist(self):
        """Test that conflict resolution endpoints are registered"""
        response = client.post("/api/notes/1/conflict/detect")
        assert response.status_code == 401  # Requires auth
        
        response = client.post("/api/notes/1/conflict/resolve")
        assert response.status_code == 401  # Requires auth
    
    def test_collaborated_notes_endpoint(self):
        """Test collaborated notes endpoint"""
        response = client.get("/api/collaborated-notes")
        assert response.status_code == 401
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is registered"""
        # WebSocket endpoints can't be tested with HTTP client
        # Just verify the route exists in the app
        from app.main import app
        routes = [r for r in app.routes if hasattr(r, 'path') and '/ws/collaborate' in r.path]
        assert len(routes) >= 1, "WebSocket endpoint should be registered"


class TestCollaborationModels:
    """Test collaboration database models"""
    
    def test_note_version_model(self):
        """Test NoteVersion model exists and works"""
        from app.database import NoteVersion, create_note_version
        
        db = TestingSessionLocal()
        
        # Create a user first
        from app.database import create_user
        from app.auth import get_password_hash
        
        user = create_user(db, "testuser", get_password_hash("password"))
        
        # Create a note
        from app.database import create_note
        note = create_note(db, user.id, "Test Note", "Test content")
        
        # Create a version
        version = create_note_version(
            db,
            note_id=note.id,
            user_id=user.id,
            title=note.title,
            content=note.content,
            change_summary="Test version",
            change_type="create"
        )
        
        assert version is not None
        assert version.note_id == note.id
        assert version.version_number == 1
        
        db.close()
    
    def test_note_collaborator_model(self):
        """Test NoteCollaborator model exists and works"""
        from app.database import add_collaborator, check_collaborator_permission
        
        db = TestingSessionLocal()
        
        # Create users
        from app.database import create_user
        from app.auth import get_password_hash
        
        owner = create_user(db, "owner", get_password_hash("password"))
        collaborator = create_user(db, "collaborator", get_password_hash("password"))
        
        # Create a note
        from app.database import create_note
        note = create_note(db, owner.id, "Test Note", "Test content")
        
        # Add collaborator
        collab = add_collaborator(
            db,
            note_id=note.id,
            user_id=collaborator.id,
            permission="write",
            added_by=owner.id
        )
        
        assert collab is not None
        assert collab.permission == "write"
        
        # Check permission
        perm = check_collaborator_permission(db, note.id, collaborator.id)
        assert perm == "write"
        
        db.close()
    
    def test_collaboration_session_model(self):
        """Test CollaborationSession model exists and works"""
        from app.database import create_collaboration_session, get_collaboration_session
        
        db = TestingSessionLocal()
        
        # Create a user
        from app.database import create_user
        from app.auth import get_password_hash
        
        user = create_user(db, "sessionuser", get_password_hash("password"))
        
        # Create a note
        from app.database import create_note
        note = create_note(db, user.id, "Test Note", "Test content")
        
        # Create session
        session = create_collaboration_session(db, note.id, user.id)
        
        assert session is not None
        assert session.note_id == note.id
        assert session.user_id == user.id
        assert session.session_id is not None
        
        # Get session
        retrieved = get_collaboration_session(db, session.session_id)
        assert retrieved is not None
        assert retrieved.id == session.id
        
        db.close()


class TestCollaborationIntegration:
    """Integration tests for collaboration features"""
    
    def test_conflict_detection(self):
        """Test conflict detection function"""
        from app.database import detect_conflict, create_note_version
        
        db = TestingSessionLocal()
        
        # Create user and note
        from app.database import create_user, create_note
        from app.auth import get_password_hash
        
        user = create_user(db, "conflictuser", get_password_hash("password"))
        note = create_note(db, user.id, "Test Note", "Version 1")
        
        # Create versions
        v1 = create_note_version(db, note.id, user.id, note.title, "Version 1", change_type="create")
        note.current_version = 1
        v2 = create_note_version(db, note.id, user.id, note.title, "Version 2", change_type="edit")
        note.current_version = 2
        
        # Detect conflict (different versions)
        result = detect_conflict(db, note.id, 1, 2)
        
        assert result["has_conflict"] is True
        assert result["content_changed"] is True
        
        # No conflict (same version)
        result = detect_conflict(db, note.id, 2, 2)
        assert result["has_conflict"] is False
        
        db.close()
    
    def test_merge_changes(self):
        """Test merge changes function"""
        from app.database import merge_changes
        
        db = TestingSessionLocal()
        
        # Create user and note
        from app.database import create_user, create_note
        from app.auth import get_password_hash
        
        user = create_user(db, "mergeuser", get_password_hash("password"))
        note = create_note(db, user.id, "Original Title", "Original content")
        
        # Merge changes
        changes = {
            "title": "Merged Title",
            "content": "Merged content",
            "change_summary": "Test merge"
        }
        
        result = merge_changes(db, note.id, user.id, 1, changes)
        
        assert result is not None
        assert result.title == "Merged Title"
        assert result.content == "Merged content"
        
        db.close()


if __name__ == "__main__":
    # Run tests
    print("Running collaboration tests...")
    
    test_class = TestCollaborationAPI()
    test_class.test_version_history_endpoints_exist()
    print("✅ Version history endpoints test passed")
    
    test_class.test_collaborator_endpoints_exist()
    print("✅ Collaborator endpoints test passed")
    
    test_class.test_conflict_endpoints_exist()
    print("✅ Conflict endpoints test passed")
    
    test_class.test_collaborated_notes_endpoint()
    print("✅ Collaborated notes endpoint test passed")
    
    test_class.test_websocket_endpoint_exists()
    print("✅ WebSocket endpoint test passed")
    
    test_models = TestCollaborationModels()
    test_models.test_note_version_model()
    print("✅ NoteVersion model test passed")
    
    test_models.test_note_collaborator_model()
    print("✅ NoteCollaborator model test passed")
    
    test_models.test_collaboration_session_model()
    print("✅ CollaborationSession model test passed")
    
    test_integration = TestCollaborationIntegration()
    test_integration.test_conflict_detection()
    print("✅ Conflict detection test passed")
    
    test_integration.test_merge_changes()
    print("✅ Merge changes test passed")
    
    print("\n" + "="*50)
    print("All collaboration tests passed! ✅")
    print("="*50)

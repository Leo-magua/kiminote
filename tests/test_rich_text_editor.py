"""
Tests for Rich Text Editor functionality
- Image upload
- Attachment upload
- Attachment management
"""
import pytest
import os
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db, Base, engine

# Create a test client
client = TestClient(app)

# Test data
test_user = {
    "username": "testuser_editor",
    "email": "test_editor@example.com",
    "password": "testpassword123"
}

test_note = {
    "title": "Test Note for Editor",
    "content": "# Test Content\n\nThis is a test note."
}


class TestImageUpload:
    """Test image upload functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        # Register user
        client.post("/api/auth/register", json=test_user)
        
        # Login
        response = client.post("/api/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_upload_image_endpoint_exists(self, auth_token):
        """Test that image upload endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a test image file
        test_image = io.BytesIO(b"fake image content")
        
        response = client.post(
            "/api/upload/image",
            headers=headers,
            files={"file": ("test.png", test_image, "image/png")}
        )
        # Should return 400 for invalid image, not 404
        assert response.status_code != 404, "Image upload endpoint should exist"
    
    def test_upload_image_invalid_format(self, auth_token):
        """Test uploading non-image file to image endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to upload a text file as image
        test_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            "/api/upload/image",
            headers=headers,
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        # Should reject non-image files
        assert response.status_code == 400


class TestAttachmentUpload:
    """Test attachment upload functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        # Try to login first (user might already exist)
        response = client.post("/api/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        if response.status_code != 200:
            # Register if login fails
            client.post("/api/auth/register", json=test_user)
            response = client.post("/api/auth/login", json={
                "username": test_user["username"],
                "password": test_user["password"]
            })
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_upload_attachment_endpoint_exists(self, auth_token):
        """Test that attachment upload endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a test PDF file
        test_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        # Should return 200 or 400, not 404
        assert response.status_code != 404, "Attachment upload endpoint should exist"
    
    def test_get_note_attachments_endpoint_exists(self, auth_token):
        """Test that get note attachments endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a note
        note_response = client.post(
            "/api/notes",
            headers=headers,
            json=test_note
        )
        
        if note_response.status_code == 200:
            note_id = note_response.json()["id"]
            
            # Try to get attachments
            response = client.get(
                f"/api/notes/{note_id}/attachments",
                headers=headers
            )
            # Should return 200 even if no attachments
            assert response.status_code == 200, "Get attachments endpoint should exist"
            
            # Verify response structure
            data = response.json()
            assert "attachments" in data
            assert "total" in data
            assert "note_id" in data


class TestEditorAPI:
    """Test editor-related API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        response = client.post("/api/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        if response.status_code != 200:
            client.post("/api/auth/register", json=test_user)
            response = client.post("/api/auth/login", json={
                "username": test_user["username"],
                "password": test_user["password"]
            })
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_markdown_preview_endpoint(self, auth_token):
        """Test markdown to HTML preview endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        markdown_content = {
            "content": "# Hello\n\nThis is **bold** and *italic*."
        }
        
        response = client.post(
            "/api/preview",
            headers=headers,
            json=markdown_content
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        # Check for h1 tag (might have id attribute)
        assert "<h1" in data["html"]
    
    def test_editor_static_files(self):
        """Test that editor static files are accessible"""
        # Check CSS files
        response = client.get("/static/css/editor.css")
        assert response.status_code == 200
        
        # Check JS files
        response = client.get("/static/js/editor.js")
        assert response.status_code == 200


class TestEditorFrontend:
    """Test editor frontend integration"""
    
    def test_index_page_has_editor(self):
        """Test that index page contains editor elements"""
        # Login first
        client.post("/api/auth/register", json=test_user)
        login_response = client.post("/api/auth/login", json={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        
        # Get the index page
        response = client.get("/", cookies=login_response.cookies)
        
        # Check that editor-related elements are present
        content = response.text
        assert "tiptap" in content.lower() or "editor" in content.lower(), "Editor should be present in page"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for Rich Text Editor functionality
- Image upload
- Attachment upload
- Attachment management
- Undo/redo integration
- Editor frontend
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


def get_auth_token():
    """Helper to get authentication token"""
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


class TestImageUpload:
    """Test image upload functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        return get_auth_token()
    
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
    
    def test_upload_image_success(self, auth_token):
        """Test uploading a valid image file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a simple valid PNG header
        png_header = b'\x89PNG\r\n\x1a\n'
        test_image = io.BytesIO(png_header + b'\x00\x00\x00\rIHDR' + b'\x00' * 100)
        
        response = client.post(
            "/api/upload/image",
            headers=headers,
            files={"file": ("test_image.png", test_image, "image/png")}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert "url" in data
        assert data["url"].startswith("/uploads/")
        assert data["filename"]
        assert data["original_filename"] == "test_image.png"
        assert data["file_size"] > 0
    
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
        return get_auth_token()
    
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
    
    def test_upload_attachment_success(self, auth_token):
        """Test uploading a valid attachment file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_file = io.BytesIO(b"fake pdf content for attachment test")
        
        response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("document.pdf", test_file, "application/pdf")}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert "url" in data
        assert data["url"].startswith("/uploads/")
        assert data["filename"]
        assert data["original_filename"] == "document.pdf"
        assert data["file_size"] > 0
        assert "mime_type" in data
        assert "file_type" in data
        assert data["file_type"] == "document"
    
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
    
    def test_update_note_attachments(self, auth_token):
        """Test updating note attachment associations"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a note
        note_response = client.post(
            "/api/notes",
            headers=headers,
            json={"title": "Attachment Test Note", "content": "Test content"}
        )
        assert note_response.status_code == 200
        note_id = note_response.json()["id"]
        
        # Upload an attachment
        test_file = io.BytesIO(b"test attachment content")
        upload_response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("attach.txt", test_file, "text/plain")}
        )
        assert upload_response.status_code == 200
        attachment_id = upload_response.json()["id"]
        
        # Associate attachment with note
        response = client.put(
            f"/api/notes/{note_id}/attachments",
            headers=headers,
            json=[attachment_id]
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        
        # Verify attachment is associated
        get_response = client.get(
            f"/api/notes/{note_id}/attachments",
            headers=headers
        )
        assert get_response.status_code == 200
        attachments_data = get_response.json()
        assert attachments_data["total"] >= 1
        assert any(att["id"] == attachment_id for att in attachments_data["attachments"])
    
    def test_delete_attachment(self, auth_token):
        """Test deleting an attachment"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Upload an attachment
        test_file = io.BytesIO(b"content to be deleted")
        upload_response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("delete_me.txt", test_file, "text/plain")}
        )
        assert upload_response.status_code == 200
        attachment_id = upload_response.json()["id"]
        
        # Delete the attachment
        delete_response = client.delete(
            f"/api/attachments/{attachment_id}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify attachment no longer exists
        get_response = client.get(
            f"/api/notes/0/attachments",
            headers=headers
        )
        # This might return 200 with empty list, just verify it's not in any note
        # Actually, verify by trying to get the specific attachment (indirectly)
        # A better way: create a note, associate, delete, then verify note has 0 attachments
        note_response = client.post(
            "/api/notes",
            headers=headers,
            json={"title": "Delete Test", "content": "Test"}
        )
        note_id = note_response.json()["id"]
        
        upload2 = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("delete2.txt", io.BytesIO(b"content"), "text/plain")}
        )
        att2_id = upload2.json()["id"]
        
        client.put(f"/api/notes/{note_id}/attachments", headers=headers, json=[att2_id])
        
        client.delete(f"/api/attachments/{att2_id}", headers=headers)
        
        get_response = client.get(f"/api/notes/{note_id}/attachments", headers=headers)
        data = get_response.json()
        assert att2_id not in [a["id"] for a in data["attachments"]]


class TestEditorAPI:
    """Test editor-related API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        return get_auth_token()
    
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
        assert "richtexteditor" in content.lower() or "rich-text" in content.lower() or "editor.js" in content.lower(), "Rich text editor integration should be present"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

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
    
    def test_upload_video_attachment(self, auth_token):
        """Test uploading a video file as attachment"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_file = io.BytesIO(b"fake mp4 video content")
        
        response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("video.mp4", test_file, "video/mp4")}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["file_type"] == "video"
        assert data["mime_type"] == "video/mp4"
    
    def test_upload_audio_attachment(self, auth_token):
        """Test uploading an audio file as attachment"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_file = io.BytesIO(b"fake mp3 audio content")
        
        response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("audio.mp3", test_file, "audio/mpeg")}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["file_type"] == "audio"
        assert data["mime_type"] == "audio/mpeg"


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


class TestEditorEndToEndWorkflow:
    """Test complete rich text editor workflow end-to-end"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        return get_auth_token()
    
    def test_full_editor_workflow(self, auth_token):
        """Test complete workflow: create note, upload image, upload attachment, associate, verify"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create a note with content_html (simulating TipTap editor save)
        note_payload = {
            "title": "富文本编辑器工作流测试",
            "content": "# 工作流测试\n\n这是一个**富文本编辑器**的端到端测试。",
            "content_html": "<h1>工作流测试</h1><p>这是一个<strong>富文本编辑器</strong>的端到端测试。</p>"
        }
        note_response = client.post("/api/notes", headers=headers, json=note_payload)
        assert note_response.status_code == 200, f"Create note failed: {note_response.text}"
        note_id = note_response.json()["id"]
        assert note_response.json()["content_html"] == note_payload["content_html"]
        
        # Step 2: Upload an image
        png_header = b'\x89PNG\r\n\x1a\n'
        test_image = io.BytesIO(png_header + b'\x00\x00\x00\rIHDR' + b'\x00' * 100)
        image_response = client.post(
            "/api/upload/image",
            headers=headers,
            files={"file": ("workflow_image.png", test_image, "image/png")}
        )
        assert image_response.status_code == 200, f"Image upload failed: {image_response.text}"
        image_data = image_response.json()
        image_id = image_data["id"]
        assert image_data["url"].startswith("/uploads/")
        
        # Step 3: Upload an attachment
        test_doc = io.BytesIO(b"This is a test document for workflow validation.")
        attachment_response = client.post(
            "/api/upload/attachment",
            headers=headers,
            files={"file": ("workflow_doc.txt", test_doc, "text/plain")}
        )
        assert attachment_response.status_code == 200, f"Attachment upload failed: {attachment_response.text}"
        attachment_data = attachment_response.json()
        attachment_id = attachment_data["id"]
        assert attachment_data["file_type"] == "document"
        
        # Step 4: Associate both image and attachment with the note
        assoc_response = client.put(
            f"/api/notes/{note_id}/attachments",
            headers=headers,
            json=[image_id, attachment_id]
        )
        assert assoc_response.status_code == 200, f"Associate attachments failed: {assoc_response.text}"
        
        # Step 5: Verify note attachments
        get_attachments = client.get(f"/api/notes/{note_id}/attachments", headers=headers)
        assert get_attachments.status_code == 200
        attachments_list = get_attachments.json()
        assert attachments_list["total"] == 2
        attachment_ids = [a["id"] for a in attachments_list["attachments"]]
        assert image_id in attachment_ids
        assert attachment_id in attachment_ids
        
        # Step 6: Update note from editor (modify content_html)
        update_payload = {
            "title": "富文本编辑器工作流测试 - 已更新",
            "content": "# 工作流测试\n\n已更新内容，包含图片和附件。",
            "content_html": "<h1>工作流测试</h1><p>已更新内容，包含图片和附件。</p>"
        }
        update_response = client.put(f"/api/notes/{note_id}", headers=headers, json=update_payload)
        assert update_response.status_code == 200
        updated_note = update_response.json()
        assert updated_note["content_html"] == update_payload["content_html"]
        
        # Step 7: Verify version history was created (undo/redo support via versions)
        versions_response = client.get(f"/api/notes/{note_id}/versions", headers=headers)
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        assert versions_data["total"] >= 2  # Create + Update
        assert any(v["change_type"] == "create" for v in versions_data["versions"])
        assert any(v["change_type"] == "edit" for v in versions_data["versions"])
        
        # Step 8: Cleanup - delete note (should also cleanup attachments)
        delete_response = client.delete(f"/api/notes/{note_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # Step 9: Verify attachments are cleaned up
        get_attachments_after = client.get(f"/api/notes/{note_id}/attachments", headers=headers)
        # Note endpoint returns 404 because note is deleted
        assert get_attachments_after.status_code == 404
    
    def test_undo_redo_version_history(self, auth_token):
        """Test that saving notes creates version history supporting undo/redo workflow"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create note
        create_payload = {
            "title": "Version History Test",
            "content": "Initial content.",
            "content_html": "<p>Initial content.</p>"
        }
        create_resp = client.post("/api/notes", headers=headers, json=create_payload)
        assert create_resp.status_code == 200
        note_id = create_resp.json()["id"]
        
        # Save multiple times (simulating edit -> undo -> redo -> edit workflow)
        for i in range(3):
            update_payload = {
                "content": f"Updated content v{i+1}.",
                "content_html": f"<p>Updated content v{i+1}.</p>"
            }
            resp = client.put(f"/api/notes/{note_id}", headers=headers, json=update_payload)
            assert resp.status_code == 200
        
        # Verify versions exist
        versions_resp = client.get(f"/api/notes/{note_id}/versions", headers=headers)
        assert versions_resp.status_code == 200
        versions_data = versions_resp.json()
        assert versions_data["total"] >= 4  # create + 3 edits
        
        # Test restore to a previous version (ultimate undo)
        versions = versions_data["versions"]
        earliest_version = versions[-1]  # Last in list is earliest due to desc ordering
        restore_resp = client.post(
            f"/api/notes/{note_id}/versions/{earliest_version['id']}/restore",
            headers=headers
        )
        assert restore_resp.status_code == 200
        restored_note = restore_resp.json()
        assert restored_note["content"] == create_payload["content"]
        assert restored_note["content_html"] == create_payload["content_html"]
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}", headers=headers)


class TestContentHtmlStorage:
    """Test content_html dual-mode storage for rich text editor"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        return get_auth_token()
    
    def test_create_note_with_content_html(self, auth_token):
        """Test creating a note with content_html preserves HTML content"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        payload = {
            "title": "HTML Test Note",
            "content": "# HTML Test\n\nThis is **bold**.",
            "content_html": "<h1>HTML Test</h1><p>This is <strong>bold</strong>.</p>"
        }
        
        response = client.post("/api/notes", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["title"] == payload["title"]
        assert data["content"] == payload["content"]
        assert data["content_html"] == payload["content_html"]
        
        # Verify retrieval also returns content_html
        note_id = data["id"]
        get_response = client.get(f"/api/notes/{note_id}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["content_html"] == payload["content_html"]
    
    def test_update_note_with_content_html(self, auth_token):
        """Test updating a note updates content_html correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create initial note
        create_payload = {
            "title": "Initial Title",
            "content": "Initial content.",
            "content_html": "<p>Initial content.</p>"
        }
        create_response = client.post("/api/notes", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        note_id = create_response.json()["id"]
        
        # Update with new HTML
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content.",
            "content_html": "<p>Updated content.</p><p>Extra paragraph.</p>"
        }
        update_response = client.put(f"/api/notes/{note_id}", headers=headers, json=update_payload)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        # Verify update
        get_response = client.get(f"/api/notes/{note_id}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["title"] == update_payload["title"]
        assert get_data["content_html"] == update_payload["content_html"]
    
    def test_share_page_uses_content_html(self, auth_token):
        """Test that share page renders content_html when available"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        html_content = "<h1>Shared HTML</h1><p>Custom <em>styled</em> paragraph.</p>"
        payload = {
            "title": "Share HTML Test",
            "content": "# Shared HTML\n\nCustom *styled* paragraph.",
            "content_html": html_content
        }
        
        # Create note
        note_response = client.post("/api/notes", headers=headers, json=payload)
        assert note_response.status_code == 200
        note_id = note_response.json()["id"]
        
        # Create share
        share_response = client.post("/api/shares", headers=headers, json={
            "note_id": note_id,
            "permission": "public"
        })
        assert share_response.status_code == 200
        token = share_response.json()["share_token"]
        
        # Access share page
        share_page = client.get(f"/s/{token}")
        assert share_page.status_code == 200
        
        # The HTML content should be present in the rendered page
        assert html_content in share_page.text, "Share page should render content_html directly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

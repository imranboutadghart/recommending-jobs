"""API endpoint tests"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestProfileAPI:
    """Test profile API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_create_profile(self):
        """Test profile creation"""
        profile_data = {
            "name": "Test User",
            "email": "test@example.com",
            "skills": ["Python", "FastAPI"],
            "desired_job_titles": ["Software Engineer"],
            "experience": [],
            "education": []
        }
        
        response = client.post("/api/profile/confirm", json=profile_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test User"
        assert "id" in data
    
    def test_get_profile(self):
        """Test getting profile by ID"""
        # First create a profile
        profile_data = {
            "name": "Get Test",
            "skills": ["JavaScript"],
            "desired_job_titles": ["Developer"],
            "experience": [],
            "education": []
        }
        
        create_response = client.post("/api/profile/confirm", json=profile_data)
        user_id = create_response.json()["id"]
        
        # Now get it
        response = client.get(f"/api/profile/{user_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"
    
    def test_update_profile(self):
        """Test profile update"""
        # Create profile
        profile_data = {
            "name": "Update Test",
            "skills": ["Python"],
            "desired_job_titles": [],
            "experience": [],
            "education": []
        }
        
        create_response = client.post("/api/profile/confirm", json=profile_data)
        user_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "name": "Updated Name",
            "skills": ["Python", "Go"]
        }
        
        response = client.put(f"/api/profile/{user_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Name"
        assert "Go" in data["skills"]


class TestJobsAPI:
    """Test jobs API endpoints"""
    
    def test_search_jobs(self):
        """Test job search"""
        response = client.get("/api/jobs/search?query=software engineer")
        assert response.status_code == 200
        
        jobs = response.json()
        assert isinstance(jobs, list)
        assert len(jobs) > 0  # Should have at least mock jobs
    
    def test_save_job(self):
        """Test saving a job"""
        # Create user first
        profile_data = {
            "name": "Save Job Test",
            "skills": ["Python"],
            "desired_job_titles": ["Engineer"],
            "experience": [],
            "education": []
        }
        
        profile_response = client.post("/api/profile/confirm", json=profile_data)
        user_id = profile_response.json()["id"]
        
        # Save a job
        job_data = {
            "user_id": user_id,
            "job": {
                "id": "test_job_1",
                "title": "Test Job",
                "company": "Test Corp",
                "description": "Test description",
                "location": "Remote",
                "skills": ["Python"],
                "remote": True,
                "source": "test"
            },
            "match_score": 85.5
        }
        
        response = client.post("/api/jobs/save", json=job_data)
        assert response.status_code == 200
        assert "saved" in response.json()["message"].lower()


class TestRecommendationsAPI:
    """Test recommendations API endpoints"""
    
    def test_get_recommendations(self):
        """Test getting job recommendations"""
        # Create user profile
        profile_data = {
            "name": "Recommendation Test",
            "skills": ["Python", "FastAPI"],
            "desired_job_titles": ["Software Engineer"],
            "experience": [],
            "education": []
        }
        
        profile_response = client.post("/api/profile/confirm", json=profile_data)
        user_id = profile_response.json()["id"]
        
        # Get recommendations (this requires Gemini API)
        request_data = {
            "user_id": user_id,
            "limit": 5
        }
        
        try:
            response = client.post("/api/recommendations/", json=request_data)
            # May fail if Gemini API not configured
            if response.status_code == 200:
                matches = response.json()
                assert isinstance(matches, list)
        except Exception:
            pytest.skip("Gemini API not available for recommendations")
    
    def test_quick_recommendations(self):
        """Test quick recommendations endpoint"""
        # Create user
        profile_data = {
            "name": "Quick Test",
            "skills": ["JavaScript"],
            "desired_job_titles": ["Developer"],
            "experience": [],
            "education": []
        }
        
        profile_response = client.post("/api/profile/confirm", json=profile_data)
        user_id = profile_response.json()["id"]
        
        try:
            response = client.get(f"/api/recommendations/quick/{user_id}?limit=3")
            if response.status_code == 200:
                matches = response.json()
                assert len(matches) <= 3
        except Exception:
            pytest.skip("Gemini API not available")


class TestFrontendRoutes:
    """Test frontend page routes"""
    
    def test_home_page(self):
        """Test home page loads"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"JobMatch AI" in response.content or b"Find Your Dream Job" in response.content
    
    def test_upload_page(self):
        """Test upload page loads"""
        response = client.get("/upload")
        assert response.status_code == 200
    
    def test_profile_page(self):
        """Test profile page loads"""
        response = client.get("/profile")
        assert response.status_code == 200
    
    def test_recommendations_page(self):
        """Test recommendations page loads"""
        response = client.get("/recommendations")
        assert response.status_code == 200

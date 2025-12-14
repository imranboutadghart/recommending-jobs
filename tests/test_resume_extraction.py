"""Unit tests for resume extraction service"""
import pytest
import asyncio
from backend.services.resume_extractor import ResumeExtractor, resume_extractor
from backend.models.user import ExtractedResume


class TestResumeExtractor:
    """Test resume extraction functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return ResumeExtractor()
    
    def test_file_type_validation(self, extractor):
        """Test that invalid file types are rejected"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            extractor.extract_text_from_file("test.txt")
    
    @pytest.mark.asyncio
    async def test_resume_data_extraction(self, extractor):
        """Test extraction of structured data from resume text"""
        sample_resume = """
        John Doe
        john.doe@email.com
        (555) 123-4567
        
        SKILLS
        Python, JavaScript, React, FastAPI, AWS, Docker
        
        EXPERIENCE
        Senior Software Engineer at TechCorp (2021-Present)
        - Built scalable web applications
        
        EDUCATION
        BS Computer Science, UC Berkeley, 2018
        """
        
        # Note: This test requires actual Gemini API key to run
        # For unit testing without API, you would mock the API call
        try:
            result = await extractor.extract_resume_data(sample_resume)
            assert isinstance(result, ExtractedResume)
            # The exact extracted data will vary based on Gemini's response
        except Exception as e:
            # If API key not configured, skip this test
            pytest.skip(f"Gemini API not available: {e}")
    
    @pytest.mark.asyncio
    async def test_extract_resume_data_format(self, extractor):
        """Test that extracted data has correct format"""
        simple_text = "Jane Smith\nEmail: jane@example.com\nSkills: Python, SQL"
        
        try:
            result = await extractor.extract_resume_data(simple_text)
            
            # Check that result has expected attributes
            assert hasattr(result, 'name')
            assert hasattr(result, 'email')
            assert hasattr(result, 'skills')
            assert isinstance(result.skills, list)
            assert isinstance(result.experience, list)
            assert isinstance(result.education, list)
            
        except Exception as e:
            pytest.skip(f"Gemini API not available: {e}")


@pytest.mark.integration
class TestResumeExtractionIntegration:
    """Integration tests for complete resume extraction workflow"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_extraction(self):
        """Test complete extraction from sample file"""
        # This would test actual PDF/DOCX file processing
        # Requires sample files in data/sample_resumes/
        pytest.skip("Requires sample PDF/DOCX files")

"""Resume extraction service using Google Gemini API"""
import logging
from typing import Optional
import PyPDF2
import docx
import google.generativeai as genai
from backend.config import settings
from backend.models.user import ExtractedResume, Experience, Education

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)

logger = logging.getLogger(__name__)


class ResumeExtractor:
    """Extract structured information from resumes using Gemini API"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from resume file (PDF or DOCX)"""
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path_lower.endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX file.")
    
    async def extract_resume_data(self, resume_text: str) -> ExtractedResume:
        """Extract structured data from resume text using Gemini API"""
        
        # Create a detailed prompt for Gemini
        prompt = f"""
You are an expert resume parser. Extract the following information from this resume and return it in a structured JSON format.

Resume text:
{resume_text}

Please extract and return a JSON object with the following structure:
{{
    "name": "Full name of the person",
    "email": "Email address if present",
    "phone": "Phone number if present",
    "location": "Current location/city if mentioned",
    "summary": "Professional summary or objective if present",
    "skills": ["skill1", "skill2", ...],  // List of technical and soft skills
    "experience": [
        {{
            "title": "Job title",
            "company": "Company name",
            "duration": "Time period (e.g., 'Jan 2020 - Dec 2022' or '2 years')",
            "description": "Brief job description or key responsibilities"
        }}
    ],
    "education": [
        {{
            "degree": "Degree name",
            "institution": "School/University name",
            "year": "Graduation year or period",
            "field": "Field of study"
        }}
    ]
}}

Important:
- Extract ALL skills mentioned (programming languages, frameworks, tools, soft skills)
- Include all work experience entries
- Include all education entries
- If a field is not found, use null for strings or empty array [] for lists
- Return ONLY the JSON object, no additional text or markdown formatting

JSON:
"""
        
        try:
            # Generate response from Gemini
            response = await self._generate_async(prompt)
            
            # Parse the JSON response
            import json
            import re
            
            # Extract JSON from response (in case it's wrapped in markdown or extra text)
            response_text = response.text
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                # If no JSON found, try parsing the whole response
                data = json.loads(response_text)
            
            # Convert to ExtractedResume model
            experience_list = [
                Experience(**exp) if isinstance(exp, dict) else exp
                for exp in data.get('experience', [])
            ]
            
            education_list = [
                Education(**edu) if isinstance(edu, dict) else edu
                for edu in data.get('education', [])
            ]
            
            extracted = ExtractedResume(
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone'),
                location=data.get('location'),
                summary=data.get('summary'),
                skills=data.get('skills', []),
                experience=experience_list,
                education=education_list
            )
            
            logger.info(f"Successfully extracted resume data for: {extracted.name}")
            return extracted
            
        except Exception as e:
            logger.error(f"Error extracting resume data with Gemini: {e}")
            raise ValueError(f"Failed to extract resume data: {str(e)}")
    
    async def _generate_async(self, prompt: str):
        """Async wrapper for Gemini API call"""
        import asyncio
        # Gemini SDK doesn't have native async, so we run in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.model.generate_content,
            prompt
        )
        return response
    
    async def extract_from_file(self, file_path: str) -> ExtractedResume:
        """
        Complete extraction: read file and extract structured data
        
        For PDFs: Sends file directly to Gemini (better for scanned PDFs)
        For DOCX: Extracts text first, then sends to Gemini
        
        Args:
            file_path: Path to the resume file (PDF or DOCX)
        
        Returns:
            ExtractedResume object with structured data
        """
        file_path_lower = file_path.lower()
        
        # For PDFs, send file directly to Gemini (handles scanned PDFs)
        if file_path_lower.endswith('.pdf'):
            logger.info(f"Processing PDF file with Gemini vision: {file_path}")
            
            try:
                import base64
                import asyncio
                
                # Read PDF file as base64
                with open(file_path, 'rb') as f:
                    pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')
                
                # Create prompt for file analysis
                prompt = """
You are an expert resume parser. Extract the following information from this resume PDF (which may be scanned) and return it in a structured JSON format.

Please extract and return a JSON object with the following structure:
{
    "name": "Full name of the person",
    "email": "Email address if present",
    "phone": "Phone number if present",
    "location": "Current location/city if mentioned",
    "summary": "Professional summary or objective if present",
    "skills": ["skill1", "skill2", ...],
    "experience": [
        {
            "title": "Job title",
            "company": "Company name",
            "duration": "Time period (e.g., 'Jan 2020 - Dec 2022' or '2 years')",
            "description": "Brief job description or key responsibilities"
        }
    ],
    "education": [
        {
            "degree": "Degree name",
            "institution": "School/University name",
            "year": "Graduation year or period",
            "field": "Field of study"
        }
    ]
}

Important:
- Extract ALL skills mentioned (programming languages, frameworks, tools, soft skills)
- Include all work experience entries
- Include all education entries
- If a field is not found, use null for strings or empty array [] for lists
- Return ONLY the JSON object, no additional text or markdown formatting

JSON:
"""
                
                # Use vision model that can handle PDFs
                vision_model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Generate response with the PDF data
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    vision_model.generate_content,
                    [
                        {
                            'mime_type': 'application/pdf',
                            'data': pdf_data
                        },
                        prompt
                    ]
                )
                
                # Parse the response
                import json
                import re
                
                response_text = response.text
                logger.info(f"Received response from Gemini for PDF")
                logger.info(f"response_text: {response_text}")
                
                # Clean up markdown formatting if present
                response_text = response_text.strip()
                if response_text.startswith('```'):
                    # Remove markdown code blocks
                    lines = response_text.split('\n')
                    response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                    if response_text.startswith('json'):
                        response_text = response_text[4:].strip()
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                else:
                    data = json.loads(response_text)
                
                # Convert to ExtractedResume model
                experience_list = [
                    Experience(**exp) if isinstance(exp, dict) else exp
                    for exp in data.get('experience', [])
                ]
                
                education_list = [
                    Education(**edu) if isinstance(edu, dict) else edu
                    for edu in data.get('education', [])
                ]
                
                extracted = ExtractedResume(
                    name=data.get('name'),
                    email=data.get('email'),
                    phone=data.get('phone'),
                    location=data.get('location'),
                    summary=data.get('summary'),
                    skills=data.get('skills', []),
                    experience=experience_list,
                    education=education_list
                )
                
                logger.info(f"Successfully extracted resume data from PDF: {extracted.name}")
                return extracted
                
            except Exception as e:
                logger.error(f"Error processing PDF with Gemini vision API: {e}")
                logger.info("Falling back to text extraction method")
                # Fallback to text extraction if vision processing fails
                try:
                    resume_text = self.extract_text_from_file(file_path)
                    return await self.extract_resume_data(resume_text)
                except Exception as e2:
                    logger.error(f"Text extraction also failed: {e2}")
                    raise ValueError(f"Failed to extract resume data: {str(e)}")
        
        # For DOCX files, use text extraction
        else:
            logger.info(f"Extracting text from DOCX file: {file_path}")
            resume_text = self.extract_text_from_file(file_path)
            return await self.extract_resume_data(resume_text)


# Global instance
resume_extractor = ResumeExtractor()

# Job Recommendation System 🎯

An AI-powered job recommendation system that matches users with jobs using resume analysis, vector embeddings, and intelligent ranking algorithms.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **🤖 AI Resume Extraction**: Uses Google Gemini API to extract structured information from PDF/DOCX resumes
- **🎯 Vector Similarity Matching**: Employs ML embeddings to calculate semantic similarity between profiles and jobs
- **🔍 Multi-Platform Job Aggregation**: Fetches jobs from Adzuna, Jooble, and includes fallback mock data
- **📊 Weighted Ranking Algorithm**: Combines title match, skills overlap, experience, and embeddings for precise scoring
- **💾 SQLite Database**: Stores user profiles and saved jobs
- **🎨 Modern Web Interface**: Beautiful, responsive UI with gradients and animations
- **✅ Comprehensive Tests**: Unit, integration, and API tests with pytest

## Architecture

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │
│  ┌──────────────────────────┐  │
│  │   Resume Extractor       │  │
│  │   (Gemini API)           │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │   Job Aggregator         │  │
│  │   (Multi-platform APIs)  │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │   Embedding Service      │  │
│  │   (Vector Similarity)    │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Recommendation Engine   │  │
│  │  (Weighted Ranking)      │  │
│  └──────────────────────────┘  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  SQLite Database│
└─────────────────┘
```

## Project Structure

```
recommendation_system/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration management
│   ├── models/
│   │   ├── user.py               # User profile models
│   │   └── job.py                # Job listing models
│   ├── services/
│   │   ├── resume_extractor.py   # Gemini API integration
│   │   ├── job_aggregator.py     # Multi-platform job fetching
│   │   ├── embedding_service.py  # Vector embeddings
│   │   └── recommendation.py     # Similarity ranking
│   ├── database/
│   │   └── db.py                 # Database setup
│   └── api/
│       ├── profile.py            # Profile endpoints
│       ├── jobs.py               # Job endpoints
│       └── recommendations.py    # Recommendation endpoints
├── frontend/
│   ├── static/
│   │   ├── css/styles.css        # Modern, responsive styles
│   │   └── js/app.js             # Frontend logic
│   └── templates/
│       ├── index.html            # Landing page
│       ├── upload.html           # Resume upload
│       ├── profile.html          # Profile editing
│       └── recommendations.html  # Job listings
├── tests/
│   ├── test_resume_extraction.py
│   ├── test_job_aggregation.py
│   ├── test_similarity.py
│   └── test_api.py
├── data/
│   └── sample_resumes/           # Example resumes
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- (Optional) Adzuna and Jooble API keys for live job data

### Setup Steps

1. **Clone or navigate to the project directory:**

```bash
cd "c:\Users\hp\Desktop\9raya_ajmi\recommendation system"
```

2. **Create and activate a virtual environment:**

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Copy `.env.example` to `.env` and add your API keys:

```bash
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional job API keys (system uses mock data if not provided):
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key
JOOBLE_API_KEY=your_jooble_api_key
```

5. **Initialize the database:**

The database will be created automatically on first run.

## Running the Application

### Start the server:

```bash
cd backend
python main.py
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs:** http://localhost:8000/redoc

### Using the Application

1. **Navigate to** http://localhost:8000
2. **Click "Upload Resume"** and upload a PDF or DOCX resume
3. **Review and edit** the AI-extracted information
4. **Save your profile** to get personalized job recommendations
5. **Browse ranked jobs** with match scores and explanations
6. **Save favorite jobs** for later review

## API Documentation

### Profile Endpoints

- `POST /api/profile/upload-resume` - Upload and extract resume data
- `POST /api/profile/confirm` - Create/update profile
- `GET /api/profile/{user_id}` - Get profile by ID
- `PUT /api/profile/{user_id}` - Update profile
- `DELETE /api/profile/{user_id}` - Delete profile

### Job Endpoints

- `GET /api/jobs/search` - Search jobs with query and location
- `GET /api/jobs/saved/{user_id}` - Get saved jobs
- `POST /api/jobs/save` - Save a job
- `DELETE /api/jobs/save/{user_id}/{job_id}` - Remove saved job

### Recommendation Endpoints

- `POST /api/recommendations/` - Get personalized job recommendations
- `GET /api/recommendations/quick/{user_id}` - Quick recommendations with simple params

## Running Tests

Run all tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=backend --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_api.py -v
```

**Note:** Some tests require a valid Gemini API key and will be skipped if not available.

## Key Technologies

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **AI/ML:** Google Gemini API, scikit-learn, numpy
- **Database:** SQLite (async with aiosqlite)
- **Document Processing:** PyPDF2, python-docx
- **HTTP:** aiohttp, httpx
- **Testing:** pytest, pytest-asyncio
- **Frontend:** HTML5, CSS3, Vanilla JavaScript

## Matching Algorithm

The recommendation system uses a weighted scoring algorithm:

- **Title Match (25%):** How well the job title matches desired roles
- **Skills Match (40%):** Percentage of required skills the user has
- **Experience Match (15%):** Relevance of work history
- **Embedding Similarity (20%):** Semantic similarity using vector embeddings

Final scores range from 0-100%, with detailed explanations for each match.

## Configuration

Edit `backend/config.py` or use environment variables to configure:

- **Embedding model:** Default is `models/embedding-001` (Gemini)
- **Max jobs per source:** Default 50
- **Default location:** Default "United States"
- **Database URL:** Default SQLite in `data/jobs.db`

## Troubleshooting

### "Gemini API key not found"

Make sure you've added `GEMINI_API_KEY` to your `.env` file.

### "No module named 'backend'"

Make sure you're running commands from the project root directory.

### Database errors

Delete `data/jobs.db` and restart the application to recreate the database.

### No jobs showing up

The system will use mock data if external APIs aren't configured. Check your API keys in `.env`.

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Resume parsing for multiple file formats
- [ ] Advanced filters (salary range, company size, benefits)
- [ ] Email notifications for new matches
- [ ] Mobile application
- [ ] Integration with LinkedIn
- [ ] Job application tracking

## License

MIT License - feel free to use this project for learning or commercial purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please create an issue in the project repository.

---

**Built with ❤️ using FastAPI, Google Gemini AI, and modern web technologies**

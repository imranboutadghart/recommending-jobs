"""Job aggregation service - fetch jobs from multiple platforms"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
from backend.config import settings
from backend.models.job import JobListing

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregate job listings from multiple sources"""
    
    def __init__(self):
        self.sources = []
        
        # Add sources based on available API keys
        if settings.adzuna_api_key and settings.adzuna_app_id:
            self.sources.append('adzuna')
        if settings.jooble_api_key:
            self.sources.append('jooble')
        
        # Always include mock fallback
        self.sources.append('mock')
        
        logger.info(f"Initialized JobAggregator with sources: {self.sources}")
    
    async def fetch_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        max_results: int = 50
    ) -> List[JobListing]:
        """
        Fetch jobs from all available sources
        
        Args:
            query: Search query (job title, keywords)
            location: Location filter
            max_results: Maximum results per source
        
        Returns:
            List of standardized job listings
        """
        location = location or settings.default_location
        
        # Fetch from all sources concurrently
        tasks = []
        
        if 'adzuna' in self.sources:
            tasks.append(self._fetch_adzuna(query, location, max_results))
        if 'jooble' in self.sources:
            tasks.append(self._fetch_jooble(query, location, max_results))
        if 'mock' in self.sources:
            tasks.append(self._fetch_mock_jobs(query, location, max_results))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_jobs = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching jobs: {result}")
                continue
            all_jobs.extend(result)
        
        logger.info(f"Fetched {len(all_jobs)} total jobs for query: {query}")
        return all_jobs
    
    async def _fetch_adzuna(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Fetch jobs from Adzuna API"""
        try:
            # Adzuna API endpoint
            country = "us"  # Default to US, could be made configurable
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            
            params = {
                'app_id': settings.adzuna_app_id,
                'app_key': settings.adzuna_api_key,
                'what': query,
                'where': location,
                'results_per_page': min(max_results, 50),
                'content-type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs = []
                        
                        for job in data.get('results', []):
                            jobs.append(JobListing(
                                id=f"adzuna_{job.get('id', '')}",
                                title=job.get('title', ''),
                                company=job.get('company', {}).get('display_name', 'Unknown'),
                                description=job.get('description', ''),
                                location=job.get('location', {}).get('display_name', location),
                                skills=self._extract_skills(job.get('description', '')),
                                remote='remote' in job.get('description', '').lower(),
                                salary_min=job.get('salary_min'),
                                salary_max=job.get('salary_max'),
                                url=job.get('redirect_url', ''),
                                source='adzuna',
                                posted_date=job.get('created', '')
                            ))
                        
                        logger.info(f"Fetched {len(jobs)} jobs from Adzuna")
                        return jobs
                    else:
                        logger.error(f"Adzuna API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching from Adzuna: {e}")
            return []
    
    async def _fetch_jooble(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Fetch jobs from Jooble API"""
        try:
            url = "https://jooble.org/api/" + settings.jooble_api_key
            
            payload = {
                "keywords": query,
                "location": location,
                "page": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs = []
                        
                        for job in data.get('jobs', [])[:max_results]:
                            jobs.append(JobListing(
                                id=f"jooble_{job.get('id', '')}",
                                title=job.get('title', ''),
                                company=job.get('company', 'Unknown'),
                                description=job.get('snippet', ''),
                                location=job.get('location', location),
                                skills=self._extract_skills(job.get('snippet', '')),
                                remote='remote' in job.get('snippet', '').lower(),
                                salary_min=None,
                                salary_max=None,
                                url=job.get('link', ''),
                                source='jooble',
                                posted_date=job.get('updated', '')
                            ))
                        
                        logger.info(f"Fetched {len(jobs)} jobs from Jooble")
                        return jobs
                    else:
                        logger.error(f"Jooble API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching from Jooble: {e}")
            return []
    
    async def _fetch_mock_jobs(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Generate mock job listings for testing"""
        # This provides fallback data when no real APIs are available
        mock_jobs = [
            # Software Engineering & Tech
            JobListing(
                id="mock_1",
                title="Senior Software Engineer",
                company="TechCorp Inc",
                description="We are looking for a senior software engineer with experience in Python, FastAPI, and React. You will work on building scalable web applications and APIs. Requirements: 5+ years of experience, strong knowledge of Python, experience with cloud platforms (AWS/GCP), RESTful API design.",
                location="San Francisco, CA",
                skills=["Python", "FastAPI", "React", "AWS", "REST APIs", "Docker"],
                remote=True,
                salary_min=120000,
                salary_max=180000,
                url="https://example.com/job/1",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_2",
                title="Data Scientist",
                company="DataAnalytics Co",
                description="Join our data science team to build ML models and analyze large datasets. Requirements: Python, machine learning, SQL, pandas, scikit-learn. Experience with deep learning is a plus.",
                location="New York, NY",
                skills=["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn", "TensorFlow"],
                remote=False,
                salary_min=100000,
                salary_max=150000,
                url="https://example.com/job/2",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_3",
                title="Full Stack Developer",
                company="WebDev Solutions",
                description="Looking for a full stack developer proficient in JavaScript, Node.js, React, and MongoDB. You will build modern web applications from frontend to backend.",
                location="Remote",
                skills=["JavaScript", "Node.js", "React", "MongoDB", "Express", "HTML", "CSS"],
                remote=True,
                salary_min=90000,
                salary_max=130000,
                url="https://example.com/job/3",
                source="mock",
                posted_date="2025-12-09"
            ),
            JobListing(
                id="mock_4",
                title="DevOps Engineer",
                company="CloudTech Inc",
                description="We need a DevOps engineer to manage our cloud infrastructure. Experience with Kubernetes, Docker, CI/CD, and AWS required. You will automate deployments and ensure system reliability.",
                location="Austin, TX",
                skills=["Kubernetes", "Docker", "AWS", "CI/CD", "Python", "Terraform", "Jenkins"],
                remote=True,
                salary_min=110000,
                salary_max=160000,
                url="https://example.com/job/4",
                source="mock",
                posted_date="2025-12-08"
            ),
            JobListing(
                id="mock_5",
                title="Machine Learning Engineer",
                company="AI Innovations",
                description="Build and deploy ML models at scale. Requirements: Python, PyTorch/TensorFlow, MLOps, cloud platforms. Experience with NLP or computer vision is preferred.",
                location="Seattle, WA",
                skills=["Python", "PyTorch", "TensorFlow", "MLOps", "Docker", "Kubernetes", "NLP"],
                remote=True,
                salary_min=130000,
                salary_max=190000,
                url="https://example.com/job/5",
                source="mock",
                posted_date="2025-12-12"
            ),
            JobListing(
                id="mock_6",
                title="Frontend Developer",
                company="UI/UX Studio",
                description="Create beautiful and responsive user interfaces using React, TypeScript, and modern CSS. Work closely with designers to bring mockups to life.",
                location="Los Angeles, CA",
                skills=["React", "TypeScript", "CSS", "HTML", "JavaScript", "Git"],
                remote=True,
                salary_min=85000,
                salary_max=125000,
                url="https://example.com/job/6",
                source="mock",
                posted_date="2025-12-13"
            ),
            JobListing(
                id="mock_7",
                title="Backend Developer",
                company="API Systems Inc",
                description="Build robust and scalable backend systems using Java, Spring Boot, and PostgreSQL. Experience with microservices architecture required.",
                location="Chicago, IL",
                skills=["Java", "Spring Boot", "PostgreSQL", "REST API", "Docker", "Kubernetes"],
                remote=False,
                salary_min=95000,
                salary_max=140000,
                url="https://example.com/job/7",
                source="mock",
                posted_date="2025-12-14"
            ),
            JobListing(
                id="mock_8",
                title="Mobile App Developer",
                company="Mobile First Inc",
                description="Develop cross-platform mobile applications using React Native. Experience with iOS and Android development required.",
                location="Remote",
                skills=["React Native", "JavaScript", "iOS", "Android", "Git", "REST API"],
                remote=True,
                salary_min=90000,
                salary_max=135000,
                url="https://example.com/job/8",
                source="mock",
                posted_date="2025-12-15"
            ),
            JobListing(
                id="mock_9",
                title="Cloud Architect",
                company="Enterprise Solutions",
                description="Design and implement cloud infrastructure solutions on AWS and Azure. Lead cloud migration projects and optimize costs.",
                location="Boston, MA",
                skills=["AWS", "Azure", "Terraform", "Kubernetes", "Python", "Cloud Architecture"],
                remote=True,
                salary_min=140000,
                salary_max=200000,
                url="https://example.com/job/9",
                source="mock",
                posted_date="2025-12-16"
            ),
            JobListing(
                id="mock_10",
                title="Security Engineer",
                company="CyberSafe Corp",
                description="Protect our systems from security threats. Experience with penetration testing, security audits, and compliance required.",
                location="Washington, DC",
                skills=["Security", "Python", "Penetration Testing", "Linux", "Network Security"],
                remote=False,
                salary_min=115000,
                salary_max=165000,
                url="https://example.com/job/10",
                source="mock",
                posted_date="2025-12-17"
            ),
            
            # Healthcare
            JobListing(
                id="mock_11",
                title="Registered Nurse",
                company="City Hospital",
                description="Provide patient care in our emergency department. RN license required with minimum 2 years experience.",
                location="Miami, FL",
                skills=["Patient Care", "Emergency Medicine", "Medical Charts", "IV Therapy"],
                remote=False,
                salary_min=65000,
                salary_max=85000,
                url="https://example.com/job/11",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_12",
                title="Medical Billing Specialist",
                company="HealthCare Services",
                description="Process medical claims and insurance billing. Knowledge of ICD-10 coding and medical terminology required.",
                location="Phoenix, AZ",
                skills=["Medical Billing", "ICD-10", "Insurance Claims", "Healthcare"],
                remote=True,
                salary_min=45000,
                salary_max=60000,
                url="https://example.com/job/12",
                source="mock",
                posted_date="2025-12-12"
            ),
            JobListing(
                id="mock_13",
                title="Physical Therapist",
                company="Rehabilitation Center",
                description="Help patients recover from injuries and improve mobility. PT license and experience with orthopedic cases required.",
                location="Denver, CO",
                skills=["Physical Therapy", "Patient Assessment", "Treatment Planning", "Orthopedics"],
                remote=False,
                salary_min=70000,
                salary_max=95000,
                url="https://example.com/job/13",
                source="mock",
                posted_date="2025-12-13"
            ),
            
            # Finance & Banking
            JobListing(
                id="mock_14",
                title="Financial Analyst",
                company="Global Finance Corp",
                description="Analyze financial data and create reports. Excel, financial modeling, and SQL skills required.",
                location="New York, NY",
                skills=["Financial Analysis", "Excel", "SQL", "Financial Modeling", "PowerBI"],
                remote=False,
                salary_min=75000,
                salary_max=110000,
                url="https://example.com/job/14",
                source="mock",
                posted_date="2025-12-14"
            ),
            JobListing(
                id="mock_15",
                title="Investment Banker",
                company="Wall Street Partners",
                description="Advise clients on mergers, acquisitions, and capital raising. MBA and 3+ years experience in investment banking required.",
                location="New York, NY",
                skills=["Investment Banking", "Financial Analysis", "M&A", "Valuation"],
                remote=False,
                salary_min=150000,
                salary_max=250000,
                url="https://example.com/job/15",
                source="mock",
                posted_date="2025-12-15"
            ),
            JobListing(
                id="mock_16",
                title="Accountant",
                company="Smith & Associates CPA",
                description="Prepare financial statements and tax returns. CPA certification preferred.",
                location="Dallas, TX",
                skills=["Accounting", "Tax Preparation", "Financial Statements", "QuickBooks"],
                remote=True,
                salary_min=60000,
                salary_max=85000,
                url="https://example.com/job/16",
                source="mock",
                posted_date="2025-12-16"
            ),
            
            # Marketing & Communications
            JobListing(
                id="mock_17",
                title="Digital Marketing Manager",
                company="Marketing Pro Agency",
                description="Lead digital marketing campaigns across social media, email, and SEO. Google Analytics and Google Ads experience required.",
                location="Remote",
                skills=["Digital Marketing", "SEO", "Google Ads", "Social Media", "Analytics"],
                remote=True,
                salary_min=70000,
                salary_max=105000,
                url="https://example.com/job/17",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_18",
                title="Content Writer",
                company="Creative Content Co",
                description="Create engaging content for blogs, websites, and social media. Strong writing skills and SEO knowledge required.",
                location="Remote",
                skills=["Content Writing", "SEO", "Copywriting", "Social Media"],
                remote=True,
                salary_min=50000,
                salary_max=70000,
                url="https://example.com/job/18",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_19",
                title="Social Media Manager",
                company="Brand Builders",
                description="Manage social media accounts and create engaging content. Experience with Instagram, TikTok, and Twitter required.",
                location="Los Angeles, CA",
                skills=["Social Media", "Content Creation", "Analytics", "Community Management"],
                remote=True,
                salary_min=55000,
                salary_max=80000,
                url="https://example.com/job/19",
                source="mock",
                posted_date="2025-12-12"
            ),
            JobListing(
                id="mock_20",
                title="Brand Manager",
                company="Consumer Goods Inc",
                description="Develop and execute brand strategy. Experience in consumer goods and marketing analytics required.",
                location="Chicago, IL",
                skills=["Brand Management", "Marketing Strategy", "Analytics", "Market Research"],
                remote=False,
                salary_min=85000,
                salary_max=120000,
                url="https://example.com/job/20",
                source="mock",
                posted_date="2025-12-13"
            ),
            
            # Design
            JobListing(
                id="mock_21",
                title="UX/UI Designer",
                company="Design Studio Pro",
                description="Design user-friendly interfaces for web and mobile apps. Figma, Sketch, and user research experience required.",
                location="San Francisco, CA",
                skills=["UX Design", "UI Design", "Figma", "Sketch", "User Research", "Prototyping"],
                remote=True,
                salary_min=80000,
                salary_max=115000,
                url="https://example.com/job/21",
                source="mock",
                posted_date="2025-12-14"
            ),
            JobListing(
                id="mock_22",
                title="Graphic Designer",
                company="Creative Agency",
                description="Create visual designs for marketing materials, websites, and branding. Adobe Creative Suite proficiency required.",
                location="Portland, OR",
                skills=["Graphic Design", "Adobe Photoshop", "Illustrator", "InDesign", "Branding"],
                remote=True,
                salary_min=55000,
                salary_max=75000,
                url="https://example.com/job/22",
                source="mock",
                posted_date="2025-12-15"
            ),
            JobListing(
                id="mock_23",
                title="Product Designer",
                company="SaaS Startup",
                description="Design end-to-end product experiences. Experience with design systems and user testing required.",
                location="Remote",
                skills=["Product Design", "Figma", "User Testing", "Design Systems", "Prototyping"],
                remote=True,
                salary_min=90000,
                salary_max=130000,
                url="https://example.com/job/23",
                source="mock",
                posted_date="2025-12-16"
            ),
            
            # Sales
            JobListing(
                id="mock_24",
                title="Sales Representative",
                company="Tech Sales Corp",
                description="Sell software solutions to enterprise clients. B2B sales experience and excellent communication skills required.",
                location="Atlanta, GA",
                skills=["Sales", "B2B", "CRM", "Communication", "Negotiation"],
                remote=False,
                salary_min=60000,
                salary_max=100000,
                url="https://example.com/job/24",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_25",
                title="Account Executive",
                company="SaaS Solutions",
                description="Manage client relationships and close deals. Experience with Salesforce and SaaS sales required.",
                location="Remote",
                skills=["Account Management", "Salesforce", "SaaS", "Sales", "Customer Relations"],
                remote=True,
                salary_min=70000,
                salary_max=120000,
                url="https://example.com/job/25",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_26",
                title="Business Development Manager",
                company="Growth Partners",
                description="Identify new business opportunities and build partnerships. Strong networking and negotiation skills required.",
                location="San Diego, CA",
                skills=["Business Development", "Sales", "Networking", "Negotiation", "Strategy"],
                remote=True,
                salary_min=85000,
                salary_max=125000,
                url="https://example.com/job/26",
                source="mock",
                posted_date="2025-12-12"
            ),
            
            # Customer Service
            JobListing(
                id="mock_27",
                title="Customer Support Specialist",
                company="HelpDesk Pro",
                description="Provide excellent customer support via phone, email, and chat. Experience with Zendesk preferred.",
                location="Remote",
                skills=["Customer Support", "Zendesk", "Communication", "Problem Solving"],
                remote=True,
                salary_min=40000,
                salary_max=55000,
                url="https://example.com/job/27",
                source="mock",
                posted_date="2025-12-13"
            ),
            JobListing(
                id="mock_28",
                title="Customer Success Manager",
                company="Enterprise Software Inc",
                description="Ensure customer satisfaction and retention. Experience with SaaS and customer onboarding required.",
                location="Remote",
                skills=["Customer Success", "SaaS", "Customer Onboarding", "CRM", "Analytics"],
                remote=True,
                salary_min=65000,
                salary_max=90000,
                url="https://example.com/job/28",
                source="mock",
                posted_date="2025-12-14"
            ),
            
            # Education
            JobListing(
                id="mock_29",
                title="High School Math Teacher",
                company="City Public Schools",
                description="Teach mathematics to high school students. Teaching certification and degree in mathematics required.",
                location="Houston, TX",
                skills=["Teaching", "Mathematics", "Classroom Management", "Curriculum Development"],
                remote=False,
                salary_min=50000,
                salary_max=70000,
                url="https://example.com/job/29",
                source="mock",
                posted_date="2025-12-15"
            ),
            JobListing(
                id="mock_30",
                title="Online Tutor",
                company="EduTech Platform",
                description="Provide online tutoring in various subjects. Experience with online teaching tools required.",
                location="Remote",
                skills=["Tutoring", "Online Teaching", "Communication", "Subject Expertise"],
                remote=True,
                salary_min=25000,
                salary_max=45000,
                url="https://example.com/job/30",
                source="mock",
                posted_date="2025-12-16"
            ),
            JobListing(
                id="mock_31",
                title="Instructional Designer",
                company="Corporate Training Co",
                description="Design engaging e-learning courses. Experience with Articulate Storyline and adult learning principles required.",
                location="Remote",
                skills=["Instructional Design", "E-Learning", "Articulate Storyline", "Curriculum Design"],
                remote=True,
                salary_min=60000,
                salary_max=85000,
                url="https://example.com/job/31",
                source="mock",
                posted_date="2025-12-17"
            ),
            
            # Engineering (Non-Software)
            JobListing(
                id="mock_32",
                title="Mechanical Engineer",
                company="Manufacturing Corp",
                description="Design and test mechanical systems. AutoCAD and SolidWorks experience required.",
                location="Detroit, MI",
                skills=["Mechanical Engineering", "AutoCAD", "SolidWorks", "CAD", "Manufacturing"],
                remote=False,
                salary_min=70000,
                salary_max=95000,
                url="https://example.com/job/32",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_33",
                title="Electrical Engineer",
                company="Electronics Inc",
                description="Design electrical circuits and systems. Experience with PCB design and embedded systems required.",
                location="San Jose, CA",
                skills=["Electrical Engineering", "PCB Design", "Embedded Systems", "Circuit Design"],
                remote=False,
                salary_min=80000,
                salary_max=110000,
                url="https://example.com/job/33",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_34",
                title="Civil Engineer",
                company="Infrastructure Solutions",
                description="Design and oversee construction projects. PE license and experience with AutoCAD Civil 3D required.",
                location="Charlotte, NC",
                skills=["Civil Engineering", "AutoCAD Civil 3D", "Project Management", "Construction"],
                remote=False,
                salary_min=75000,
                salary_max=105000,
                url="https://example.com/job/34",
                source="mock",
                posted_date="2025-12-12"
            ),
            
            # Legal
            JobListing(
                id="mock_35",
                title="Corporate Lawyer",
                company="Law Firm LLP",
                description="Advise clients on corporate law matters. JD and bar admission required.",
                location="New York, NY",
                skills=["Corporate Law", "Legal Research", "Contract Negotiation", "Compliance"],
                remote=False,
                salary_min=120000,
                salary_max=200000,
                url="https://example.com/job/35",
                source="mock",
                posted_date="2025-12-13"
            ),
            JobListing(
                id="mock_36",
                title="Paralegal",
                company="Legal Services Inc",
                description="Assist lawyers with legal research and document preparation. Paralegal certification preferred.",
                location="Philadelphia, PA",
                skills=["Legal Research", "Document Preparation", "Case Management", "Legal Writing"],
                remote=True,
                salary_min=50000,
                salary_max=70000,
                url="https://example.com/job/36",
                source="mock",
                posted_date="2025-12-14"
            ),
            
            # HR & Recruiting
            JobListing(
                id="mock_37",
                title="HR Manager",
                company="Enterprise Corp",
                description="Manage HR operations including recruitment, benefits, and employee relations. SHRM certification preferred.",
                location="Minneapolis, MN",
                skills=["Human Resources", "Recruitment", "Employee Relations", "Benefits Administration"],
                remote=False,
                salary_min=75000,
                salary_max=105000,
                url="https://example.com/job/37",
                source="mock",
                posted_date="2025-12-15"
            ),
            JobListing(
                id="mock_38",
                title="Technical Recruiter",
                company="Tech Talent Agency",
                description="Recruit software engineers and technical talent. Experience with LinkedIn Recruiter and ATS required.",
                location="Remote",
                skills=["Recruiting", "Technical Recruiting", "LinkedIn Recruiter", "ATS", "Sourcing"],
                remote=True,
                salary_min=60000,
                salary_max=90000,
                url="https://example.com/job/38",
                source="mock",
                posted_date="2025-12-16"
            ),
            JobListing(
                id="mock_39",
                title="HR Business Partner",
                company="Global Enterprise",
                description="Partner with business leaders on HR strategy and talent management. 5+ years HR experience required.",
                location="Seattle, WA",
                skills=["HR Strategy", "Talent Management", "Change Management", "Business Partnership"],
                remote=True,
                salary_min=90000,
                salary_max=125000,
                url="https://example.com/job/39",
                source="mock",
                posted_date="2025-12-17"
            ),
            
            # Data & Analytics
            JobListing(
                id="mock_40",
                title="Data Analyst",
                company="Analytics Corp",
                description="Analyze business data and create visualizations. SQL, Python, and Tableau experience required.",
                location="Remote",
                skills=["Data Analysis", "SQL", "Python", "Tableau", "Excel", "Statistics"],
                remote=True,
                salary_min=70000,
                salary_max=95000,
                url="https://example.com/job/40",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_41",
                title="Business Intelligence Analyst",
                company="BI Solutions",
                description="Build dashboards and reports for business stakeholders. PowerBI and SQL expertise required.",
                location="Boston, MA",
                skills=["Business Intelligence", "PowerBI", "SQL", "Data Visualization", "ETL"],
                remote=True,
                salary_min=80000,
                salary_max=110000,
                url="https://example.com/job/41",
                source="mock",
                posted_date="2025-12-11"
            ),
            
            # Product Management
            JobListing(
                id="mock_42",
                title="Product Manager",
                company="Tech Products Inc",
                description="Define product strategy and roadmap. Experience with agile methodologies and user research required.",
                location="San Francisco, CA",
                skills=["Product Management", "Agile", "User Research", "Roadmap Planning", "Analytics"],
                remote=True,
                salary_min=110000,
                salary_max=160000,
                url="https://example.com/job/42",
                source="mock",
                posted_date="2025-12-12"
            ),
            JobListing(
                id="mock_43",
                title="Technical Product Manager",
                company="SaaS Platform",
                description="Manage technical products and work with engineering teams. Technical background and API knowledge required.",
                location="Remote",
                skills=["Product Management", "Technical", "API", "Agile", "SQL"],
                remote=True,
                salary_min=120000,
                salary_max=170000,
                url="https://example.com/job/43",
                source="mock",
                posted_date="2025-12-13"
            ),
            
            # Project Management
            JobListing(
                id="mock_44",
                title="Project Manager",
                company="Consulting Group",
                description="Lead cross-functional projects from initiation to completion. PMP certification preferred.",
                location="Washington, DC",
                skills=["Project Management", "Agile", "Stakeholder Management", "Risk Management"],
                remote=False,
                salary_min=85000,
                salary_max=120000,
                url="https://example.com/job/44",
                source="mock",
                posted_date="2025-12-14"
            ),
            JobListing(
                id="mock_45",
                title="Scrum Master",
                company="Agile Software Co",
                description="Facilitate scrum ceremonies and remove impediments. CSM certification and agile experience required.",
                location="Remote",
                skills=["Scrum", "Agile", "Facilitation", "Coaching", "JIRA"],
                remote=True,
                salary_min=90000,
                salary_max=125000,
                url="https://example.com/job/45",
                source="mock",
                posted_date="2025-12-15"
            ),
            
            # Operations
            JobListing(
                id="mock_46",
                title="Operations Manager",
                company="Logistics Solutions",
                description="Manage daily operations and optimize processes. Experience in supply chain and logistics required.",
                location="Memphis, TN",
                skills=["Operations Management", "Supply Chain", "Process Improvement", "Logistics"],
                remote=False,
                salary_min=70000,
                salary_max=100000,
                url="https://example.com/job/46",
                source="mock",
                posted_date="2025-12-16"
            ),
            JobListing(
                id="mock_47",
                title="Supply Chain Analyst",
                company="Manufacturing Global",
                description="Analyze supply chain data and optimize inventory. Excel and supply chain software experience required.",
                location="Cleveland, OH",
                skills=["Supply Chain", "Analytics", "Excel", "Inventory Management", "Forecasting"],
                remote=True,
                salary_min=65000,
                salary_max=90000,
                url="https://example.com/job/47",
                source="mock",
                posted_date="2025-12-17"
            ),
            
            # Quality Assurance
            JobListing(
                id="mock_48",
                title="QA Engineer",
                company="Software Testing Inc",
                description="Test software applications and write automated tests. Experience with Selenium and test automation required.",
                location="Remote",
                skills=["QA", "Selenium", "Test Automation", "Python", "JIRA", "Agile"],
                remote=True,
                salary_min=75000,
                salary_max=105000,
                url="https://example.com/job/48",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_49",
                title="Quality Assurance Manager",
                company="Enterprise Software",
                description="Lead QA team and establish testing standards. Experience managing QA teams and test strategies required.",
                location="Austin, TX",
                skills=["QA Management", "Test Strategy", "Team Leadership", "Automation", "CI/CD"],
                remote=True,
                salary_min=95000,
                salary_max=135000,
                url="https://example.com/job/49",
                source="mock",
                posted_date="2025-12-11"
            ),
            
            # Additional Tech Roles
            JobListing(
                id="mock_50",
                title="Database Administrator",
                company="Data Systems Corp",
                description="Manage and optimize database systems. Experience with PostgreSQL, MySQL, and database performance tuning required.",
                location="Remote",
                skills=["Database Administration", "PostgreSQL", "MySQL", "SQL", "Performance Tuning"],
                remote=True,
                salary_min=85000,
                salary_max=120000,
                url="https://example.com/job/50",
                source="mock",
                posted_date="2025-12-12"
            ),
            JobListing(
                id="mock_51",
                title="Site Reliability Engineer",
                company="Cloud Native Inc",
                description="Ensure system reliability and performance. Experience with monitoring, incident response, and automation required.",
                location="San Francisco, CA",
                skills=["SRE", "Kubernetes", "Monitoring", "Python", "Incident Response", "Automation"],
                remote=True,
                salary_min=130000,
                salary_max=180000,
                url="https://example.com/job/51",
                source="mock",
                posted_date="2025-12-13"
            ),
        ]
        
        # Filter by query keywords
        query_lower = query.lower()
        filtered_jobs = [
            job for job in mock_jobs
            if query_lower in job.title.lower() or query_lower in job.description.lower()
        ]
        
        # If no matches, return all mock jobs
        if not filtered_jobs:
            filtered_jobs = mock_jobs
        
        logger.info(f"Generated {len(filtered_jobs[:max_results])} mock jobs")
        return filtered_jobs[:max_results]
    
    def _extract_skills(self, description: str) -> List[str]:
        """
        Extract skills from job description using keyword matching
        This is a simple implementation - could be enhanced with NLP
        """
        # Common technical skills to look for
        skill_keywords = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
            'TensorFlow', 'PyTorch', 'Scikit-learn',
            'Git', 'CI/CD', 'REST API', 'GraphQL',
            'HTML', 'CSS', 'TypeScript'
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in skill_keywords:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills


# Global instance
job_aggregator = JobAggregator()

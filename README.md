# 🏆 Resume Dangal

### AI-Powered Resume Intelligence & Candidate Ranking Platform

Resume Dangal is an AI-powered recruitment intelligence platform designed to automate **resume parsing, job-description analysis, candidate evaluation, and resume ranking**.

The system converts unstructured resumes and job descriptions into structured data using LLMs, evaluates candidate-to-job compatibility using a weighted scoring engine, and produces **ranked and explainable candidate recommendations**.

It combines:

* 🤖 LLM-powered information extraction
* 📄 PDF resume processing
* 🎯 Candidate-to-JD matching
* 📊 Weighted candidate scoring
* 🔍 Explainable evaluations
* ☁️ AWS S3 document storage
* ⚡ FastAPI backend
* 🖥️ Streamlit frontend
* 🧩 Pydantic structured schemas

---

## 🚀 Core Features

### 📄 Resume Intelligence

* Upload PDF resumes
* Extract text from resumes
* Automatically generate candidate profiles
* Extract:

  * Candidate name
  * Skills
  * Experience
  * Projects
  * Education
  * Summary
* Generate an overall resume quality score
* Store resumes securely in AWS S3
* Store structured candidate profiles as JSON
* Generate temporary presigned resume URLs
* Retrieve candidate profiles
* Delete candidate data

---

### 💼 Job Description Intelligence

Resume Dangal converts raw job descriptions into structured data.

The system extracts:

* Job title
* Job summary
* Required skills
* Preferred skills
* Experience requirements
* Education requirements
* Responsibilities
* JD quality score

This structured representation becomes the foundation for candidate matching.

---

### 🎯 AI Candidate Ranking

Multiple candidates can be evaluated against a single Job Description.

The ranking engine evaluates:

* Required skills
* Preferred skills
* Professional experience
* Project relevance
* Responsibility alignment
* Education

Candidates are then sorted according to their final match score.

---

### 🔍 Explainable Candidate Evaluation

Instead of returning only a numerical score, Resume Dangal provides detailed evaluation information.

Each candidate can receive:

* Overall match score
* Required skill score
* Preferred skill score
* Experience score
* Project score
* Responsibility score
* Education score
* Matched skill assessments
* Strengths
* Skill gaps
* Recommendation

This makes the ranking more transparent and useful for recruiters.

---

# 🧠 System Architecture

```text
                         ┌──────────────────────┐
                         │     Streamlit UI     │
                         │       app.py         │
                         └──────────┬───────────┘
                                    │
                                  HTTP
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       main.py        │
                         └──────────┬───────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
       ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
       │ Resume        │    │ Job           │    │ Candidate     │
       │ Extraction    │    │ Description   │    │ Ranking       │
       │ Pipeline      │    │ Extraction    │    │ Engine        │
       └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
               │                    │                    │
               ▼                    ▼                    ▼
       ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
       │ Candidate     │    │ Job           │    │ LLM Semantic  │
       │ Profile       │    │ Description   │    │ Evaluation    │
       │ Schema        │    │ Schema        │    │               │
       └───────────────┘    └───────────────┘    └───────┬───────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Weighted Score  │
                                                │ Calculation     │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Ranked          │
                                                │ Candidates      │
                                                └─────────────────┘

                              AWS S3
                                ▲
                                │
                    ┌───────────┴───────────┐
                    │                       │
                 Resume PDF            Profile JSON
```

---

# 🔄 End-to-End Workflow

```text
Resume PDF
    │
    ▼
PDF Text Extraction
    │
    ▼
LLM Candidate Extraction
    │
    ▼
CandidateProfile
    │
    ├── Skills
    ├── Experience
    ├── Projects
    ├── Education
    └── Resume Score
    │
    ▼
AWS S3
    │
    │
    │
Job Description
    │
    ▼
LLM JD Extraction
    │
    ▼
JobDescriptionProfile
    │
    ├── Required Skills
    ├── Preferred Skills
    ├── Experience
    ├── Education
    └── Responsibilities
    │
    ▼
Candidate Evaluation
    │
    ├── Required Skills
    ├── Preferred Skills
    ├── Experience
    ├── Projects
    ├── Responsibilities
    └── Education
    │
    ▼
Weighted Match Score
    │
    ▼
Candidate Ranking
    │
    ▼
Explainable Results
```

---

# 🧮 Ranking Methodology

Resume Dangal uses a weighted scoring system.

| Evaluation Factor |   Weight |
| ----------------- | -------: |
| Required Skills   |  **40%** |
| Experience        |  **20%** |
| Projects          |  **15%** |
| Preferred Skills  |  **10%** |
| Responsibilities  |  **10%** |
| Education         |   **5%** |
| **Total**         | **100%** |

The scoring logic is implemented in the ranking engine rather than relying entirely on the LLM for arithmetic.

---

## 🛠️ Required Skill Evaluation

Required skills are treated as the most important part of candidate matching.

Each required skill can receive one of four statuses:

| Status    | Credit |
| --------- | -----: |
| `EXACT`   |   100% |
| `RELATED` |    75% |
| `PARTIAL` |    50% |
| `MISSING` |     0% |

For example:

```text
Job Description:

Required Skill:
"Retrieval-Augmented Generation"

Candidate:

"FAISS"
"Vector Embeddings"
"ChromaDB"
"Semantic Search"
```

The semantic evaluation layer can identify related evidence while still requiring the candidate profile to contain supporting information.

---

## 🛡️ Required Skill Score Protection

The system also applies a score cap based on required-skill coverage.

This prevents a candidate from receiving an artificially high final score when critical required skills are missing.

```text
Required Skill Coverage
        │
        ├── 0%              → Maximum score: 45
        ├── <25%            → Maximum score: 55
        ├── <50%            → Maximum score: 70
        ├── <75%            → Maximum score: 82
        └── ≥75%            → Maximum score: 100
```

This makes the ranking system more aligned with real recruitment requirements.

---

# 🧠 LLM Architecture

The project uses **Groq-hosted LLMs through LangChain**.

The LLM is primarily responsible for:

* Understanding unstructured resume content
* Extracting structured candidate information
* Understanding job descriptions
* Identifying semantic relationships between candidate evidence and JD requirements
* Generating strengths and gaps
* Producing structured evaluation outputs

The application code remains responsible for:

* Validation
* Score aggregation
* Required-skill coverage
* Score boundaries
* Candidate sorting
* S3 operations
* API error handling

This separation makes the system more predictable and easier to maintain.

---

# 📦 Structured Data Models

## Candidate Profile

```json
{
  "candidate_id": "uuid",
  "name": "Candidate Name",
  "resume_score": 88,
  "summary": "AI Engineer with experience in...",
  "skills": [
    "Python",
    "FastAPI",
    "AWS",
    "Docker"
  ],
  "experience": [],
  "projects": [],
  "education": []
}
```

---

## Job Description Profile

```json
{
  "job_title": "AI Engineer",
  "summary": "Looking for an AI Engineer...",
  "required_skills": [
    "Python",
    "FastAPI",
    "Machine Learning"
  ],
  "preferred_skills": [
    "AWS",
    "LangChain"
  ],
  "experience_requirements": "1+ years",
  "education_requirements": "Bachelor's degree",
  "responsibilities": [
    "Build AI applications",
    "Develop APIs"
  ],
  "jd_score": 92
}
```

---

## Candidate Evaluation

```json
{
  "candidate_id": "candidate-001",
  "candidate_name": "John Doe",
  "match_score": 86.5,
  "required_skill_score": 90,
  "preferred_skill_score": 80,
  "experience_score": 85,
  "project_score": 88,
  "responsibility_score": 84,
  "education_score": 75,
  "strengths": [
    "Strong Python experience",
    "Relevant AI projects"
  ],
  "gaps": [
    "No Kubernetes evidence found"
  ],
  "recommendation": "Strong candidate"
}
```

---

# 📊 Recommendation System

The final match score is converted into a human-readable recommendation.

|      Score | Recommendation      |
| ---------: | ------------------- |
|   `90–100` | Excellent candidate |
| `80–89.99` | Strong candidate    |
| `70–79.99` | Good candidate      |
| `60–69.99` | Moderate candidate  |
|      `<60` | Weak candidate      |

---

# ☁️ AWS S3 Storage Architecture

Resume Dangal uses Amazon S3 for document and profile storage.

```text
resume-dangal-storage/
│
├── resumes/
│   └── <candidate_id>/
│       └── resume.pdf
│
└── candidates/
    └── <candidate_id>/
        └── profile.json
```

### Resume

```text
resumes/<candidate_id>/resume.pdf
```

### Candidate Profile

```text
candidates/<candidate_id>/profile.json
```

The backend also generates presigned URLs for temporary resume access.

---

# 📁 Project Structure

```text
Resume-Dangal/
│
├── main.py
├── app.py
├── README.md
├── LICENSE
├── .gitignore
│
├── Ranker/
│   ├── __init__.py
│   ├── evaluator.py
│   ├── prompts.py
│   ├── ranker.py
│   └── schemas.py
│
├── services/
│   ├── __init__.py
│   └── s3_service.py
│
└── src/
    └── extractor/
        ├── __init__.py
        ├── candidate.py
        └── job_description.py
```

---

# 🛠️ Technology Stack

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

## AI / LLM

* LangChain
* Groq
* Structured LLM outputs
* Semantic candidate evaluation

## Document Processing

* PyPDF

## Cloud

* Amazon S3
* Boto3

## Frontend

* Streamlit
* Requests

## Configuration

* python-dotenv

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Chitranshu-ByteIQ/Resume-Dangal.git

cd Resume-Dangal
```

---

## 2. Create a Virtual Environment

### Conda

```bash
conda create -n resume-dangal python=3.11 -y
```

Activate:

```bash
conda activate resume-dangal
```

### Or using venv

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

---

# 📦 Install Dependencies

Install the core dependencies:

```bash
pip install fastapi uvicorn streamlit requests boto3 python-dotenv pypdf pydantic langchain-core langchain-groq python-multipart
```

> For production deployments, use a pinned `requirements.txt` generated and tested against your deployment environment.

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

```env
# ==========================================================
# AWS
# ==========================================================

AWS_ACCESS_KEY_ID=your_aws_access_key

AWS_SECRET_ACCESS_KEY=your_aws_secret_key

AWS_REGION=your_aws_region

AWS_S3_BUCKET=your_s3_bucket


# ==========================================================
# GROQ
# ==========================================================

GROQ_API_KEY=your_groq_api_key

GROQ_MODEL=openai/gpt-oss-120b


# ==========================================================
# FRONTEND
# ==========================================================

API_BASE_URL=http://127.0.0.1:8000
```

---

# ⚠️ Security

**Never commit your `.env` file.**

Make sure `.gitignore` contains:

```gitignore
.env
.env.*
!.env.example
```

For production:

* Use IAM roles instead of long-lived AWS credentials where possible.
* Keep S3 buckets private.
* Use least-privilege IAM policies.
* Rotate compromised credentials immediately.
* Never expose API keys in frontend code.
* Never hard-code secrets into Python files.

---

# ☁️ AWS S3 Setup

Create an S3 bucket.

Example:

```text
resume-dangal-storage
```

Configure:

```env
AWS_REGION=your_region
AWS_S3_BUCKET=resume-dangal-storage
```

The application will create logical prefixes automatically:

```text
resumes/
candidates/
```

No manually created folders are required.

---

# ▶️ Running the Backend

Start FastAPI:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

# 🖥️ Running the Frontend

Open another terminal.

Activate the environment:

```bash
conda activate resume-dangal
```

Run Streamlit:

```bash
streamlit run app.py
```

The frontend will normally be available at:

```text
http://localhost:8501
```

---

# 🔌 API Endpoints

## Health

```http
GET /
```

Example:

```json
{
  "status": "ok",
  "message": "Resume Dangal API is running"
}
```

---

## Upload Resume

```http
POST /resumes/upload
```

Content type:

```text
multipart/form-data
```

Field:

```text
file=<resume.pdf>
```

Example using cURL:

```bash
curl -X POST \
  http://127.0.0.1:8000/resumes/upload \
  -F "file=@resume.pdf"
```

The backend:

```text
PDF
 ↓
S3 Upload
 ↓
Text Extraction
 ↓
LLM Candidate Extraction
 ↓
CandidateProfile
 ↓
S3 Profile Storage
 ↓
API Response
```

---

# 📋 List Candidates

```http
GET /candidates
```

Example:

```bash
curl http://127.0.0.1:8000/candidates
```

Candidates are returned ordered by their resume score.

---

# 👤 Get Candidate

```http
GET /candidates/{candidate_id}
```

Example:

```bash
curl http://127.0.0.1:8000/candidates/<candidate_id>
```

Returns:

* Candidate information
* Resume score
* Skills
* Experience
* Projects
* Education
* Temporary resume download URL

---

# 🗑️ Delete Candidate

```http
DELETE /candidates/{candidate_id}
```

Example:

```bash
curl -X DELETE \
  http://127.0.0.1:8000/candidates/<candidate_id>
```

The backend removes:

```text
resumes/<candidate_id>/resume.pdf

candidates/<candidate_id>/profile.json
```

---

# 💼 Extract Job Description

```http
POST /jobs/extract
```

Content type:

```text
text/plain
```

Example:

```bash
curl -X POST \
  http://127.0.0.1:8000/jobs/extract \
  -H "Content-Type: text/plain" \
  --data "We are looking for an AI Engineer with Python, FastAPI and AWS experience."
```

The API converts the raw JD into a structured `JobDescriptionProfile`.

The current backend also validates the JD length and rejects inputs exceeding:

```text
30,000 characters
```

---

# 🎯 Candidate Ranking

The ranking system accepts:

```text
JobDescriptionProfile
+
Candidate IDs
```

Conceptually:

```json
{
  "job_description": {
    "job_title": "AI Engineer",
    "summary": "AI engineering role",
    "required_skills": [
      "Python",
      "FastAPI",
      "Machine Learning"
    ],
    "preferred_skills": [
      "AWS",
      "LangChain"
    ],
    "experience_requirements": "1+ years",
    "education_requirements": "Bachelor's degree",
    "responsibilities": [
      "Build AI applications"
    ],
    "jd_score": 90
  },
  "candidate_ids": [
    "candidate-001",
    "candidate-002",
    "candidate-003"
  ]
}
```

The system evaluates every candidate and sorts the results by:

```text
match_score DESC
```

The exact current route and request schema can always be verified through:

```text
http://127.0.0.1:8000/docs
```

---

# 📈 Example Ranking

```text
==================================================
             RESUME DANGAL RESULTS
==================================================

Job: AI Engineer

--------------------------------------------------
Rank: 1
Candidate: Candidate A

Match Score: 91.50

Recommendation:
Excellent candidate

Required Skills:     95
Experience:          88
Projects:            92
Preferred Skills:    80
Responsibilities:    90
Education:           85

Strengths:
✓ Strong Python experience
✓ Relevant AI projects
✓ Strong backend experience

Gaps:
• Limited Kubernetes evidence
--------------------------------------------------

Rank: 2
Candidate: Candidate B

Match Score: 78.20

Recommendation:
Good candidate
--------------------------------------------------
```

---

# 🔍 Explainability Example

Instead of:

```text
Candidate Score = 82
```

Resume Dangal can provide:

```text
Candidate Score = 82

Strengths:
- Strong Python experience
- Relevant machine learning projects
- Good FastAPI experience

Gaps:
- Missing Kubernetes experience
- Limited AWS production experience

Recommendation:
Strong candidate
```

This allows recruiters to understand **why** a candidate received a particular ranking.

---

# 🧱 Design Principles

## 1. Structured LLM Outputs

LLM responses are constrained through Pydantic schemas instead of relying on arbitrary text.

This provides predictable application contracts.

---

## 2. Deterministic Score Aggregation

The LLM evaluates semantic relationships, while Python performs:

* Weighted scoring
* Score normalization
* Required-skill coverage
* Score caps
* Sorting
* Deduplication
* Recommendation generation

This reduces the amount of critical business logic delegated to the model.

---

## 3. Separation of Responsibilities

```text
main.py
    ↓
API Layer

src/extractor/
    ↓
Information Extraction

Ranker/
    ↓
Candidate Evaluation

services/
    ↓
AWS Infrastructure

app.py
    ↓
Frontend
```

This makes the project easier to extend and maintain.

---

# 🧪 Testing Strategy

Recommended test layers:

```text
                    Tests
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
     Unit Tests   Integration   API Tests
        │             │             │
        ▼             ▼             ▼
    Scoring       S3 + LLM      FastAPI
    Schemas       Pipeline      Endpoints
    Utilities
```

Recommended test cases include:

* Invalid PDF upload
* Empty PDF
* Corrupted PDF
* Missing API keys
* Missing S3 bucket
* Invalid candidate ID
* Duplicate candidate IDs
* Empty JD
* Oversized JD
* Missing required skills
* Candidate with no experience
* Candidate with no projects
* Candidate with incomplete education
* S3 object not found
* LLM failure
* Invalid structured LLM output

---

# 🚀 Production Considerations

Resume Dangal is designed with production-oriented separation of concerns, but a production deployment should additionally consider:

### Security

* Authentication
* Authorization
* IAM least privilege
* Private S3 buckets
* Secret management
* Rate limiting

### Reliability

* LLM retry policies
* Timeouts
* Circuit breakers
* Graceful degradation
* Background processing
* Queue-based workloads

### Observability

* Structured logging
* Request IDs
* LLM latency tracking
* Token usage monitoring
* Error tracking
* Application metrics

### Scalability

For large resume collections:

```text
User
 │
 ▼
FastAPI
 │
 ▼
Message Queue
 │
 ├───────────────┐
 ▼               ▼
Resume Worker   JD Worker
 │               │
 └───────┬───────┘
         ▼
       S3
         │
         ▼
 Ranking Workers
         │
         ▼
   Ranking Results
```

This architecture would allow resume processing and candidate ranking to scale independently.

---

# 🗺️ Roadmap

Future improvements may include:

* [ ] Batch resume processing
* [ ] Async resume processing
* [ ] Background job queues
* [ ] Authentication and authorization
* [ ] Recruiter accounts
* [ ] Multi-tenant architecture
* [ ] Candidate search
* [ ] Advanced filtering
* [ ] Skill-gap analysis
* [ ] Candidate comparison
* [ ] Recruiter feedback-based score calibration
* [ ] Evaluation caching
* [ ] LLM observability
* [ ] Automated ranking benchmarks
* [ ] CI/CD pipeline
* [ ] Docker deployment
* [ ] Kubernetes deployment
* [ ] Cloud-native monitoring

---

# 🤝 Contributing

Contributions are welcome.

### 1. Fork the repository

```bash
git clone https://github.com/Chitranshu-ByteIQ/Resume-Dangal.git
```

### 2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

### 3. Make your changes

```bash
git add .
```

### 4. Commit

```bash
git commit -m "feat: describe your change"
```

### 5. Push

```bash
git push origin feature/your-feature
```

### 6. Open a Pull Request

Please include:

* What changed
* Why the change was required
* How it was tested
* Any new environment variables
* Any deployment impact

---

# 📜 License

See the repository's [`LICENSE`](LICENSE) file for licensing information.

---

# 👨‍💻 Author

**Chitranshu**

GitHub:

https://github.com/Chitranshu-ByteIQ

Project:

https://github.com/Chitranshu-ByteIQ/Resume-Dangal

---

# ⭐ Why Resume Dangal?

Resume Dangal demonstrates how modern AI engineering can combine:

```text
LLMs
 +
Structured Outputs
 +
PDF Processing
 +
Semantic Evaluation
 +
Deterministic Scoring
 +
FastAPI
 +
AWS S3
 +
Streamlit
```

to build an end-to-end **AI-powered recruitment intelligence system**.

The goal is not simply to ask an LLM:

> "Which candidate is better?"

Instead, Resume Dangal builds a structured pipeline where candidate information, job requirements, evaluation criteria, scoring, and explanations are represented explicitly.

That makes the system easier to **understand, debug, evaluate, extend, and eventually productionize**.

# 🏆 Resume Dangal

**AI-Powered Resume Ranking & Candidate Intelligence System**

Resume Dangal is an AI-powered resume screening and ranking system that evaluates multiple candidates against a given Job Description (JD). It combines deterministic scoring with LLM-based semantic analysis to produce explainable candidate rankings.

The system is designed around a **FastAPI backend, Streamlit frontend, AWS S3 resume storage, and LangGraph-based AI ranking pipeline**.

---

## 🚀 Features

### 📄 Resume Management

* Upload PDF resumes
* Store resumes securely in AWS S3
* Automatically generate a unique ID for every resume
* Retrieve all previously uploaded resumes
* Select existing resumes for evaluation
* Delete resumes
* Prevent duplicate filename overwrites
* Validate file type and file size

### 🎯 AI Resume Ranking

Compare multiple resumes against a Job Description.

The ranking engine evaluates:

* **Skills**
* **Project relevance**
* **Professional experience**
* **Education**
* **Overall JD alignment**

The scoring system prioritizes:

| Factor     | Weight |
| ---------- | -----: |
| Skills     |    40% |
| Projects   |    30% |
| Experience |    20% |
| Education  |    10% |

### 🧠 Explainable AI

The system does not simply return a score.

It provides:

* Final score
* Candidate rank
* Recommendation
* Matched skills
* Skill score
* Project score
* Experience score
* Education score
* Reason for recommendation

### ⚡ Production-Oriented Architecture

* FastAPI REST API
* Streamlit UI
* AWS S3 storage
* LangGraph workflow
* Pydantic structured outputs
* Deterministic scoring where possible
* LLM semantic evaluation where required
* Logging and error handling

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │     Streamlit UI     │
                         │      Frontend        │
                         └──────────┬──────────┘
                                    │
                              HTTP / REST
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │       main.py       │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │     Upload   │    │    Resume    │    │   Ranking    │
        │    / List    │    │   Retrieval  │    │    Engine    │
        │   / Delete   │    │              │    │              │
        └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                           ┌──────────────┐
                           │   AWS S3     │
                           │    Storage   │
                           └──────────────┘
                                                      
                                                       ▼
                                             ┌──────────────────┐
                                             │    LangGraph     │
                                             │     Workflow     │
                                             └────────┬─────────┘
                                                      │
                             ┌────────────────────────┼──────────────────────┐
                             ▼                        ▼                      ▼
                       ┌───────────┐           ┌───────────┐          ┌───────────┐
                       │  Resume   │           │     JD    │          │ Candidate │
                       │  Parser   │           │  Analyzer │          │  Scorer   │
                       └───────────┘           └───────────┘          └─────┬─────┘
                                                                            │
                                                                            ▼
                                                                     ┌────────────┐
                                                                     │   Ranker   │
                                                                     └─────┬──────┘
                                                                           │
                                                                           ▼
                                                                     Ranked Results
```

---

# 🔄 Ranking Pipeline

The ranking engine follows a multi-stage pipeline:

```text
Job Description
       │
       ▼
JD Analysis
       │
       ├── Required Skills
       ├── Preferred Skills
       ├── Required Experience
       └── Education Requirements
       
Resume PDFs
       │
       ▼
PDF Text Extraction
       │
       ▼
Resume Parsing
       │
       ├── Skills
       ├── Experience
       ├── Education
       └── Projects
       
       ▼
Candidate Scoring
       │
       ├── Skill Matching
       ├── Project Relevance
       ├── Experience
       └── Education
       
       ▼
Final Score
       │
       ▼
Candidate Ranking
```

---

# 🧮 Scoring Methodology

Resume Dangal uses a weighted scoring system.

## Skills — 40%

Skills have the highest weight because technical and professional competencies are usually the strongest indicators of JD alignment.

The system uses two stages:

### 1. Deterministic matching

Required skills are searched across the entire resume text.

This prevents the system from missing skills that appear inside:

* Project descriptions
* Work experience
* Certifications
* Summary
* Skills section

### 2. Semantic matching

An LLM evaluates skills that may be conceptually equivalent even when the exact keyword is absent.

For example:

```text
JD:
"Retrieval-Augmented Generation"

Resume:
"FAISS, vector embeddings, ChromaDB"
```

The semantic layer can identify the relationship while requiring evidence from the resume.

---

## Projects — 30%

Projects are evaluated based on:

* Technical relevance
* Technologies used
* Problem similarity
* Methods implemented
* Relationship to the JD

A project title alone is not considered sufficient evidence.

---

## Experience — 20%

Professional experience is calculated using actual experience duration.

Internships count as professional experience.

Academic projects and coursework do not count as professional experience.

Experience scoring is calculated deterministically rather than asking the LLM to perform arithmetic.

---

## Education — 10%

Education considers:

* Degree level
* Field of study
* Relevance to the role
* JD education requirements

---

# 📊 Example Result

```text
Rank: 1

Candidate: Rahul Sharma

Final Score: 91%

Recommendation: Strongly Recommended

Skill Score: 96
Project Score: 92
Experience Score: 85
Education Score: 90

Matched Skills:
Python
FastAPI
Docker
AWS
Kubernetes
LangChain
LangGraph

Reason:
Candidate demonstrates strong alignment with the required
technical stack and relevant project experience.
```

---

# 📁 Project Structure

```text
Resume-Dangal/
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── Frontend/
│   └── app.py
│
├── services/
│   ├── __init__.py
│   └── s3_service.py
│
└── src/
    ├── __init__.py
    │
    ├── agents/
    │   ├── __init__.py
    │   ├── jd_analyzer.py
    │   ├── matcher.py
    │   ├── ranker.py
    │   ├── recruiter_matcher.py
    │   ├── resume_parser.py
    │   ├── section_scorer.py
    │   └── skill_gap.py
    │
    ├── graph/
    │   ├── __init__.py
    │   ├── state.py
    │   └── workflow.py
    │
    ├── llm/
    │   ├── __init__.py
    │   └── llm_config.py
    │
    ├── models/
    │   ├── __init__.py
    │   └── schema.py
    │
    ├── prompts/
    │   ├── __init__.py
    │   └── prompts.py
    │
    └── utils/
        ├── __init__.py
        ├── file_handler.py
        └── text_cleaner.py
```

---

# 🛠️ Tech Stack

### Backend

* Python
* FastAPI
* Pydantic
* Uvicorn

### AI / ML

* LangChain
* LangGraph
* LLM-based structured extraction
* Deterministic skill matching
* Semantic skill matching

### Frontend

* Streamlit
* Requests
* Pandas

### Storage

* AWS S3
* Boto3

### Document Processing

* PyPDF

### Configuration

* python-dotenv

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/Chitranshu-ByteIQ/Resume-Dangal.git

cd Resume-Dangal
```

---

## 2. Create a Conda environment

```bash
conda create -n resume-dangal python=3.11 -y
```

Activate it:

```bash
conda activate resume-dangal
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

AWS_REGION=ap-south-2
AWS_S3_BUCKET=resume-dangal-storage

GROQ_API_KEY=your_groq_api_key

BACKEND_URL=http://127.0.0.1:8000
```

Never commit your `.env` file.

---

# ☁️ AWS S3 Setup

Create an S3 bucket and configure the environment variables.

The application stores resumes using the following structure:

```text
resume-dangal-storage/
│
└── resumes/
    ├── <resume-id>_candidate1.pdf
    ├── <resume-id>_candidate2.pdf
    └── <resume-id>_candidate3.pdf
```

Each uploaded resume receives a unique ID.

This prevents two candidates with the same filename from overwriting each other.

---

# ▶️ Running the Application

The system consists of two processes.

## Start FastAPI

From the project root:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Start Streamlit

Open another terminal:

```bash
conda activate resume-dangal
```

From the project root:

```bash
streamlit run Frontend/app.py
```

Frontend:

```text
http://localhost:8501
```

---

# 🔌 API Endpoints

## Health

```http
GET /health
```

Example:

```json
{
  "status": "healthy",
  "storage": "connected"
}
```

---

## List Resumes

```http
GET /api/resumes
```

Example:

```json
{
  "count": 2,
  "resumes": [
    {
      "resume_id": "8f12abc",
      "filename": "john_resume.pdf",
      "s3_key": "resumes/8f12abc_john_resume.pdf",
      "size": 523421,
      "last_modified": "2026-08-24T10:30:00+00:00"
    }
  ]
}
```

---

## Upload Resume

```http
POST /api/resumes/upload
```

Form field:

```text
file
```

Only PDF files up to 10 MB are accepted.

---

## Get Resume

```http
GET /api/resumes/{resume_id}
```

---

## Delete Resume

```http
DELETE /api/resumes/{resume_id}
```

---

## Rank Resumes

```http
POST /api/ranking
```

Request:

```json
{
  "job_description": "We are looking for an AI Engineer with Python, FastAPI, AWS and LangChain experience.",
  "resume_ids": [
    "8f12abc",
    "91bd821",
    "72ad821"
  ]
}
```

Response:

```json
{
  "success": true,
  "total_resumes": 3,
  "results": [
    {
      "Rank": 1,
      "Candidate Name": "john_resume.pdf",
      "Final Score": 91,
      "Recommendation": "Strongly Recommended"
    }
  ]
}
```

---

# 🖥️ Frontend Workflow

The Streamlit interface follows this workflow:

```text
1. Upload resumes
        ↓
2. Resumes are stored in S3
        ↓
3. Resume Library refreshes
        ↓
4. Select existing resumes
        ↓
5. Paste Job Description
        ↓
6. Click "Rank Selected Resumes"
        ↓
7. Backend retrieves selected PDFs
        ↓
8. PDFs are converted to text
        ↓
9. LangGraph processes candidates
        ↓
10. Results appear in Streamlit
```

---

# 🧠 Why LangGraph?

LangGraph is used to represent the ranking process as a controlled workflow.

```text
START
  │
  ▼
Resume Parser
  │
  ▼
JD Analyzer
  │
  ▼
Candidate Scorer
  │
  ▼
Candidate Ranker
  │
  ▼
END
```

This makes the system easier to:

* Debug
* Extend
* Test
* Observe
* Add additional AI agents
* Introduce human-in-the-loop workflows

---

# 🛡️ Design Principles

Resume Dangal follows several important engineering principles.

### Deterministic where possible

Arithmetic and exact keyword matching should not depend on an LLM.

### LLM where semantic reasoning is required

LLMs are used for:

* Resume information extraction
* Semantic skill relationships
* Project relevance
* Education relevance
* Evidence-based reasoning

### API-first architecture

The frontend does not communicate directly with AWS S3.

```text
Streamlit
    ↓
FastAPI
    ↓
S3
```

This keeps credentials and storage logic away from the frontend.

### Stable identifiers

Every resume receives a unique ID.

The frontend uses:

```text
resume_id
```

rather than manipulating S3 keys directly.

### Explainability

The system provides the reasoning behind the ranking rather than returning only a numerical score.

---

# ⚠️ Current Limitations

The current version primarily supports **text-based PDF resumes**.

Scanned/image-only PDFs may require an OCR pipeline.

Potential future improvements include:

* OCR for scanned resumes
* Resume preview
* Candidate profile extraction
* Duplicate resume detection
* Better semantic skill ontology
* Vector-based resume retrieval
* Resume-to-JD similarity embeddings
* Evaluation benchmark datasets
* Ranking evaluation metrics such as NDCG and MRR
* Human-in-the-loop review
* Authentication and multi-user support
* Persistent ranking history
* Recruiter dashboards
* Async/background ranking jobs
* Docker deployment
* CI/CD
* Cloud deployment
* Observability with LangSmith

---

# 🔬 Future Evaluation Strategy

For a production-quality ranking system, accuracy should not be judged only by whether an LLM "looks reasonable."

The system should eventually be evaluated using a labeled dataset containing:

```text
Job Description
        +
Multiple Resumes
        +
Human Recruiter Ranking
        ↓
Ground Truth
```

Then evaluate:

* Precision@K
* Recall@K
* NDCG@K
* MRR
* Pairwise ranking accuracy
* Skill extraction accuracy
* Experience extraction accuracy
* Recommendation accuracy

This allows Resume Dangal to measure whether the ranking engine actually performs well against human recruiter judgments.

---

# 🔒 Security Considerations

Before deploying publicly:

* Never expose AWS credentials to Streamlit
* Keep `.env` out of Git
* Use IAM roles with least privilege
* Validate uploaded files
* Limit upload size
* Sanitize filenames
* Validate S3 keys server-side
* Add authentication
* Add rate limiting
* Add request logging
* Avoid exposing raw candidate data unnecessarily
* Encrypt sensitive data at rest
* Configure appropriate S3 bucket policies

---

# 🧪 Development

Run FastAPI:

```bash
uvicorn main:app --reload
```

Run Streamlit:

```bash
streamlit run Frontend/app.py
```

Check API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 📌 Project Goal

Resume Dangal aims to move beyond simple keyword-based ATS matching.

The long-term goal is to build an **evidence-based AI recruitment system** that can understand:

```text
Job Requirements
       ↓
Candidate Skills
       ↓
Candidate Experience
       ↓
Project Relevance
       ↓
Education
       ↓
Evidence
       ↓
Explainable Score
       ↓
Candidate Ranking
```

The objective is not simply to ask an LLM:

> "Which resume is better?"

Instead, the system decomposes the decision into measurable components and uses AI only where semantic reasoning is genuinely useful.

---

# 👨‍💻 Author

**Chitranshu-ByteIQ**

Computer Science & Engineering — Data Science

GitHub:
https://github.com/Chitranshu-ByteIQ

---

# 📄 License

This project is licensed under the MIT License.

See `LICENSE` for more information.

# Job Board Platform Backend

A robust, role-based RESTful API for a Job Board platform built with Django, Django REST Framework (DRF), and SQLite.

---

## Tech Stack

- **Language:** Python 3.13
- **Framework:** Django 6.1
- **API Toolkit:** Django REST Framework (DRF) 3.18
- **Authentication:** DRF Token Authentication (`rest_framework.authtoken`)
- **Database:** SQLite3
- **File Handling:** Multipart form-data with server-side extension & size validation (PDF, DOC, DOCX up to 5MB)

---

## Project Overview

The Job Board platform provides a dual-role workflow:

- **Employers:** Register company profiles, create and manage job postings, review applicants who applied to their postings, and update application review statuses.
- **Candidates:** Register candidate profiles, upload resumes, search/filter active jobs, submit job applications with custom cover letters, and track application statuses.
- **Admins:** Manage data via the Django Admin interface and query platform-wide aggregate metrics via an administrative stats endpoint.
- **Event-Driven Notifications:** Real-time in-app notification records are generated automatically whenever a candidate applies (notifying the employer) and whenever an application status changes (notifying the candidate).

---

## Documentation PDF

A complete, step-by-step visual technical reference PDF is included in the root directory:
- **[Job_Board_Platform_Documentation.pdf](Job_Board_Platform_Documentation.pdf)**: Comprehensive 5-page architectural guide covering system overview, entity-relationship schemas, end-to-end operational workflows, complete API endpoint specifications, Postman samples, and deployment checklists.

---

## Setup & Installation

### 1. Clone & Navigate
```bash
git clone <repository-url>
cd CodeAlpha_JobBoard
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.

### 7. Run Unit Tests
```bash
python manage.py test jobs
```

---

## API Endpoints Reference

All API routes are prefixed with `/api/`.

| Method | Endpoint | Access Level | Description |
|---|---|---|---|
| `POST` | `/api/register/employer/` | Public | Register an employer and company profile |
| `POST` | `/api/register/candidate/` | Public | Register a job candidate profile |
| `POST` | `/api/login/` | Public | Authenticate user & receive auth token |
| `GET` | `/api/jobs/` | Public | List active jobs with optional filter query parameters |
| `POST` | `/api/jobs/` | Employer only | Post a new job |
| `GET` | `/api/jobs/<id>/` | Public | Retrieve job details by ID |
| `POST` | `/api/resume/upload/` | Candidate only | Upload candidate resume (PDF/DOC/DOCX, max 5MB) |
| `POST` | `/api/jobs/<id>/apply/` | Candidate only | Apply for an active job (blocks duplicates) |
| `GET` | `/api/my-applications/` | Candidate only | List all applications submitted by candidate |
| `GET` | `/api/jobs/<id>/applications/` | Employer only | View applicants for employer's own job |
| `PATCH` | `/api/applications/<id>/status/` | Employer only | Update applicant status (`applied`, `reviewed`, `shortlisted`, `rejected`, `hired`) |
| `GET` | `/api/notifications/` | Authenticated | Retrieve notifications for the logged-in user |
| `GET` | `/api/stats/` | Admin only | Platform statistics (total jobs, total applications, breakdown by status) |

---

## Query Parameters for Job Filtering

The `GET /api/jobs/` endpoint supports combination filtering:

- `?search=<term>`: Matches against `title`, `description`, or `skills_required` (case-insensitive)
- `?location=<city/remote>`: Matches against `location` (case-insensitive)
- `?job_type=<type>`: Matches job type (`full-time`, `part-time`, `internship`, `contract`)
- `?min_salary=<number>`: Filters jobs with `salary >= min_salary`

**Example:**
```
GET /api/jobs/?search=django&location=remote&job_type=full-time&min_salary=80000
```

---

## Authentication Header

For endpoints requiring authentication, supply the DRF Token in the HTTP `Authorization` header:

```http
Authorization: Token <your_token_here>
```

---

## Postman-Friendly Sample JSON Request Bodies

Copy and paste these payloads directly into Postman under **Body -> raw -> JSON**:

### 1. Register Employer (`POST /api/register/employer/`)
```json
{
  "username": "techcorp_hr",
  "email": "careers@techcorp.io",
  "password": "StrongPassword123!",
  "company_name": "TechCorp Solutions",
  "description": "Leading cloud solutions and distributed systems development firm.",
  "website": "https://techcorp.io"
}
```

### 2. Register Candidate (`POST /api/register/candidate/`)
```json
{
  "username": "alex_dev",
  "email": "alex.dev@example.com",
  "password": "StrongPassword123!",
  "full_name": "Alex Mercer",
  "phone": "+1-555-0199",
  "skills": "Python, Django, Django REST Framework, PostgreSQL, Docker, Git"
}
```

### 3. Login (`POST /api/login/`)
```json
{
  "username": "techcorp_hr",
  "password": "StrongPassword123!"
}
```

### 4. Create Job Posting (`POST /api/jobs/`)
*Headers: `Authorization: Token <employer_token>`*
```json
{
  "title": "Senior Backend Engineer",
  "description": "We are seeking a senior backend engineer to scale our core API services and data ingestion pipelines.",
  "location": "Remote",
  "job_type": "full-time",
  "salary": 115000.00,
  "skills_required": "Python, Django, PostgreSQL, Redis, Celery, REST APIs",
  "is_active": true
}
```

### 5. Apply for Job (`POST /api/jobs/1/apply/`)
*Headers: `Authorization: Token <candidate_token>`*
```json
{
  "cover_letter": "I have over 5 years of experience building high-throughput backend services using Django and DRF. I would love to contribute to TechCorp Solutions."
}
```

### 6. Update Application Status (`PATCH /api/applications/1/status/`)
*Headers: `Authorization: Token <employer_token>`*
*Allowed values: `applied`, `reviewed`, `shortlisted`, `rejected`, `hired`*
```json
{
  "status": "shortlisted"
}
```

### 7. Resume Upload (`POST /api/resume/upload/`)
*Headers: `Authorization: Token <candidate_token>`*
- In Postman, select **Body -> form-data**
- Set Key: `resume` (change key type from *Text* to *File*)
- Select a file from your local system (`.pdf`, `.doc`, or `.docx`, max 5MB)

---

## Sample Responses

### Login Response (`POST /api/login/`)
```json
{
  "token": "4f9d2e7b8a1c3d5e6f7a8b9c0d1e2f3a4b5c6d7e",
  "user_id": 2,
  "username": "techcorp_hr",
  "role": "employer"
}
```

### Admin Stats Response (`GET /api/stats/`)
*Headers: `Authorization: Token <admin_token>`*
```json
{
  "total_jobs": 12,
  "total_applications": 38,
  "applications_per_status": {
    "applied": 15,
    "reviewed": 8,
    "shortlisted": 7,
    "rejected": 5,
    "hired": 3
  }
}
```

### User Notifications (`GET /api/notifications/`)
*Headers: `Authorization: Token <token>`*
```json
[
  {
    "id": 1,
    "message": "Your application status for Senior Backend Engineer has been updated to shortlisted.",
    "is_read": false,
    "created_at": "2026-11-19T08:20:00Z"
  }
]
```

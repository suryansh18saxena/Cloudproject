<div align="center">

# ☁️ CloudLabX

### *Master Cloud & Linux — Hands On.*

<br>

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Gemini](https://img.shields.io/badge/Gemini_AI-Powered-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Channels](https://img.shields.io/badge/WebSockets-Real_Time-10B981?style=for-the-badge&logo=socketdotio&logoColor=white)](https://channels.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-A855F7?style=for-the-badge)](LICENSE)

<br>

**CloudLabX** is a full-stack learning platform that lets students practice **Linux system administration** inside real Docker containers, deploy **AWS infrastructure** using Terraform, and prepare for **technical interviews** with an AI-powered coach — all from the browser.

<br>

[Getting Started](#-getting-started) · [Features](#-features) · [Architecture](#-architecture) · [Tech Stack](#-tech-stack) · [Setup Guide](#-complete-setup-guide) · [Environment Variables](#-environment-variables) · [Contributing](#-contributing)

---

</div>

<br>

## 📸 Platform Overview

| Module | What It Does |
|--------|-------------|
| 🖥️ **Linux Terminal Labs** | Spin up isolated Docker containers and solve hands-on Linux challenges with a real browser-based terminal |
| ☁️ **AWS Cloud Labs** | Launch EC2 instances, create S3 buckets, build VPC networks — Terraform provisions temporary IAM users and validates your work via Boto3 |
| 🤖 **AI Interview Prep** | Practice technical interviews with Google Gemini AI — get real-time feedback, scoring, and a detailed performance report |
| 📊 **Student Dashboard** | Track completed labs, scores, streaks, and performance trends at a glance |
| 👨‍🏫 **Teacher Dashboard** | Monitor all students, view individual reports, track activity logs, and create teacher accounts |
| 📚 **Study Materials** | Pre-lab reading with structured sections, code examples, key takeaways, and hands-on guides |

<br>

---

## ✨ Features

### 🖥️ Linux Terminal Labs
> Interactive, containerized Linux environments in your browser.

- **Real Docker Containers** — Each lab session spins up an isolated Alpine Linux container with 40+ pre-installed tools (bash, vim, curl, nmap, htop, tcpdump, etc.)
- **Browser Terminal** — Low-latency terminal access powered by **xterm.js** over **WebSockets** (Django Channels + Daphne ASGI)
- **MCQ + Command Validation** — Every challenge has a theory question and a practical command task; both are validated for scoring
- **Live Command Tracking** — Your terminal command history is captured in real-time and verified against expected patterns (regex)
- **Timed Sessions** — Labs have configurable durations with countdown timers; expired sessions auto-cleanup containers
- **Difficulty Levels** — Beginner, Intermediate, and Advanced labs
- **Resource Limits** — Containers are sandboxed with 128 MB RAM, 50% CPU, and no network access for security

### ☁️ AWS Cloud Labs (Infrastructure as Code)
> Deploy real AWS resources and get scored automatically.

- **Terraform Provisioning** — Each lab session creates a temporary IAM user with scoped permissions via Terraform
- **Three Lab Types:**
  - **EC2 Launch Lab** — Launch instances, configure security groups with SSH access
  - **S3 Bucket Lab** — Create buckets, enable versioning, set bucket policies, block public access, upload objects
  - **VPC Networking Lab** — Create VPCs, subnets, internet gateways, route tables, and configure routing
- **Boto3 Validation** — Automated scoring checks your AWS account for completed tasks (CloudTrail + EC2/S3/VPC APIs)
- **Auto-Cleanup** — `terraform destroy` runs automatically when the lab ends, leaving no orphaned resources
- **Background Processing** — Terraform apply/destroy runs in background threads; the UI polls for status updates

### 🤖 AI Interview Prep
> Practice technical interviews with Google's Gemini AI.

- **10 Tech Roles** — Cloud Engineer, DevOps, Solutions Architect, SRE, Security Engineer, Data Engineer, Backend/Fullstack Developer, ML Engineer, Platform Engineer
- **5 Difficulty Levels** — Fresher → Junior → Mid-Level → Senior → Lead/Principal
- **Context-Aware Conversations** — The AI maintains full conversation history and adapts questions
- **Instant Feedback** — Each answer gets a rating (Excellent/Good/Average/Poor/Incorrect), a score out of 10, detailed feedback, and the ideal answer
- **Final Report** — End-of-interview analysis with strengths, areas for improvement, a hire/maybe/not-ready verdict, and study tips
- **Session History** — Browse and review past interview sessions

### 📊 Dashboards & Analytics

- **Student Dashboard** — Labs completed, average score, total hours, streaks, active sessions, recent activity feed, score chart
- **Teacher Dashboard** — Total/active students, overall averages, student-by-student stats, activity timeline, ability to create new teacher accounts
- **Student Reports** — Detailed per-student view: lab history, interview history, score trends, activity timeline

### 🔐 Authentication & Roles

- **User Registration & Login** — Custom signup/login views with validation
- **Role-Based Access** — Students and Teachers have separate dashboards and permissions
- **Activity Logging** — Every login, lab start/end, and interview start/end is recorded in `StudentActivityLog`
- **Auto Profile Creation** — `UserProfile` is automatically created via Django signals on user registration

<br>

---

## 🏗️ Architecture

```
CloudLabX/
├── Cloud_Project/          # Django project settings, ASGI/WSGI, root URL config
│   ├── settings.py         # Installed apps, channels, Q cluster, DB, auth
│   ├── asgi.py             # ASGI app with WebSocket routing (Daphne)
│   ├── urls.py             # Root URL patterns → home, account, dashboard, Lab, interview, linux-labs
│   └── .env                # Environment variables (secrets — not committed)
│
├── home/                   # Landing page app
│   └── views.py            # Renders the public home page
│
├── account/                # Authentication & user profiles
│   ├── models.py           # UserProfile (stats, streaks), StudentActivityLog
│   ├── views.py            # signup, login, logout views
│   └── decorators.py       # @teacher_required decorator
│
├── dashboard/              # Student & teacher dashboards
│   ├── views.py            # dashboard(), teacher_dashboard(), student_profile(), create_teacher()
│   └── signals.py          # Auto-update profile stats on lab completion
│
├── Lab/                    # AWS Cloud Labs (EC2, S3, VPC)
│   ├── models.py           # Lab, LabSession, LabActivity, LabScore, StudyMaterial, StudySection
│   ├── views.py            # lab_detail, start_lab, submit_lab, end_lab, study_material_hub
│   ├── validators.py       # Boto3 validation: EC2, S3, VPC task checkers
│   └── tasks.py            # Background Terraform apply/destroy functions
│
├── interview/              # AI Interview Prep
│   ├── models.py           # InterviewSession, InterviewMessage
│   └── views.py            # start_interview, send_answer, end_interview, session_history
│
├── linux_labs/             # Linux Terminal Labs
│   ├── models.py           # TerminalLab, TerminalChallenge, TerminalLabSession, ChallengeAttempt
│   ├── views.py            # labs_hub, lab_detail, start_lab, submit_answer, finish_lab, end_lab
│   ├── consumers.py        # WebSocket consumer — bridges xterm.js ↔ Docker PTY
│   ├── routing.py          # WebSocket URL patterns
│   └── management/commands/seed_linux_labs.py  # Django command to seed lab data
│
├── docker/
│   └── Dockerfile.linux_lab  # Alpine 3.19 image with 40+ sysadmin tools
│
├── Terraform/              # IaC configs for AWS labs
│   ├── IAM/                # IAM user + policy + login profile (EC2 lab)
│   ├── S3/                 # IAM user + S3 permissions
│   └── VPC/                # IAM user + VPC/EC2 permissions
│
├── templates/              # Django HTML templates
│   ├── base.html           # Base layout with navigation, glassmorphism UI
│   ├── home/               # Landing page
│   ├── account/            # Login & signup pages
│   ├── dashboard/          # Student dashboard, teacher dashboard, student report
│   ├── lab/                # EC2, S3, VPC lab pages + study material pages
│   ├── interview/          # Interview chatbot + recent sessions
│   └── linux_labs/         # Terminal lab hub + split-view lab environment
│
├── .github/workflows/
│   └── deploy.yml          # CI/CD: auto-deploy to EC2 on push to main
│
├── manage.py               # Django management CLI
├── requirements.txt        # Python dependencies
├── seed_lab.py             # Seed AWS lab data
├── seed_study_materials.py # Seed study material content
├── build_templates.py      # Template builder utility
└── setup.md                # Legacy setup notes
```

### Data Flow

```
┌──────────────┐     HTTP/WS      ┌──────────────────┐      Docker API       ┌──────────────────┐
│   Browser    │ ◄──────────────► │   Daphne (ASGI)  │ ◄──────────────────► │  Docker Containers│
│  xterm.js    │                  │  Django Channels  │                      │  (Alpine Linux)   │
└──────────────┘                  └──────────────────┘                      └──────────────────┘
                                         │
                                         │ ORM
                                         ▼
                                  ┌──────────────────┐
                                  │   SQLite / DB     │
                                  └──────────────────┘
                                         │
                              ┌──────────┼──────────┐
                              ▼          ▼          ▼
                        ┌──────────┐ ┌────────┐ ┌──────────┐
                        │ Terraform│ │Boto3   │ │Gemini AI │
                        │ (AWS IaC)│ │(Valid.)│ │(Interview│
                        └──────────┘ └────────┘ └──────────┘
```

<br>

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.10+, Django 4.2+ | Web framework, ORM, admin, authentication |
| **ASGI Server** | Daphne 4.1+ | Serves HTTP + WebSocket connections |
| **Real-Time** | Django Channels 4.0+ | WebSocket routing & consumers |
| **Containerization** | Docker (Python SDK 7.0+) | Isolated Linux lab environments |
| **Infrastructure** | Terraform | Provisions/destroys AWS resources per session |
| **Cloud** | AWS (Boto3) | EC2, S3, VPC, IAM, CloudTrail integration |
| **AI** | Google Gemini 2.5 Flash | AI interview chatbot |
| **Frontend** | Vanilla JS, CSS (Glassmorphism) | No framework — custom UI with animations |
| **Terminal** | xterm.js | Browser-based terminal emulator |
| **Task Queue** | Django-Q2 | Background task processing (ORM-based) |
| **Database** | SQLite (dev) | Default development database |
| **CI/CD** | GitHub Actions | Auto-deploy to EC2 on push to `main` |

<br>

---

## 🚀 Complete Setup Guide

### 📋 Prerequisites

Before you begin, make sure you have the following installed:

| Tool | Version | Required For | Installation |
|------|---------|-------------|-------------|
| **Python** | 3.10+ | Core application | [python.org](https://www.python.org/downloads/) |
| **pip** | Latest | Package management | Comes with Python |
| **Docker Desktop** | Latest | Linux Terminal Labs | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/downloads) |
| **Terraform** | 1.5+ | AWS Cloud Labs (optional) | [terraform.io](https://developer.hashicorp.com/terraform/downloads) |
| **AWS CLI** | v2 | AWS Cloud Labs (optional) | [aws.amazon.com/cli](https://aws.amazon.com/cli/) |

> [!NOTE]
> Docker Desktop must be **running** before starting Linux Terminal Labs. Terraform and AWS CLI are only needed if you plan to use the AWS Cloud Labs.

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/suryansh18saxena/Cloudproject.git
cd Cloudproject
```

---

### Step 2: Create a Virtual Environment

<details>
<summary><strong>🪟 Windows (PowerShell)</strong></summary>

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If you get an execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

</details>

<details>
<summary><strong>🪟 Windows (Command Prompt)</strong></summary>

```cmd
python -m venv .venv
.venv\Scripts\activate
```

</details>

<details>
<summary><strong>🐧 Linux / 🍎 macOS</strong></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
```

</details>

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
| Package | Purpose |
|---------|---------|
| `django>=4.2` | Web framework |
| `daphne>=4.1.0` | ASGI server for WebSocket support |
| `channels>=4.0.0` | Django Channels (WebSocket framework) |
| `docker>=7.0.0` | Docker SDK for Python (Linux labs) |
| `boto3` | AWS SDK for Python (cloud lab validation) |
| `google-generativeai` | Google Gemini AI SDK (interview chatbot) |
| `django-q2` | Background task queue |
| `python-dotenv` | Environment variable loading |
| `requests` | HTTP requests library |

---

### Step 4: Configure Environment Variables

Create a `.env` file inside the `Cloud_Project/` directory (the Django project folder, not the repo root):

```bash
# Cloud_Project/.env

# Django secret key (generate your own for production)
DJANGO_SECRET_KEY='your-secret-key-here'

# Google Gemini API key (required for AI Interview Prep)
GEMINI_API_KEY='your-gemini-api-key'

# AWS credentials (required for AWS Cloud Labs)
AWS_ACCESS_KEY_ID='your-aws-access-key'
AWS_SECRET_ACCESS_KEY='your-aws-secret-key'
```

> [!IMPORTANT]
> **Get your API keys:**
> - **Gemini API Key**: Go to [Google AI Studio](https://aistudio.google.com/apikey) → Create API Key
> - **AWS Credentials**: Go to AWS Console → IAM → Create a user with programmatic access and appropriate permissions (EC2, S3, VPC, IAM, CloudTrail)

> [!CAUTION]
> Never commit your `.env` file to version control. It is already listed in `.gitignore`.

---

### Step 5: Run Database Migrations

```bash
python manage.py migrate
```

This creates all the required tables in the SQLite database (`db.sqlite3`).

---

### Step 6: Seed Lab Data

```bash
# Seed Linux Terminal Lab challenges (5 labs with multi-step challenges)
python manage.py seed_linux_labs

# Seed AWS Cloud Lab definitions (optional — for EC2, S3, VPC labs)
python seed_lab.py

# Seed study materials (optional — pre-lab reading content)
python seed_study_materials.py
```

---

### Step 7: Build the Docker Image (for Linux Labs)

```bash
docker build -t cloudlabx-linux-lab:latest -f docker/Dockerfile.linux_lab .
```

> [!NOTE]
> This builds an Alpine Linux image with 40+ sysadmin tools (bash, vim, curl, nmap, htop, tcpdump, etc.). It only needs to be done once.

---

### Step 8: Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

Access the Django admin at `http://127.0.0.1:8000/admin/` to manage labs, users, and data.

---

### Step 9: Start the Application

You need **two terminal windows** (both with the virtual environment activated):

**Terminal 1 — Django-Q Background Worker:**
```bash
python manage.py qcluster
```

**Terminal 2 — Daphne ASGI Server:**
```bash
daphne -b 127.0.0.1 -p 8000 Cloud_Project.asgi:application
```

> [!TIP]
> Use `daphne` instead of `python manage.py runserver` to get **WebSocket support** for the Linux Terminal Labs. The regular Django dev server does not support WebSockets.

---

### Step 10: Open in Browser

```
http://127.0.0.1:8000/
```

🎉 **You're all set!** Sign up for an account and start learning.

---

### Step 11: Initialize Terraform (for AWS Labs)

If you want to use AWS Cloud Labs, initialize Terraform in each lab directory:

```bash
cd Terraform/IAM && terraform init
cd ../S3  && terraform init
cd ../VPC && terraform init
```

> [!WARNING]
> AWS Cloud Labs provision **real AWS resources** that may incur charges. The platform auto-destroys resources when labs end, but always verify cleanup in your AWS Console.

<br>

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SECRET_KEY` | ✅ Yes | Django secret key for cryptographic signing |
| `GEMINI_API_KEY` | ✅ For interviews | Google Gemini API key for the AI interview chatbot |
| `AWS_ACCESS_KEY_ID` | ✅ For AWS labs | AWS access key for Terraform and Boto3 |
| `AWS_SECRET_ACCESS_KEY` | ✅ For AWS labs | AWS secret key for Terraform and Boto3 |
| `AWS_DEFAULT_REGION` | ❌ Optional | AWS region (defaults to `us-east-1`) |

<br>

---

## 📁 Django Apps Breakdown

| App | URL Prefix | Key Models | Description |
|-----|-----------|------------|-------------|
| `home` | `/` | — | Public landing page |
| `account` | `/account/` | `UserProfile`, `StudentActivityLog` | Auth (signup, login, logout), user profiles, activity logging |
| `dashboard` | `/dashboard/` | — | Student & teacher dashboards, student reports |
| `Lab` | `/Lab/` | `Lab`, `LabSession`, `LabActivity`, `LabScore`, `StudyMaterial`, `StudySection` | AWS cloud labs with Terraform + Boto3 validation |
| `interview` | `/interview/` | `InterviewSession`, `InterviewMessage` | AI-powered mock interview chatbot |
| `linux_labs` | `/linux-labs/` | `TerminalLab`, `TerminalChallenge`, `TerminalLabSession`, `ChallengeAttempt` | Docker-based Linux terminal labs |

<br>

---

## 🔄 CI/CD Pipeline

The project includes a **GitHub Actions** workflow (`.github/workflows/deploy.yml`) that auto-deploys to an EC2 instance on every push to `main`:

```
Push to main → Checkout code → SSH into EC2 → git pull → pip install →
migrate → collectstatic → restart Daphne → restart Django-Q → reload Nginx
```

**Required GitHub Secrets:**

| Secret | Description |
|--------|-------------|
| `EC2_HOST` | Public IP or hostname of your EC2 instance |
| `EC2_USER` | SSH username (e.g., `ubuntu`) |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |

<br>

---

## 🧪 Running in Development vs Production

| Aspect | Development | Production |
|--------|------------|------------|
| **Server** | `daphne -b 127.0.0.1 -p 8000` | Daphne behind Nginx reverse proxy |
| **Database** | SQLite | PostgreSQL / MySQL recommended |
| **Channel Layer** | `InMemoryChannelLayer` | Redis (`channels_redis`) |
| **Debug** | `DEBUG = True` | `DEBUG = False` |
| **Static Files** | Django serves directly | `collectstatic` + Nginx |
| **Workers** | `python manage.py qcluster` | systemd service for Django-Q |
| **Docker** | Docker Desktop | Docker Engine |

<br>

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use Django conventions for models, views, and URLs
- Keep templates organized under `templates/<app_name>/`

<br>

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<br>

---

<div align="center">

### ⭐ Star this repo if CloudLabX helped you learn!

Built with ❤️ by the **CloudLabX Team**

<br>

[![Django](https://img.shields.io/badge/Made_with-Django-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Powered_by-Docker-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![Gemini](https://img.shields.io/badge/AI_by-Gemini-4285F4?style=flat-square&logo=googlegemini)](https://ai.google.dev/)

</div>

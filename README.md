# 🚀 CloudLabX - Master Cloud & Linux with Hands-on Labs

<div align="center">
  <img src="https://img.shields.io/badge/Platform-CloudLabX-06b6d4?style=for-the-badge&logo=rocket" alt="CloudLabX">
  <img src="https://img.shields.io/badge/Stack-Django%20%7C%20Docker%20%7C%20Terraform-10b981?style=for-the-badge" alt="Stack">
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License">
</div>

---

## 🌟 Overview

**CloudLabX** is a next-generation learning platform designed to bridge the gap between theory and practice. Whether you are prepping for a sysadmin role or mastering AWS infrastructure, CloudLabX provides real-world environments right in your browser.

---

## ✨ Key Features

### 🖥️ Linux Terminal Labs
Dive into interactive Linux challenges powered by isolated **Docker containers**.
- **Real-time Terminal**: Low-latency terminal access via WebSockets (`xterm.js`).
- **Live Verification**: Command-line history tracking with instant validation for tasks.
- **Dynamic Scenarios**: Practice everything from log analysis to Apache server deployment.

### 🤖 AI Interview Prep
Get ready for your dream job with our integrated AI coach.
- **Gemini-Powered**: Realistic technical interviews powered by Google's Gemini AI.
- **Context-Aware**: Tailored questions based on your specialized skills.

### 🏗️ Infrastructure as Code (IaC)
Master AWS by deploying actual resources using **Terraform**.
- **VPC & S3 Labs**: Automated provisioning and cleanup of AWS environments.
- **Boto3 Integration**: Secure validation of your AWS infrastructure.

---

## 🛠️ Tech Stack

- **Backend**: Python / Django (Daphne ASGI)
- **Real-time**: Django Channels / WebSockets
- **Virtualization**: Docker (Alpine Linux)
- **Infrastructure**: Terraform / AWS SDK (Boto3)
- **Frontend**: Vanilla JS / CSS (Glassmorphism UI) / xterm.js
- **AI**: Google Gemini API

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.10+
- Docker Desktop (Running)
- Terraform (Optional, for AWS labs)

### Installation

1. **Clone the Repo**
   ```bash
   git clone https://github.com/suryansh18saxena/Cloudproject.git
   cd Cloudproject
   ```

2. **Virtual Environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   ```

3. **Install Deps**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations & Seed**
   ```bash
   python manage.py migrate
   python manage.py seed_linux_labs
   ```

5. **Start Server (Daphne for WebSockets)**
   ```bash
   daphne Cloud_Project.asgi:application
   ```

---

## 📸 Screenshots

*(Add your screenshots here to make it truly aesthetic!)*

> [!TIP]
> Use the **End Lab** button to properly clean up Docker resources and maintain system performance.

---

<div align="center">
  <sub>Built with ❤️ by the CloudLabX Team</sub>
</div>

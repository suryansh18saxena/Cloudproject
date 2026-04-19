# Setup Instructions for Cloud Project

## Prerequisites
- Python 3.8+
- Terraform (for infrastructure deployment)
- AWS CLI (configured with valid credentials)

## Environment Setup

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd Cloud_Project
   ```

2. **Create and activate a virtual environment:**
   - On Windows (Command Prompt):
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - On Linux/macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   - Ensure you have a `.env` file set up if the project relies on one. 
   - You might need to set your `GEMINI_API_KEY` for the interview chatbot component.
   - Ensure AWS credentials for Boto3/Terraform are configured correctly on your system.

## Running the Application

1. **Apply Database Migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Seed Initial Data (optional):**
   ```bash
   python seed_lab.py
   ```

3. **Start the Django Q Service (Background Tasks):**
   - Open a new terminal window, activate the virtual environment, and run:
     ```bash
     python manage.py qcluster
     ```

4. **Start the Django Development Server:**
   - Return to your main terminal window and run:
     ```bash
     python manage.py runserver
     ```

5. **Access the application:**
   - Open your browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

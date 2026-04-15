import subprocess
import os
import json
from datetime import timedelta
from django.utils import timezone
from .models import LabSession

def provision_lab_task(session_id, tf_dir):
    try:
        session = LabSession.objects.get(id=session_id)
        my_env = os.environ.copy()
        
        # Pass student_id safely if expected in terraform
        username = session.user.username
        
        # 1. Terraform Init
        subprocess.run(
            ["terraform", "init"],
            cwd=tf_dir, check=True, capture_output=True, env=my_env
        )

        # 2. Terraform Apply
        # Applying var student_id for tracking and tagging logic (Step 1 requirement)
        subprocess.run(
            ["terraform", "apply", "-auto-approve", f"-var=student_id={username}"],
            cwd=tf_dir, check=True, capture_output=True, env=my_env
        )

        session.terraform_state = 'applied'
        session.save()

        # 3. Get credentials
        output_result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=tf_dir, capture_output=True, text=True
        )
        tf_outputs = json.loads(output_result.stdout) if output_result.stdout.strip() else {}

        iam_user_name = tf_outputs.get("iam_user_name", {}).get("value", "")
        console_password = tf_outputs.get("console_password", {}).get("value", "")
        console_login_link = tf_outputs.get("console_login_link", {}).get("value", "")

        now = timezone.now()
        session.iam_user_name = iam_user_name
        session.console_password = console_password
        session.console_login_link = console_login_link
        session.credentials_received_at = now
        session.timer_expires_at = now + timedelta(minutes=session.lab.duration_minutes)
        session.status = 'active'
        session.save()
        
    except subprocess.CalledProcessError as e:
        session.terraform_state = 'error'
        session.status = 'ended'
        session.save()
        print(f"Terraform Error: {e.stderr}")
    except Exception as e:
        if 'session' in locals():
            session.terraform_state = 'error'
            session.status = 'ended'
            session.save()
        print(f"Task Exception: {e}")

def destroy_lab_task(session_id, tf_dir):
    try:
        session = LabSession.objects.get(id=session_id)
        username = session.user.username
        
        subprocess.run(
            ["terraform", "destroy", "-auto-approve", f"-var=student_id={username}"],
            cwd=tf_dir, check=True, capture_output=True
        )

        session.status = 'ended'
        session.ended_at = timezone.now()
        session.terraform_state = 'destroyed'
        session.save()
        
        # Update user stats
        from .views import _update_user_stats
        _update_user_stats(session.user)
        
    except subprocess.CalledProcessError as e:
        session.terraform_state = 'error'
        session.status = 'ended'
        session.save()
        print(f"Destroy Error: {e.stderr}")
    except Exception as e:
        session.terraform_state = 'error'
        session.status = 'ended'
        session.save()
        print(f"Destroy Task Exception: {e}")

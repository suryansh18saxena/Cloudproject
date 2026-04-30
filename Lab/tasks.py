import subprocess
import os
import json
import logging
from datetime import timedelta
from django.utils import timezone
from .models import LabSession

logger = logging.getLogger(__name__)


def _run_tf(cmd, cwd, session_id):
    """Run a terraform command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per command
        )
        if result.returncode != 0:
            logger.error(
                "[Session %s] Terraform command %s failed.\nSTDOUT: %s\nSTDERR: %s",
                session_id, cmd, result.stdout, result.stderr
            )
            return False, result.stdout, result.stderr
        return True, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error("[Session %s] Terraform command %s timed out after 5 minutes.", session_id, cmd)
        return False, "", "Timeout: Terraform command exceeded 5 minutes."
    except Exception as e:
        logger.error("[Session %s] Unexpected error running %s: %s", session_id, cmd, e)
        return False, "", str(e)


def provision_lab_task(session_id, tf_dir):
    """
    Background task: run Terraform init (if needed) + apply, then update session
    with credentials so the frontend can proceed.
    """
    session = None
    try:
        session = LabSession.objects.get(id=session_id)
        username = session.user.username

        # ── Step 1: terraform init (only if .terraform folder is missing) ──
        tf_folder = os.path.join(tf_dir, ".terraform")
        if not os.path.exists(tf_folder):
            logger.info("[Session %s] Running terraform init in %s", session_id, tf_dir)
            ok, out, err = _run_tf(["terraform", "init", "-no-color"], tf_dir, session_id)
            if not ok:
                raise RuntimeError(f"terraform init failed:\n{err}")

        # ── Step 2: terraform apply ──
        logger.info("[Session %s] Running terraform apply for user '%s'", session_id, username)
        ok, out, err = _run_tf(
            ["terraform", "apply", "-auto-approve", f"-var=student_id={username}", "-no-color"],
            tf_dir, session_id
        )
        if not ok:
            raise RuntimeError(f"terraform apply failed:\n{err}")

        session.terraform_state = 'applied'
        session.save()

        # ── Step 3: Read outputs ──
        ok, out, err = _run_tf(
            ["terraform", "output", "-json"],
            tf_dir, session_id
        )
        tf_outputs = {}
        if ok and out.strip():
            try:
                tf_outputs = json.loads(out)
            except json.JSONDecodeError:
                logger.warning("[Session %s] Could not parse terraform output JSON: %s", session_id, out)

        iam_user_name     = tf_outputs.get("iam_user_name",     {}).get("value", "")
        console_password  = tf_outputs.get("console_password",  {}).get("value", "")
        console_login_link = tf_outputs.get("console_login_link", {}).get("value", "")

        now = timezone.now()
        session.iam_user_name      = iam_user_name
        session.console_password   = console_password
        session.console_login_link = console_login_link
        session.credentials_received_at = now
        session.timer_expires_at   = now + timedelta(minutes=session.lab.duration_minutes)
        session.status             = 'active'
        session.save()

        logger.info("[Session %s] Provisioning complete. IAM user: %s", session_id, iam_user_name)

    except Exception as e:
        logger.error("[Session %s] provision_lab_task failed: %s", session_id, e, exc_info=True)
        if session is not None:
            try:
                session.terraform_state = 'error'
                session.status = 'ended'
                session.save()
            except Exception:
                pass


def destroy_lab_task(session_id, tf_dir):
    """
    Background task: run terraform destroy to clean up AWS resources,
    then mark session as ended.
    """
    session = None
    try:
        session = LabSession.objects.get(id=session_id)
        username = session.user.username

        logger.info("[Session %s] Running terraform destroy for user '%s'", session_id, username)
        ok, out, err = _run_tf(
            ["terraform", "destroy", "-auto-approve", f"-var=student_id={username}", "-no-color"],
            tf_dir, session_id
        )
        if not ok:
            logger.error("[Session %s] terraform destroy failed: %s", session_id, err)
            # Still mark as ended so the UI resets
            session.terraform_state = 'error'
        else:
            session.terraform_state = 'destroyed'

        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save()

        logger.info("[Session %s] Destroy complete.", session_id)

        # Update user stats
        from .views import _update_user_stats
        _update_user_stats(session.user)

    except Exception as e:
        logger.error("[Session %s] destroy_lab_task failed: %s", session_id, e, exc_info=True)
        if session is not None:
            try:
                session.terraform_state = 'error'
                session.status = 'ended'
                session.ended_at = timezone.now()
                session.save()
            except Exception:
                pass

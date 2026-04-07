import os
import json
import subprocess
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Lab, LabSession, LabActivity, LabScore
from .validators import validate_all_tasks, calculate_score


# Terraform directory
TF_DIR = os.path.join(settings.BASE_DIR, 'Terraform', 'IAM')


@login_required
def ec2_lab(request):
    """Render the EC2 lab page with session context."""
    lab = Lab.objects.filter(slug='ec2-launch-lab').first()

    # Check for an active session
    active_session = None
    if lab:
        active_session = LabSession.objects.filter(
            user=request.user,
            lab=lab,
            status__in=['provisioning', 'active']
        ).first()

        # Check if the session timer has expired
        if active_session and active_session.is_expired:
            active_session.status = 'expired'
            active_session.ended_at = timezone.now()
            active_session.save()
            active_session = None

    context = {
        'lab': lab,
        'session': active_session,
    }
    return render(request, 'lab/EC2_lab.html', context)


@login_required
@require_POST
def start_lab(request):

    
    """Start a new lab session: Terraform apply → credentials → timer starts."""
    try:
        lab = Lab.objects.filter(slug='ec2-launch-lab').first()
        if not lab:
            return JsonResponse({'status': 'error', 'message': 'Lab not found. Create it in admin first.'})

        # Check if user already has an active session
        existing = LabSession.objects.filter(
            user=request.user,
            lab=lab,
            status__in=['provisioning', 'active']
        ).first()

        if existing:
            if existing.status == 'active' and not existing.is_expired:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Lab already active.',
                    'credentials': {
                        'iam_user_name': existing.iam_user_name,
                        'console_password': existing.console_password,
                        'console_login_link': existing.console_login_link,
                    },
                    'timer_expires_at': existing.timer_expires_at.isoformat() if existing.timer_expires_at else None,
                    'session_id': existing.id,
                })
            elif existing.is_expired:
                existing.status = 'expired'
                existing.ended_at = timezone.now()
                existing.save()

        # Create new session
        session = LabSession.objects.create(
            user=request.user,
            lab=lab,
            status='provisioning',
            terraform_state='applying',
        )
        my_env = os.environ.copy()
        # 1. Terraform Init
        subprocess.run(
            ["terraform", "init"],
            cwd=TF_DIR, check=True, capture_output=True, env=my_env
        )

        # 2. Terraform Apply
        subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            cwd=TF_DIR, check=True, capture_output=True, env=my_env
        )

        session.terraform_state = 'applied'
        session.save()

        # 3. Get credentials from Terraform output
        output_result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=TF_DIR, capture_output=True, text=True
        )
        tf_outputs = json.loads(output_result.stdout)

        iam_user_name = tf_outputs.get("iam_user_name", {}).get("value", "")
        console_password = tf_outputs.get("console_password", {}).get("value", "")
        console_login_link = tf_outputs.get("console_login_link", {}).get("value", "")

        # 4. Update session with credentials and start timer
        now = timezone.now()
        session.iam_user_name = iam_user_name
        session.console_password = console_password
        session.console_login_link = console_login_link
        session.credentials_received_at = now
        session.timer_expires_at = now + timedelta(minutes=lab.duration_minutes)
        session.status = 'active'
        session.save()

        return JsonResponse({
            'status': 'success',
            'credentials': {
                'iam_user_name': iam_user_name,
                'console_password': console_password,
                'console_login_link': console_login_link,
            },
            'timer_expires_at': session.timer_expires_at.isoformat(),
            'session_id': session.id,
        })

    except subprocess.CalledProcessError as e:
        # Mark session as error
        if 'session' in locals():
            session.terraform_state = 'error'
            session.status = 'ended'
            session.save()
        return JsonResponse({
            'status': 'error',
            'message': f'Terraform Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)}'
        })
    except Exception as e:
        if 'session' in locals():
            session.terraform_state = 'error'
            session.status = 'ended'
            session.save()
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def lab_status(request):
    """Return current lab session status (timer, credentials, etc.)."""
    lab = Lab.objects.filter(slug='ec2-launch-lab').first()
    if not lab:
        return JsonResponse({'status': 'no_lab'})

    session = LabSession.objects.filter(
        user=request.user,
        lab=lab,
        status__in=['provisioning', 'active', 'submitted']
    ).first()

    if not session:
        return JsonResponse({'status': 'no_session'})

    # Check for expiry
    if session.is_expired and session.status == 'active':
        session.status = 'expired'
        session.ended_at = timezone.now()
        session.save()
        return JsonResponse({
            'status': 'expired',
            'message': 'Lab session has expired.',
        })

    return JsonResponse({
        'status': session.status,
        'remaining_seconds': session.remaining_seconds,
        'timer_expires_at': session.timer_expires_at.isoformat() if session.timer_expires_at else None,
        'credentials': {
            'iam_user_name': session.iam_user_name,
            'console_password': session.console_password,
            'console_login_link': session.console_login_link,
        },
        'session_id': session.id,
    })


@login_required
@require_POST
def submit_lab(request):
    """Validate user's AWS work via boto3 and generate score."""
    try:
        lab = Lab.objects.filter(slug='ec2-launch-lab').first()
        if not lab:
            return JsonResponse({'status': 'error', 'message': 'Lab not found.'})

        # 👇 YAHAN CHANGE KARNA HAI 👇
        # Pehle yahan status='active' likha tha, usko status__in=['active', 'submitted'] karna hai
        session = LabSession.objects.filter(
            user=request.user,
            lab=lab,
            status__in=['active', 'submitted'] 
        ).first()

        if not session:
            return JsonResponse({'status': 'error', 'message': 'No active lab session found.'})

        # Run boto3 validations
        validation_results = validate_all_tasks(session.iam_user_name)

        # Save each task as LabActivity
        for result in validation_results:
            LabActivity.objects.create(
                session=session,
                task_name=result['task_name'],
                task_description=result.get('details', ''),
                is_passed=result['passed'],
                details=result,
            )

        # Calculate and save score
        score_data = calculate_score(validation_results)

        lab_score, created = LabScore.objects.update_or_create(
            session=session,
            defaults={
                'user': request.user,
                'lab': lab,
                'total_tasks': score_data['total_tasks'],
                'passed_tasks': score_data['passed_tasks'],
                'score_percentage': score_data['score_percentage'],
            }
        )

        # Update session status
        session.status = 'submitted'
        session.submitted_at = timezone.now()
        session.save()

        return JsonResponse({
            'status': 'success',
            'score': {
                'total_tasks': score_data['total_tasks'],
                'passed_tasks': score_data['passed_tasks'],
                'score_percentage': score_data['score_percentage'],
            },
            'tasks': validation_results,
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def end_lab(request):
    """End the lab: save score if not done, cleanup AWS resources, terraform destroy."""
    try:
        lab = Lab.objects.filter(slug='ec2-launch-lab').first()
        if not lab:
            return JsonResponse({'status': 'error', 'message': 'Lab not found.'})

        session = LabSession.objects.filter(
            user=request.user,
            lab=lab,
            status__in=['active', 'submitted', 'expired']
        ).first()

        if not session:
            return JsonResponse({'status': 'error', 'message': 'No lab session to end.'})

        # If not yet submitted, auto-submit first
        if session.status == 'active' or session.status == 'expired':
            try:
                validation_results = validate_all_tasks(session.iam_user_name)

                for result in validation_results:
                    LabActivity.objects.create(
                        session=session,
                        task_name=result['task_name'],
                        task_description=result.get('details', ''),
                        is_passed=result['passed'],
                        details=result,
                    )

                score_data = calculate_score(validation_results)
                LabScore.objects.update_or_create(
                    session=session,
                    defaults={
                        'user': request.user,
                        'lab': lab,
                        'total_tasks': score_data['total_tasks'],
                        'passed_tasks': score_data['passed_tasks'],
                        'score_percentage': score_data['score_percentage'],
                    }
                )
                session.submitted_at = timezone.now()
            except Exception:
                pass  # Continue with cleanup even if scoring fails

        # Update session state to destroying
        session.terraform_state = 'destroying'
        session.save()

        # Terraform Destroy (this also triggers cleanup_user.py via local-exec)
        subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=TF_DIR, check=True, capture_output=True
        )

        # Final session updates
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.terraform_state = 'destroyed'
        session.save()

        # Update user profile stats
        _update_user_stats(request.user)

        # Get final score for response
        final_score = None
        try:
            score = session.score
            final_score = {
                'total_tasks': score.total_tasks,
                'passed_tasks': score.passed_tasks,
                'score_percentage': score.score_percentage,
            }
        except LabScore.DoesNotExist:
            pass

        return JsonResponse({
            'status': 'success',
            'message': 'Lab ended. All resources cleaned up successfully.',
            'score': final_score,
        })

    except subprocess.CalledProcessError as e:
        if 'session' in locals():
            session.terraform_state = 'error'
            session.save()
        return JsonResponse({
            'status': 'error',
            'message': f'Destroy Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)}'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def _update_user_stats(user):
    """Update UserProfile stats after a lab is completed."""
    from account.models import UserProfile
    from datetime import date

    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Count completed labs
    completed_sessions = LabSession.objects.filter(user=user, status='ended')
    profile.total_labs_completed = completed_sessions.count()

    # Average score
    scores = LabScore.objects.filter(user=user)
    if scores.exists():
        total = sum(s.score_percentage for s in scores)
        profile.total_score = total
        profile.average_score = round(total / scores.count(), 1)

    # Streak calculation
    today = date.today()
    if profile.last_lab_date:
        delta = (today - profile.last_lab_date).days
        if delta <= 1:
            profile.current_streak += 1
        elif delta > 1:
            profile.current_streak = 1
    else:
        profile.current_streak = 1

    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
    profile.last_lab_date = today
    profile.save()

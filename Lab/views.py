import os
from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django_q.tasks import async_task
from .models import Lab, LabSession, LabActivity, LabScore, StudyMaterial
from .validators import validate_lab_tasks, calculate_score
from .tasks import provision_lab_task, destroy_lab_task

TEMPLATE_MAP = {
    'ec2-launch-lab': 'lab/EC2_lab.html',
    's3-bucket-lab': 'lab/s3_lab.html',
    'vpc-networking-lab': 'lab/vpc_lab.html'
}

def get_tf_dir(lab):
    base_path = os.path.abspath(settings.BASE_DIR)
    tf_path = os.path.abspath(os.path.join(base_path, *lab.terraform_dir.split('/')))
    if not tf_path.startswith(base_path):
        raise ValueError("Invalid terraform directory path")
    return tf_path

@login_required
def lab_detail(request, slug):
    """Render the lab page with session context."""
    lab = get_object_or_404(Lab, slug=slug)

    # Check for an active session
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
    template_name = TEMPLATE_MAP.get(lab.slug, 'lab/EC2_lab.html')
    return render(request, template_name, context)

@login_required
@require_POST
def start_lab(request, slug):
    """Start a new lab session: Terraform apply → credentials → timer starts."""
    try:
        lab = Lab.objects.filter(slug=slug).first()
        if not lab:
            return JsonResponse({'status': 'error', 'message': 'Lab not found.'})

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
        
        tf_dir = get_tf_dir(lab)
        
        # Enqueue background task
        async_task(provision_lab_task, session.id, tf_dir)

        return JsonResponse({
            'status': 'provisioning',
            'message': 'Lab is provisioning in background.',
            'session_id': session.id,
        })

    except Exception as e:
        session_obj = locals().get('session')
        if session_obj and hasattr(session_obj, 'terraform_state'):
            session_obj.terraform_state = 'error'
            session_obj.status = 'ended'
            session_obj.save()
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def lab_status(request, slug):
    """Return current lab session status (timer, credentials, etc.)."""
    lab = Lab.objects.filter(slug=slug).first()
    if not lab:
        return JsonResponse({'status': 'no_lab'})

    # Include 'ended' so we can detect the destroying→ended transition
    session = LabSession.objects.filter(
        user=request.user,
        lab=lab,
        status__in=['provisioning', 'active', 'submitted', 'ended']
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

    # If a background destroy is in progress, inform the frontend
    if session.terraform_state == 'destroying':
        return JsonResponse({'status': 'destroying'})

    # Session has ended (destroy completed) — tell frontend to reset
    if session.status == 'ended':
        score_data = None
        try:
            score = session.score
            score_data = {
                'total_tasks': score.total_tasks,
                'passed_tasks': score.passed_tasks,
                'score_percentage': score.score_percentage,
            }
        except Exception:
            pass
        return JsonResponse({
            'status': 'ended',
            'message': 'Lab resources destroyed. Ready to start again.',
            'score': score_data,
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
def submit_lab(request, slug):
    """Validate user's AWS work via boto3 and generate score."""
    try:
        lab = Lab.objects.filter(slug=slug).first()
        if not lab:
            return JsonResponse({'status': 'error', 'message': 'Lab not found.'})

        session = LabSession.objects.filter(
            user=request.user,
            lab=lab,
            status__in=['active', 'submitted'] 
        ).first()

        if not session:
            return JsonResponse({'status': 'error', 'message': 'No active lab session found.'})

        # Run boto3 validations based on the lab
        validation_results = validate_lab_tasks(lab.slug, session.iam_user_name)

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
def end_lab(request, slug):
    """End the lab: save score if not done, cleanup AWS resources, terraform destroy."""
    try:
        lab = Lab.objects.filter(slug=slug).first()
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
                validation_results = validate_lab_tasks(lab.slug, session.iam_user_name)

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
                pass

        # Update session state to destroying
        session.terraform_state = 'destroying'
        session.save()

        # Enqueue Terraform Destroy background task
        tf_dir = get_tf_dir(lab)
        async_task(destroy_lab_task, session.id, tf_dir)

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
            'status': 'destroying',
            'message': 'Lab resources are being destroyed in background.',
            'score': final_score,
        })

    except Exception as e:
        session_obj = locals().get('session')
        if session_obj and hasattr(session_obj, 'terraform_state'):
            session_obj.terraform_state = 'error'
            session_obj.save()
        return JsonResponse({'status': 'error', 'message': str(e)})


def _update_user_stats(user):
    """Update UserProfile stats after a lab is completed."""
    from account.models import UserProfile
    from datetime import date

    profile, _ = UserProfile.objects.get_or_create(user=user)

    completed_sessions = LabSession.objects.filter(user=user, status='ended')
    profile.total_labs_completed = completed_sessions.count()

    scores = LabScore.objects.filter(user=user)
    if scores.exists():
        total = sum(s.score_percentage for s in scores)
        profile.total_score = total
        profile.average_score = round(total / scores.count(), 1)

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


@login_required
def study_material_hub(request):
    """List all available study materials."""
    materials = StudyMaterial.objects.select_related('lab').all()
    context = {
        'materials': materials,
    }
    return render(request, 'lab/study_material_hub.html', context)


@login_required
def study_material_detail(request, slug):
    """Show detailed study material for a specific lab."""
    lab = get_object_or_404(Lab, slug=slug)
    try:
        material = lab.study_material
    except StudyMaterial.DoesNotExist:
        from django.http import Http404
        raise Http404("Study material not found for this lab.")

    sections = material.sections.all().order_by('order')

    context = {
        'lab': lab,
        'material': material,
        'sections': sections,
    }
    return render(request, 'lab/study_material_detail.html', context)

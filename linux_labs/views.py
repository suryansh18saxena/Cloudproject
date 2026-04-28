import re
import json
import docker

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from .models import TerminalLab, TerminalChallenge, TerminalLabSession, ChallengeAttempt


def _get_docker_client():
    """Get a Docker client instance."""
    return docker.from_env()


@login_required
def labs_hub(request):
    """Render the Linux Terminal Labs hub page."""
    labs = TerminalLab.objects.filter(is_active=True)

    # Get user's session data for each lab
    labs_data = []
    for lab in labs:
        last_session = TerminalLabSession.objects.filter(
            user=request.user, lab=lab
        ).first()

        best_session = TerminalLabSession.objects.filter(
            user=request.user, lab=lab, status='completed'
        ).order_by('-total_score').first()

        labs_data.append({
            'lab': lab,
            'last_session': last_session,
            'best_score': best_session.score_percentage if best_session else None,
            'attempts': TerminalLabSession.objects.filter(user=request.user, lab=lab).count(),
            'completed': TerminalLabSession.objects.filter(
                user=request.user, lab=lab, status='completed'
            ).exists(),
        })

    # Overall stats
    total_completed = TerminalLabSession.objects.filter(
        user=request.user, status='completed'
    ).count()
    completed_sessions = TerminalLabSession.objects.filter(
        user=request.user, status='completed'
    )
    avg_score = 0
    if completed_sessions.exists():
        avg_score = round(
            sum(s.score_percentage for s in completed_sessions) / completed_sessions.count(), 1
        )

    total_challenges_solved = ChallengeAttempt.objects.filter(
        session__user=request.user, is_mcq_correct=True, is_commands_correct=True
    ).count()

    context = {
        'labs_data': labs_data,
        'total_completed': total_completed,
        'avg_score': avg_score,
        'total_challenges_solved': total_challenges_solved,
    }
    return render(request, 'linux_labs/hub.html', context)


@login_required
def lab_detail(request, lab_id):
    """Render the split-view lab environment (MCQ + Terminal)."""
    lab = get_object_or_404(TerminalLab, id=lab_id, is_active=True)

    # Check for active session
    active_session = TerminalLabSession.objects.filter(
        user=request.user, lab=lab, status='active'
    ).first()

    # If session exists but timer has expired, auto-clean it so user can start fresh
    if active_session and active_session.is_expired:
        # Stop the container
        if active_session.container_id:
            try:
                client = _get_docker_client()
                container = client.containers.get(active_session.container_id)
                container.kill()
                container.remove(force=True)
            except Exception:
                pass
        active_session.status = 'expired'
        active_session.ended_at = timezone.now()
        active_session.save()
        active_session = None  # Allow starting a new session

    # If there's an active session, get the current challenge data for page refresh
    current_challenge_json = 'null'
    if active_session:
        current_challenge = TerminalChallenge.objects.filter(
            lab=lab, order=active_session.current_challenge_order
        ).first()
        if current_challenge:
            import json as json_mod
            current_challenge_json = json_mod.dumps({
                'order': current_challenge.order,
                'question_text': current_challenge.question_text,
                'option_a': current_challenge.option_a,
                'option_b': current_challenge.option_b,
                'option_c': current_challenge.option_c,
                'option_d': current_challenge.option_d,
                'points': current_challenge.points,
                'command_hint': current_challenge.command_hint,
            })

    context = {
        'lab': lab,
        'active_session': active_session,
        'challenges': lab.challenges.all(),
        'current_challenge_json': current_challenge_json,
    }
    return render(request, 'linux_labs/lab_environment.html', context)


@login_required
@require_POST
def start_lab(request, lab_id):
    """Start a new terminal lab session — spin up Docker container."""
    try:
        lab = get_object_or_404(TerminalLab, id=lab_id, is_active=True)

        # Abandon any existing active session for this lab
        old_sessions = TerminalLabSession.objects.filter(
            user=request.user, lab=lab, status='active'
        )
        for old in old_sessions:
            old.status = 'abandoned'
            old.ended_at = timezone.now()
            old.save()
            # Stop old container
            if old.container_id:
                try:
                    client = _get_docker_client()
                    container = client.containers.get(old.container_id)
                    container.stop(timeout=5)
                    container.remove(force=True)
                except Exception:
                    pass

        # Spin up a new Docker container
        client = _get_docker_client()
        container_name = f"linux_lab_{request.user.id}_{lab.id}_{int(timezone.now().timestamp())}"

        container = client.containers.run(
            lab.docker_image,
            detach=True,
            name=container_name,
            stdin_open=True,
            tty=True,
            mem_limit='128m',
            cpu_period=100000,
            cpu_quota=50000,  # 50% of one CPU
            network_mode='none',  # No network for security
            remove=False,
            labels={
                'cloudlabx': 'true',
                'user_id': str(request.user.id),
                'lab_id': str(lab.id),
            }
        )

        # Create session
        session = TerminalLabSession.objects.create(
            user=request.user,
            lab=lab,
            status='active',
            container_id=container.id,
            max_score=lab.total_points,
            timer_expires_at=timezone.now() + timedelta(minutes=lab.duration_minutes),
        )

        # Get first challenge
        first_challenge = lab.challenges.first()

        return JsonResponse({
            'status': 'success',
            'session_id': session.id,
            'container_id': container.id,
            'remaining_seconds': session.remaining_seconds,
            'challenge': {
                'order': first_challenge.order,
                'question_text': first_challenge.question_text,
                'option_a': first_challenge.option_a,
                'option_b': first_challenge.option_b,
                'option_c': first_challenge.option_c,
                'option_d': first_challenge.option_d,
                'points': first_challenge.points,
                'command_hint': first_challenge.command_hint,
            } if first_challenge else None,
            'total_challenges': lab.challenge_count,
        })

    except docker.errors.ImageNotFound:
        return JsonResponse({
            'status': 'error',
            'message': f'Docker image "{lab.docker_image}" not found. Please build it first.'
        })
    except docker.errors.APIError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Docker error: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def submit_answer(request):
    """Validate MCQ answer + terminal commands for a challenge."""
    try:
        session_id = request.POST.get('session_id')
        challenge_order = int(request.POST.get('challenge_order', 0))
        selected_option = request.POST.get('selected_option', '').lower()
        command_history = json.loads(request.POST.get('command_history', '[]'))

        session = get_object_or_404(
            TerminalLabSession, id=session_id, user=request.user, status='active'
        )

        # Check if expired
        if session.is_expired:
            session.status = 'expired'
            session.ended_at = timezone.now()
            session.save()
            return JsonResponse({'status': 'error', 'message': 'Lab session has expired.'})

        challenge = get_object_or_404(
            TerminalChallenge, lab=session.lab, order=challenge_order
        )

        # Check if already attempted
        existing = ChallengeAttempt.objects.filter(session=session, challenge=challenge).first()
        if existing:
            return JsonResponse({
                'status': 'error',
                'message': 'This challenge has already been attempted.'
            })

        # Validate MCQ
        is_mcq_correct = selected_option == challenge.correct_option

        # Validate commands
        is_commands_correct = _validate_commands(command_history, challenge.expected_commands)

        # Calculate marks
        marks = 0
        feedback = ''
        if is_mcq_correct and is_commands_correct:
            marks = challenge.points
            feedback = '🎉 Perfect! Both your answer and commands are correct.'
        elif is_mcq_correct and not is_commands_correct:
            marks = challenge.points // 2  # Partial credit
            feedback = '✅ Correct answer, but the terminal commands were not quite right.'
        elif not is_mcq_correct and is_commands_correct:
            marks = challenge.points // 4  # Small credit for commands
            feedback = '❌ Wrong answer, but your terminal commands were on the right track.'
        else:
            marks = 0
            feedback = '❌ Both the answer and commands were incorrect.'

        # Save attempt
        ChallengeAttempt.objects.create(
            session=session,
            challenge=challenge,
            selected_option=selected_option,
            is_mcq_correct=is_mcq_correct,
            command_history=command_history,
            is_commands_correct=is_commands_correct,
            marks_awarded=marks,
            feedback=feedback,
        )

        # Update session score
        session.total_score += marks
        session.save()

        # Get next challenge
        next_challenge = TerminalChallenge.objects.filter(
            lab=session.lab, order__gt=challenge_order
        ).first()

        response_data = {
            'status': 'success',
            'is_mcq_correct': is_mcq_correct,
            'is_commands_correct': is_commands_correct,
            'marks_awarded': marks,
            'max_marks': challenge.points,
            'feedback': feedback,
            'explanation': challenge.explanation,
            'correct_option': challenge.correct_option,
            'total_score': session.total_score,
            'max_score': session.max_score,
        }

        if next_challenge:
            response_data['next_challenge'] = {
                'order': next_challenge.order,
                'question_text': next_challenge.question_text,
                'option_a': next_challenge.option_a,
                'option_b': next_challenge.option_b,
                'option_c': next_challenge.option_c,
                'option_d': next_challenge.option_d,
                'points': next_challenge.points,
                'command_hint': next_challenge.command_hint,
            }
            session.current_challenge_order = next_challenge.order
            session.save()
        else:
            response_data['lab_complete'] = True

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def _validate_commands(command_history, expected_commands):
    """Check if the user's command history contains the expected commands."""
    if not expected_commands:
        return True

    # Join all commands into a single string for pattern matching
    all_commands = ' '.join(command_history).lower()

    for pattern in expected_commands:
        pattern_lower = pattern.lower()
        # Try regex match first
        try:
            if not re.search(pattern_lower, all_commands):
                return False
        except re.error:
            # Fall back to substring match
            if pattern_lower not in all_commands:
                return False
    return True


@login_required
@require_POST
def finish_lab(request):
    """End the lab session, stop Docker container, calculate final score."""
    try:
        session_id = request.POST.get('session_id')
        session = get_object_or_404(
            TerminalLabSession, id=session_id, user=request.user
        )

        # Allow finishing active or expired sessions (timer expiry triggers this)
        if session.status not in ('active', 'expired'):
            return JsonResponse({
                'status': 'error',
                'message': 'This lab session has already been completed.'
            })

        # Stop and remove Docker container
        if session.container_id:
            try:
                client = _get_docker_client()
                container = client.containers.get(session.container_id)
                container.kill()  # Force kill - faster than stop
                container.remove(force=True)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception:
                try:
                    client = _get_docker_client()
                    client.api.remove_container(session.container_id, force=True)
                except Exception:
                    pass

        # End session
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()

        # Get all attempts
        attempts = ChallengeAttempt.objects.filter(session=session).select_related('challenge')

        attempts_data = []
        for attempt in attempts:
            attempts_data.append({
                'question': attempt.challenge.question_text[:100],
                'order': attempt.challenge.order,
                'selected': attempt.selected_option,
                'correct': attempt.challenge.correct_option,
                'is_mcq_correct': attempt.is_mcq_correct,
                'is_commands_correct': attempt.is_commands_correct,
                'marks': attempt.marks_awarded,
                'max_marks': attempt.challenge.points,
                'feedback': attempt.feedback,
            })

        return JsonResponse({
            'status': 'success',
            'total_score': session.total_score,
            'max_score': session.max_score,
            'score_percentage': session.score_percentage,
            'duration_minutes': session.duration_minutes,
            'attempts': attempts_data,
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def lab_results(request, session_id):
    """View results of a completed terminal lab session."""
    session = get_object_or_404(
        TerminalLabSession, id=session_id, user=request.user
    )
    attempts = ChallengeAttempt.objects.filter(session=session).select_related('challenge')

    return JsonResponse({
        'status': 'success',
        'session': {
            'id': session.id,
            'lab': session.lab.title,
            'status': session.status,
            'total_score': session.total_score,
            'max_score': session.max_score,
            'score_percentage': session.score_percentage,
            'duration_minutes': session.duration_minutes,
            'started_at': session.started_at.strftime('%b %d, %Y %I:%M %p'),
        },
        'attempts': [{
            'question': a.challenge.question_text[:100],
            'order': a.challenge.order,
            'is_mcq_correct': a.is_mcq_correct,
            'is_commands_correct': a.is_commands_correct,
            'marks': a.marks_awarded,
            'max_marks': a.challenge.points,
        } for a in attempts],
    })


@login_required
@require_POST
def end_lab(request):
    """End lab and fully clean up — stop container, delete session and all attempts."""
    try:
        session_id = request.POST.get('session_id')
        if not session_id:
            return JsonResponse({'status': 'error', 'message': 'No session_id provided'})

        session = get_object_or_404(
            TerminalLabSession, id=session_id, user=request.user
        )

        # Stop and remove Docker container
        if session.container_id:
            try:
                client = _get_docker_client()
                container = client.containers.get(session.container_id)
                container.kill()  # Force kill — faster than stop
                container.remove(force=True)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception:
                try:
                    client = _get_docker_client()
                    client.api.remove_container(session.container_id, force=True)
                except Exception:
                    pass

        # Delete all challenge attempts for this session
        ChallengeAttempt.objects.filter(session=session).delete()

        # Delete the session itself
        session.delete()

        return JsonResponse({
            'status': 'success',
            'message': 'Lab ended. All data and container have been cleaned up.',
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


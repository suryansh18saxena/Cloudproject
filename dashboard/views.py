from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from Lab.models import Lab, LabSession, LabActivity, LabScore
from interview.models import InterviewSession
from account.models import UserProfile, StudentActivityLog
from account.decorators import teacher_required


@login_required
def dashboard(request):
    """Dashboard with real user data from the database."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Stats
    completed_count = LabSession.objects.filter(user=user, status='ended').count()
    scores = LabScore.objects.filter(user=user)
    avg_score = 0
    if scores.exists():
        avg_score = round(sum(s.score_percentage for s in scores) / scores.count(), 1)

    total_hours = 0
    ended_sessions = LabSession.objects.filter(user=user, status='ended', ended_at__isnull=False)
    for s in ended_sessions:
        if s.started_at and s.ended_at:
            delta = s.ended_at - s.started_at
            total_hours += delta.total_seconds() / 3600
    total_hours = round(total_hours, 1)

    # Active session
    active_session = LabSession.objects.filter(
        user=user,
        status__in=['provisioning', 'active']
    ).first()

    if active_session and active_session.is_expired:
        active_session.status = 'expired'
        active_session.ended_at = timezone.now()
        active_session.save()
        active_session = None

    # Available labs
    available_labs = Lab.objects.filter(is_active=True)

    # Recent activity (last 10)
    recent_activities = LabActivity.objects.filter(
        session__user=user
    ).select_related('session', 'session__lab').order_by('-checked_at')[:10]

    # Recent scores for chart
    recent_scores = LabScore.objects.filter(user=user).order_by('-scored_at')[:6]

    context = {
        'profile': profile,
        'completed_count': completed_count,
        'avg_score': avg_score,
        'total_hours': total_hours,
        'current_streak': profile.current_streak,
        'active_session': active_session,
        'available_labs': available_labs,
        'recent_activities': recent_activities,
        'recent_scores': recent_scores,
    }
    return render(request, 'dashboard/dashboard.html', context)


@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard — overview of all students, labs, and activity."""
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)

    # ── Aggregate stats ───────────────────────────────────────────
    all_students = User.objects.filter(profile__is_teacher=False)
    total_students = all_students.count()
    total_labs = Lab.objects.filter(is_active=True).count()

    # Active students = students who have at least one activity log in last 7 days
    active_student_ids = StudentActivityLog.objects.filter(
        timestamp__gte=seven_days_ago,
        user__profile__is_teacher=False,
    ).values_list('user_id', flat=True).distinct()
    active_students = len(active_student_ids)

    # Overall average score across all students
    all_scores = LabScore.objects.all()
    overall_avg = 0
    if all_scores.exists():
        overall_avg = round(sum(s.score_percentage for s in all_scores) / all_scores.count(), 1)

    # Total interviews
    total_interviews = InterviewSession.objects.filter(status='completed').count()

    # ── Student list with stats ───────────────────────────────────
    students_data = []
    for student in all_students.select_related('profile').order_by('-date_joined')[:50]:
        profile = getattr(student, 'profile', None)
        labs_done = LabSession.objects.filter(user=student, status='ended').count()
        interviews_done = InterviewSession.objects.filter(user=student, status='completed').count()

        scores = LabScore.objects.filter(user=student)
        avg_score = 0
        if scores.exists():
            avg_score = round(sum(s.score_percentage for s in scores) / scores.count(), 1)

        last_activity = StudentActivityLog.objects.filter(user=student).first()

        students_data.append({
            'user': student,
            'profile': profile,
            'labs_done': labs_done,
            'interviews_done': interviews_done,
            'avg_score': avg_score,
            'last_activity': last_activity,
            'is_active': student.id in active_student_ids,
        })

    # ── Recent activity feed (all students) ───────────────────────
    recent_logs = StudentActivityLog.objects.filter(
        user__profile__is_teacher=False,
    ).select_related('user').order_by('-timestamp')[:20]

    context = {
        'total_students': total_students,
        'total_labs': total_labs,
        'active_students': active_students,
        'overall_avg': overall_avg,
        'total_interviews': total_interviews,
        'students_data': students_data,
        'recent_logs': recent_logs,
        'profile': request.user.profile,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)


@teacher_required
def student_profile(request, student_id):
    """Detailed student report — labs, interviews, activity timeline."""
    student = get_object_or_404(User, id=student_id)
    student_profile = getattr(student, 'profile', None)

    # ── Lab history ───────────────────────────────────────────────
    lab_sessions = LabSession.objects.filter(user=student).select_related('lab').order_by('-started_at')[:20]
    lab_scores = LabScore.objects.filter(user=student).select_related('lab').order_by('-scored_at')

    total_labs = LabSession.objects.filter(user=student, status='ended').count()
    lab_avg = 0
    if lab_scores.exists():
        lab_avg = round(sum(s.score_percentage for s in lab_scores) / lab_scores.count(), 1)

    total_lab_hours = 0
    ended_sessions = LabSession.objects.filter(user=student, status='ended', ended_at__isnull=False)
    for s in ended_sessions:
        if s.started_at and s.ended_at:
            delta = s.ended_at - s.started_at
            total_lab_hours += delta.total_seconds() / 3600
    total_lab_hours = round(total_lab_hours, 1)

    # ── Interview history ─────────────────────────────────────────
    interview_sessions = InterviewSession.objects.filter(user=student).order_by('-started_at')[:20]
    completed_interviews = InterviewSession.objects.filter(user=student, status='completed')
    total_interviews = completed_interviews.count()
    interview_avg = 0
    if completed_interviews.exists():
        interview_avg = round(
            sum(s.overall_score for s in completed_interviews) / completed_interviews.count(), 1
        )

    # ── Activity timeline ─────────────────────────────────────────
    activity_logs = StudentActivityLog.objects.filter(user=student).order_by('-timestamp')[:30]

    # ── Score trend data for chart ────────────────────────────────
    score_trend = list(lab_scores.order_by('scored_at').values_list('score_percentage', flat=True))[:10]
    score_labels = []
    for s in lab_scores.order_by('scored_at')[:10]:
        score_labels.append(s.scored_at.strftime('%b %d'))

    context = {
        'student': student,
        'student_profile': student_profile,
        'lab_sessions': lab_sessions,
        'lab_scores': lab_scores,
        'total_labs': total_labs,
        'lab_avg': lab_avg,
        'total_lab_hours': total_lab_hours,
        'interview_sessions': interview_sessions,
        'total_interviews': total_interviews,
        'interview_avg': interview_avg,
        'activity_logs': activity_logs,
        'score_trend': score_trend,
        'score_labels': score_labels,
        'profile': request.user.profile,
    }
    return render(request, 'dashboard/student_report.html', context)


@teacher_required
def create_teacher(request):
    """Create a new teacher account from the teacher dashboard."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')

        # Validations
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('teacher_dashboard')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('teacher_dashboard')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('teacher_dashboard')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, f'Email "{email}" is already registered.')
            return redirect('teacher_dashboard')

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Set as teacher
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_teacher = True
        profile.save()

        messages.success(request, f'✅ Teacher account "{username}" created successfully!')
        return redirect('teacher_dashboard')

    # GET request — shouldn't happen, redirect back
    return redirect('teacher_dashboard')
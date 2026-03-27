from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from Lab.models import Lab, LabSession, LabActivity, LabScore
from account.models import UserProfile


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
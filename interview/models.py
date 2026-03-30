from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class InterviewSession(models.Model):
    """Tracks one interview practice session for a user."""

    ROLE_CHOICES = [
        ('cloud_engineer', 'Cloud Engineer'),
        ('devops_engineer', 'DevOps Engineer'),
        ('solutions_architect', 'Solutions Architect'),
        ('sre', 'Site Reliability Engineer'),
        ('cloud_security', 'Cloud Security Engineer'),
        ('data_engineer', 'Data Engineer'),
        ('backend_developer', 'Backend Developer'),
        ('fullstack_developer', 'Full Stack Developer'),
        ('ml_engineer', 'ML Engineer'),
        ('platform_engineer', 'Platform Engineer'),
    ]

    DIFFICULTY_CHOICES = [
        ('fresher', 'Fresher'),
        ('junior', 'Junior (1-2 yrs)'),
        ('mid', 'Mid-Level (3-5 yrs)'),
        ('senior', 'Senior (5+ yrs)'),
        ('lead', 'Lead / Principal'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='junior')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    overall_score = models.FloatField(default=0.0)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()} ({self.status})"

    @property
    def duration_minutes(self):
        end = self.ended_at or timezone.now()
        delta = end - self.started_at
        return round(delta.total_seconds() / 60, 1)

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)

    class Meta:
        ordering = ['-started_at']


class InterviewMessage(models.Model):
    """Individual message in an interview chat session."""

    SENDER_CHOICES = [
        ('bot', 'Bot'),
        ('user', 'User'),
    ]

    RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
        ('incorrect', 'Incorrect'),
    ]

    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()

    # For bot feedback messages
    is_question = models.BooleanField(default=False)
    is_feedback = models.BooleanField(default=False)
    answer_rating = models.CharField(max_length=20, choices=RATING_CHOICES, blank=True, default='')
    ideal_answer = models.TextField(blank=True, default='')
    score = models.IntegerField(default=0, help_text="Score out of 10 for this answer")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] {self.content[:60]}..."

    class Meta:
        ordering = ['created_at']

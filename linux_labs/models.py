from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TerminalLab(models.Model):
    """Defines a Linux terminal challenge lab (e.g., System Rescue, Network Diagnostics)."""

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    scenario = models.TextField(help_text="Backstory/scenario for the lab")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_minutes = models.IntegerField(default=30, help_text="Max lab duration in minutes")
    docker_image = models.CharField(
        max_length=200,
        default='cloudlabx-linux-lab:latest',
        help_text="Docker image to use for this lab"
    )
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, default='terminal', help_text="Material icon name")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def total_points(self):
        return sum(c.points for c in self.challenges.all())

    @property
    def challenge_count(self):
        return self.challenges.count()

    class Meta:
        ordering = ['order', 'created_at']


class TerminalChallenge(models.Model):
    """Individual MCQ + command challenge within a lab."""

    lab = models.ForeignKey(TerminalLab, on_delete=models.CASCADE, related_name='challenges')
    order = models.IntegerField(default=0)

    # MCQ Question
    question_text = models.TextField(help_text="The scenario/question presented to the user")
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')],
        help_text="Correct MCQ answer"
    )

    # Command validation
    expected_commands = models.JSONField(
        default=list,
        help_text="List of command patterns (regex) that must appear in terminal history"
    )
    command_hint = models.TextField(blank=True, default='', help_text="Hint shown after wrong attempt")

    # Scoring
    points = models.IntegerField(default=10)
    explanation = models.TextField(blank=True, default='', help_text="Explanation shown after submission")

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:80]}..."

    class Meta:
        ordering = ['order']
        unique_together = ['lab', 'order']


class TerminalLabSession(models.Model):
    """Tracks a user's attempt at a terminal lab."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='terminal_lab_sessions')
    lab = models.ForeignKey(TerminalLab, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Docker container tracking
    container_id = models.CharField(max_length=100, blank=True, default='')

    # Progress
    current_challenge_order = models.IntegerField(default=1)
    total_score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    timer_expires_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.lab.title} ({self.status})"

    @property
    def is_expired(self):
        if self.timer_expires_at and self.status == 'active':
            return timezone.now() >= self.timer_expires_at
        return False

    @property
    def remaining_seconds(self):
        if self.timer_expires_at and self.status == 'active':
            delta = self.timer_expires_at - timezone.now()
            return max(0, int(delta.total_seconds()))
        return 0

    @property
    def score_percentage(self):
        if self.max_score == 0:
            return 0
        return round((self.total_score / self.max_score) * 100, 1)

    @property
    def duration_minutes(self):
        end = self.ended_at or timezone.now()
        delta = end - self.started_at
        return round(delta.total_seconds() / 60, 1)

    class Meta:
        ordering = ['-started_at']


class ChallengeAttempt(models.Model):
    """Records the user's answer + commands for each challenge question."""

    session = models.ForeignKey(TerminalLabSession, on_delete=models.CASCADE, related_name='attempts')
    challenge = models.ForeignKey(TerminalChallenge, on_delete=models.CASCADE, related_name='attempts')

    # User's answer
    selected_option = models.CharField(max_length=1, blank=True, default='')
    is_mcq_correct = models.BooleanField(default=False)

    # Command validation
    command_history = models.JSONField(default=list, help_text="Commands the user ran in the terminal")
    is_commands_correct = models.BooleanField(default=False)

    # Scoring
    marks_awarded = models.IntegerField(default=0)
    feedback = models.TextField(blank=True, default='')

    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.user.username} — Q{self.challenge.order}: {self.marks_awarded}/{self.challenge.points}"

    class Meta:
        ordering = ['challenge__order']
        unique_together = ['session', 'challenge']

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Lab(models.Model):
    """Static definition of a lab (e.g., EC2 Launch Lab)."""

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_minutes = models.IntegerField(default=60, help_text="Max lab duration in minutes")
    max_score = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    terraform_dir = models.CharField(
        max_length=300,
        default='Terraform/IAM',
        help_text="Relative path to the Terraform config directory"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created_at']


class LabSession(models.Model):
    """Tracks one user's attempt at a lab — from start to end."""

    STATUS_CHOICES = [
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('submitted', 'Submitted'),
        ('ended', 'Ended'),
        ('expired', 'Expired'),
    ]

    TERRAFORM_STATE_CHOICES = [
        ('none', 'None'),
        ('applying', 'Applying'),
        ('applied', 'Applied'),
        ('destroying', 'Destroying'),
        ('destroyed', 'Destroyed'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_sessions')
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    credentials_received_at = models.DateTimeField(null=True, blank=True)
    timer_expires_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # AWS Credentials (stored for the session duration)
    iam_user_name = models.CharField(max_length=100, blank=True, default='')
    console_password = models.CharField(max_length=100, blank=True, default='')
    console_login_link = models.URLField(blank=True, default='')

    # Terraform state tracking
    terraform_state = models.CharField(
        max_length=20, choices=TERRAFORM_STATE_CHOICES, default='none'
    )

    def __str__(self):
        return f"{self.user.username} — {self.lab.title} ({self.status})"

    @property
    def is_expired(self):
        """Check if the timer has expired."""
        if self.timer_expires_at and self.status == 'active':
            return timezone.now() >= self.timer_expires_at
        return False

    @property
    def remaining_seconds(self):
        """Seconds remaining on the timer."""
        if self.timer_expires_at and self.status == 'active':
            delta = self.timer_expires_at - timezone.now()
            return max(0, int(delta.total_seconds()))
        return 0

    class Meta:
        ordering = ['-started_at']


class LabActivity(models.Model):
    """Individual task validation result within a lab session."""

    session = models.ForeignKey(LabSession, on_delete=models.CASCADE, related_name='activities')
    task_name = models.CharField(max_length=200)
    task_description = models.TextField(blank=True, default='')
    is_passed = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True, help_text="Raw validation details from boto3")

    def __str__(self):
        status = "✅" if self.is_passed else "❌"
        return f"{status} {self.task_name} — Session #{self.session.id}"

    class Meta:
        ordering = ['checked_at']
        verbose_name_plural = 'Lab Activities'


class LabScore(models.Model):
    """Final score record for a completed lab session."""

    session = models.OneToOneField(LabSession, on_delete=models.CASCADE, related_name='score')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_scores')
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name='scores')

    total_tasks = models.IntegerField(default=0)
    passed_tasks = models.IntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)

    scored_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.lab.title}: {self.score_percentage:.0f}%"

    class Meta:
        ordering = ['-scored_at']


class StudyMaterial(models.Model):
    """Comprehensive study material linked to a Lab for pre-lab learning."""

    lab = models.OneToOneField(Lab, on_delete=models.CASCADE, related_name='study_material')
    title = models.CharField(max_length=300)
    overview = models.TextField(help_text="Brief overview of what this material covers")
    icon = models.CharField(max_length=50, default='menu_book', help_text="Material icon name")
    estimated_read_minutes = models.IntegerField(default=15)
    prerequisites = models.TextField(blank=True, default='', help_text="Prerequisite knowledge (one per line)")
    learning_outcomes = models.TextField(blank=True, default='', help_text="Learning outcomes (one per line)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Study: {self.title}"

    @property
    def prerequisite_list(self):
        return [p.strip() for p in self.prerequisites.split('\n') if p.strip()]

    @property
    def outcome_list(self):
        return [o.strip() for o in self.learning_outcomes.split('\n') if o.strip()]

    class Meta:
        verbose_name_plural = 'Study Materials'


class StudySection(models.Model):
    """Individual section/chapter within a study material."""

    SECTION_TYPES = [
        ('theory', 'Theory'),
        ('concept', 'Concept'),
        ('architecture', 'Architecture'),
        ('best_practice', 'Best Practice'),
        ('hands_on', 'Hands-On Guide'),
        ('reference', 'Reference'),
    ]

    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='sections')
    order = models.IntegerField(default=0)
    title = models.CharField(max_length=300)
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, default='theory')
    content = models.TextField(help_text="Main content in HTML/markdown")
    code_example = models.TextField(blank=True, default='', help_text="Optional code snippet/CLI example")
    code_language = models.CharField(max_length=30, blank=True, default='bash', help_text="Language for syntax highlighting")
    tip = models.TextField(blank=True, default='', help_text="Pro tip or important note")
    key_takeaway = models.TextField(blank=True, default='', help_text="Key takeaway summary")
    icon = models.CharField(max_length=50, default='article', help_text="Material icon name")

    def __str__(self):
        return f"§{self.order}: {self.title}"

    class Meta:
        ordering = ['order']
        unique_together = ['material', 'order']

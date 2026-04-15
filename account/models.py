from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for tracking lab stats and streaks."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')

    # Aggregated stats (updated after each lab)
    total_labs_completed = models.IntegerField(default=0)
    total_score = models.FloatField(default=0.0, help_text="Sum of all lab scores")
    average_score = models.FloatField(default=0.0)

    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_lab_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile: {self.user.username}"

    @property
    def initials(self):
        """Get user initials for avatar display."""
        first = self.user.first_name[:1].upper() if self.user.first_name else ''
        last = self.user.last_name[:1].upper() if self.user.last_name else ''
        if first and last:
            return f"{first}{last}"
        return self.user.username[:2].upper()


# Auto-create profile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)





class StudentActivityLog(models.Model):
    """Tracks all student activities — logins, lab starts/ends, interview starts/ends."""

    ACTIVITY_CHOICES = [
        ('login', 'Login'),
        ('lab_start', 'Lab Started'),
        ('lab_end', 'Lab Ended'),
        ('interview_start', 'Interview Started'),
        ('interview_end', 'Interview Ended'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_CHOICES)
    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True, help_text="Extra context data")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.get_activity_type_display()} @ {self.timestamp:%b %d, %H:%M}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Student Activity Logs'

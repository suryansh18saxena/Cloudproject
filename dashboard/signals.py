from django.db.models.signals import post_save
from django.dispatch import receiver

from Lab.models import LabSession
from interview.models import InterviewSession
from account.models import StudentActivityLog


@receiver(post_save, sender=LabSession)
def log_lab_activity(sender, instance, created, **kwargs):
    """Log activity when a lab session is started or ended."""

    # Lab Started — when session is first created (status = provisioning)
    if created:
        StudentActivityLog.objects.create(
            user=instance.user,
            activity_type='lab_start',
            description=f'Started lab: {instance.lab.title}',
            metadata={
                'session_id': instance.id,
                'lab_id': instance.lab.id,
                'lab_title': instance.lab.title,
            }
        )
        return

    # Lab Ended — when status changes to 'ended'
    if instance.status == 'ended':
        # Get score if available
        score_data = {}
        try:
            score = instance.score
            score_data = {
                'score_percentage': score.score_percentage,
                'passed_tasks': score.passed_tasks,
                'total_tasks': score.total_tasks,
            }
        except Exception:
            pass

        StudentActivityLog.objects.create(
            user=instance.user,
            activity_type='lab_end',
            description=f'Completed lab: {instance.lab.title}',
            metadata={
                'session_id': instance.id,
                'lab_id': instance.lab.id,
                'lab_title': instance.lab.title,
                **score_data,
            }
        )


@receiver(post_save, sender=InterviewSession)
def log_interview_activity(sender, instance, created, **kwargs):
    """Log activity when an interview session is started or completed."""

    # Interview Started
    if created:
        StudentActivityLog.objects.create(
            user=instance.user,
            activity_type='interview_start',
            description=f'Started interview: {instance.get_role_display()} ({instance.get_difficulty_display()})',
            metadata={
                'session_id': instance.id,
                'role': instance.role,
                'difficulty': instance.difficulty,
            }
        )
        return

    # Interview Ended
    if instance.status == 'completed':
        StudentActivityLog.objects.create(
            user=instance.user,
            activity_type='interview_end',
            description=f'Completed interview: {instance.get_role_display()} — Score: {instance.overall_score}%',
            metadata={
                'session_id': instance.id,
                'role': instance.role,
                'difficulty': instance.difficulty,
                'overall_score': instance.overall_score,
                'total_questions': instance.total_questions,
                'correct_answers': instance.correct_answers,
            }
        )

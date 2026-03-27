from django.contrib import admin
from .models import Lab, LabSession, LabActivity, LabScore


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'duration_minutes', 'max_score', 'is_active']
    list_filter = ['difficulty', 'is_active']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(LabSession)
class LabSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'lab', 'status', 'terraform_state', 'started_at', 'timer_expires_at']
    list_filter = ['status', 'terraform_state']
    readonly_fields = ['console_password']


@admin.register(LabActivity)
class LabActivityAdmin(admin.ModelAdmin):
    list_display = ['session', 'task_name', 'is_passed', 'checked_at']
    list_filter = ['is_passed']


@admin.register(LabScore)
class LabScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'lab', 'passed_tasks', 'total_tasks', 'score_percentage', 'scored_at']
    list_filter = ['lab']

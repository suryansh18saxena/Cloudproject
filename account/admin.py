
from django.contrib import admin
from .models import UserProfile, StudentActivityLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_teacher', 'total_labs_completed', 'average_score', 'current_streak']
    list_editable = ['is_teacher']
    list_filter = ['is_teacher']
    readonly_fields = ['created_at']


@admin.register(StudentActivityLog)
class StudentActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'description', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__username', 'description']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_labs_completed', 'average_score', 'current_streak']
    readonly_fields = ['created_at']

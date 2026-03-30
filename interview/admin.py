from django.contrib import admin
from .models import InterviewSession, InterviewMessage


class InterviewMessageInline(admin.TabularInline):
    model = InterviewMessage
    extra = 0
    readonly_fields = ('sender', 'content', 'is_question', 'is_feedback', 'answer_rating', 'score', 'created_at')


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'difficulty', 'status', 'total_questions', 'correct_answers', 'overall_score', 'started_at')
    list_filter = ('status', 'role', 'difficulty')
    search_fields = ('user__username',)
    inlines = [InterviewMessageInline]


@admin.register(InterviewMessage)
class InterviewMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'is_question', 'is_feedback', 'answer_rating', 'score', 'created_at')
    list_filter = ('sender', 'is_question', 'answer_rating')

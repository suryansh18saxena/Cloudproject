from django.contrib import admin
from .models import TerminalLab, TerminalChallenge, TerminalLabSession, ChallengeAttempt


class TerminalChallengeInline(admin.TabularInline):
    model = TerminalChallenge
    extra = 1
    fields = ['order', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
              'correct_option', 'expected_commands', 'points']


@admin.register(TerminalLab)
class TerminalLabAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'duration_minutes', 'is_active', 'challenge_count']
    list_filter = ['difficulty', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TerminalChallengeInline]

    def challenge_count(self, obj):
        return obj.challenges.count()
    challenge_count.short_description = 'Questions'


@admin.register(TerminalChallenge)
class TerminalChallengeAdmin(admin.ModelAdmin):
    list_display = ['lab', 'order', 'question_text', 'correct_option', 'points']
    list_filter = ['lab']


@admin.register(TerminalLabSession)
class TerminalLabSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'lab', 'status', 'total_score', 'max_score', 'started_at']
    list_filter = ['status', 'lab']


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = ['session', 'challenge', 'is_mcq_correct', 'is_commands_correct', 'marks_awarded']

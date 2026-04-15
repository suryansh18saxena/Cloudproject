from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create-teacher/', views.create_teacher, name='create_teacher'),
    path('teacher/student/<int:student_id>/', views.student_profile, name='student_profile'),
]
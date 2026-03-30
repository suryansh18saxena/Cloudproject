from django.urls import path
from . import views

urlpatterns = [
    path('', views.interview_home, name='interview_home'),
    path('start/', views.start_interview, name='start_interview'),
    path('answer/', views.send_answer, name='send_answer'),
    path('end/', views.end_interview, name='end_interview'),
    path('history/<int:session_id>/', views.session_history, name='session_history'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ec2_lab, name='EC2_Lab'),
    path('start/', views.start_lab, name='start_lab'),
    path('submit/', views.submit_lab, name='submit_lab'),
    path('status/', views.lab_status, name='lab_status'),
    path('validate/', views.submit_lab, name='validate_lab'),  # alias for backward compat
    path('end/', views.end_lab, name='end_lab'),
]

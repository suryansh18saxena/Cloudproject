from django.urls import path
from . import views

urlpatterns = [
    path('', views.labs_hub, name='linux_labs_hub'),
    path('<int:lab_id>/', views.lab_detail, name='linux_lab_detail'),
    path('start/<int:lab_id>/', views.start_lab, name='start_linux_lab'),
    path('submit/', views.submit_answer, name='submit_linux_answer'),
    path('finish/', views.finish_lab, name='finish_linux_lab'),
    path('end/', views.end_lab, name='end_linux_lab'),
    path('results/<int:session_id>/', views.lab_results, name='linux_lab_results'),
]

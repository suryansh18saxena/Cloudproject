from django.urls import path
from . import views

urlpatterns = [
    path('study-materials/', views.study_material_hub, name='study_material_hub'),
    path('study-materials/<slug:slug>/', views.study_material_detail, name='study_material_detail'),
    path('<slug:slug>/', views.lab_detail, name='lab_detail'),
    path('<slug:slug>/start/', views.start_lab, name='start_lab'),
    path('<slug:slug>/submit/', views.submit_lab, name='submit_lab'),
    path('<slug:slug>/status/', views.lab_status, name='lab_status'),
    path('<slug:slug>/end/', views.end_lab, name='end_lab'),
]

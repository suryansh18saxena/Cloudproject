from django.urls import path
from . import views 

urlpatterns = [
    path('', views.ec2_lab, name='EC2_Lab'),
]
from django.shortcuts import render

# Create your views here.
def ec2_lab(request):
    return render(request, 'Lab/ec2_lab.html')
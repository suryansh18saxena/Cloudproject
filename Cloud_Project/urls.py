from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('account/', include('account.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('Lab/', include('Lab.urls')),
    path('interview/', include('interview.urls')),
    path('linux-labs/', include('linux_labs.urls')),
]

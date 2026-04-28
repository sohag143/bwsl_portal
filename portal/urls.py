from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls), # এখানে শুধু admin.site.urls হবে
    path('', include('calculator.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
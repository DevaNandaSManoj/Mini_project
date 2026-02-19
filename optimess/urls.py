"""
URL configuration for optimess project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('warden/', views.warden_dashboard, name='warden_dashboard'),
    path('mess/', views.mess_dashboard, name='mess_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student/complaint/', views.student_complaint, name='student_complaint'),
    path('student/broadcast/', views.student_broadcast, name='student_broadcast'),
    path('warden/broadcast/', views.warden_broadcast, name='warden_broadcast'),
    path('', include('food.urls')),
    path('', include('leave.urls')),

]

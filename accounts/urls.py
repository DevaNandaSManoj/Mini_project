from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('warden/', views.warden_dashboard, name='warden_dashboard'),
    path('mess/', views.mess_dashboard, name='mess_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student/complaint/', views.student_complaint, name='student_complaint'),
    path('student/broadcast/', views.student_broadcast, name='student_broadcast'),
    path('warden/broadcast/', views.warden_broadcast, name='warden_broadcast'),
]
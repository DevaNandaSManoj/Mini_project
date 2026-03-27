from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student/complaint/', views.student_complaint, name='student_complaint'),
    path('student/complaint/delete/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('student/broadcast/', views.student_broadcast, name='student_broadcast'),
    path('student/attendance/', views.student_attendance_month, name='student_attendance'),
    path('student/profile/', views.student_profile, name='student_profile'),
    
]
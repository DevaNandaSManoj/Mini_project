from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='warden_dashboard'),
    path('leave-requests/', views.leave_requests, name='warden_leave_requests'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    path('broadcast/', views.warden_broadcast, name='warden_broadcast'),
]
from django.urls import path
from .views import apply_leave, warden_leave_requests
from .views import leave_history
from .views import (
    apply_leave,
    warden_leave_requests,
    approve_leave,
    reject_leave,
    modify_leave
)




urlpatterns = [
    path('student/leave/apply/', apply_leave, name='apply_leave'),
    path('warden/leave/requests/', warden_leave_requests, name='warden_leave_requests'),
    path('warden/leave/approve/<int:leave_id>/', approve_leave, name='approve_leave'),
    path('warden/leave/reject/<int:leave_id>/', reject_leave, name='reject_leave'),
    path('student/leave/cancel/<int:leave_id>/', modify_leave, name='modify_leave'),
    path('student/leave/history/', leave_history, name='leave_history'),



]

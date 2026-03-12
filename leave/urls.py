from django.urls import path
from .views import apply_leave, leave_history, modify_leave
 

urlpatterns = [
    path('student/leave/apply/', apply_leave, name='apply_leave'),
    path('student/leave/cancel/<int:leave_id>/', modify_leave, name='modify_leave'),
    path('student/leave/history/', leave_history, name='leave_history'),



]

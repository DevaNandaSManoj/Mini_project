from django.urls import path
from . import views

urlpatterns = [

    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.manage_students, name='manage_students'),
    path('wardens/', views.manage_wardens, name='manage_wardens'),
    path('mess-managers/', views.manage_mess, name='manage_mess'),

    path('leaves/', views.all_leaves, name='all_leaves'),
    path('broadcasts/', views.broadcasts, name='broadcasts'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('food-report/', views.food_report, name='food_report'),
    path('meal-analysis/', views.meal_analysis, name='meal_analysis'),

    path('student-portal/', views.admin_student_portal, name='admin_student_portal'),
    path('student-portal/<int:student_id>/', views.admin_view_student_profile, name='admin_view_student_profile'),
    path('student-portal/toggle-edit/<int:student_id>/', views.admin_toggle_student_edit, name='admin_toggle_student_edit'),
]
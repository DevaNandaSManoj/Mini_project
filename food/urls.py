from django.urls import path
from .views import student_food_attendance, food_history, verify_location


urlpatterns = [
    path('student/food-attendance/', student_food_attendance,
         name='student_food_attendance'),
    path('student/food-history/', food_history, name='food_history'),
    path('student/verify-location/', verify_location, name='verify_location'),
]

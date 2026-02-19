from django.urls import path
from .views import student_food_attendance, attendance_mark


urlpatterns = [
    path('student/food-attendance/', student_food_attendance,
         name='student_food_attendance'),
    path('student/attendance/', attendance_mark,
     name='attendance_mark'),

]

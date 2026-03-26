from django.urls import path
from . import views

urlpatterns = [
    path('', views.mess_dashboard, name='mess_dashboard'),
    path('edit-menu/', views.edit_menu, name='edit_menu'),
    path('statistics/', views.meal_statistics, name='meal_statistics'),
]

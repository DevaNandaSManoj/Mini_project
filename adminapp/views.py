from django.shortcuts import render

def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')

def manage_students(request):
    return render(request, 'admin/admin_students.html')

def manage_wardens(request):
    return render(request, 'admin/admin_wardens.html')

def manage_mess(request):
    return render(request, 'admin/admin_mess_managers.html')

def all_leaves(request):
    return render(request, 'admin/all_leaves.html')

def broadcasts(request):
    return render(request, 'admin/admin_broadcasts.html')

def attendance_report(request):
    return render(request, 'admin/attendance.html')

def food_report(request):
    return render(request, 'admin/food_report.html')

def meal_analysis(request):
    return render(request, 'admin/meal_analysis.html')


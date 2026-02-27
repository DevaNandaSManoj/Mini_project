from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import DailyMenu, StudentDailyRecord

def get_client_ip(request):                   #currently not used
    return request.META.get('REMOTE_ADDR')   

def verify_college_network(ip):                 #currently not used
    return ip.startswith("192.168.")  # example

@login_required
def student_food_attendance(request):
    student = Student.objects.get(user=request.user)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    from leave.models import LeaveRequest

    # Leave checks
    leave_blocked = LeaveRequest.objects.filter(
        student=student,
        status='approved',
        from_date__lte=tomorrow,
        to_date__gte=tomorrow
    ).exists()

    leave_today = LeaveRequest.objects.filter(
        student=student,
        status='approved',
        from_date__lte=today,
        to_date__gte=today
    ).exists()

    # Menu
    menu, _ = DailyMenu.objects.get_or_create(
        date=tomorrow,
        defaults={
            'breakfast': 'Default Breakfast',
            'lunch': 'Default Lunch',
            'dinner': 'Default Dinner'
        }
    )

    food_record, _ = StudentDailyRecord.objects.get_or_create(
        student=student,
        date=tomorrow
    )

    attendance_record, _ = StudentDailyRecord.objects.get_or_create(
        student=student,
        date=today
    )

    # FOOD SUBMIT
    if request.method == "POST" and 'breakfast' in request.POST:
        if not leave_blocked:
            food_record.breakfast = request.POST.get('breakfast') == 'yes'
            food_record.lunch = request.POST.get('lunch') == 'yes'
            food_record.dinner = request.POST.get('dinner') == 'yes'
            food_record.save()

        return redirect('student_food_attendance')

    # ATTENDANCE SUBMIT
    if request.method == "POST" and 'status' in request.POST:
        if attendance_record.present is None:
            attendance_record.present = request.POST.get('status') == 'present'
            attendance_record.save()

        return redirect('student_food_attendance')

    food_submitted = (
        food_record.breakfast is not None and
        food_record.lunch is not None and
        food_record.dinner is not None
    )

    return render(request, 'student/food_attendance.html', {
        'student': student,
        'menu': menu,
        'food_record': food_record,
        'attendance_record': attendance_record,
        'leave_blocked': leave_blocked,
        'leave_today': leave_today,
        'food_submitted': food_submitted,
        'today': today,
        'tomorrow': tomorrow,
    })
    
@login_required
def food_history(request):
    if request.user.role != 'student':
        return redirect('login')

    student = Student.objects.get(user=request.user)

    last_10_days = date.today() - timedelta(days=10)

    records = StudentDailyRecord.objects.filter(
        student=student,
        date__gte=last_10_days
    ).order_by('-date')

    return render(request, "student/food_history.html", {
        "records": records
    })
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import DailyMenu, StudentDailyRecord

def get_client_ip(request):
    return request.META.get('REMOTE_ADDR')

def verify_college_network(ip):
    return ip.startswith("192.168.")  # example

@login_required
def student_food_attendance(request):
    student = Student.objects.get(user=request.user)
    tomorrow = date.today() + timedelta(days=1)

    from leave.models import LeaveRequest

    # 🔒 Block food if tomorrow is inside approved leave
    approved_leave = LeaveRequest.objects.filter(
        student=student,
        status='approved',
        from_date__lte=tomorrow,
        to_date__gte=tomorrow
    ).exists()

    menu, created = DailyMenu.objects.get_or_create(
        date=tomorrow,
        defaults={
            'breakfast': 'Default Breakfast',
            'lunch': 'Default Lunch',
            'dinner': 'Default Dinner'
        }
    )

    if approved_leave:
        return render(request, 'student_food_attendance.html', {
            'menu': menu,
            'student': student,
            'leave_blocked': True
        })

    if request.method == "POST":
        breakfast = request.POST.get('breakfast') == 'yes'
        lunch = request.POST.get('lunch') == 'yes'
        dinner = request.POST.get('dinner') == 'yes'

        StudentDailyRecord.objects.update_or_create(
            student=student,
            date=tomorrow,
            defaults={
                'breakfast': breakfast,
                'lunch': lunch,
                'dinner': dinner
            }
        )

        return redirect('attendance_mark')

    return render(request, 'student_food_attendance.html', {
        'menu': menu,
        'student': student
    })


@login_required
def attendance_mark(request):
    student = Student.objects.get(user=request.user)
    today = date.today()

    from leave.models import LeaveRequest

    approved_leave = LeaveRequest.objects.filter(
        student=student,
        status='approved',
        from_date__lte=today,
        to_date__gte=today
    ).exists()

    if approved_leave:
        return render(request, "attendance.html", {
            "leave_blocked": True
        })

    record, created = StudentDailyRecord.objects.get_or_create(
        student=student,
        date=today
    )

    if request.method == "POST":
        record.present = request.POST.get('status') == 'present'
        record.save()
        return redirect('student_dashboard')

    return render(request, 'attendance.html', {
        'record': record
    })

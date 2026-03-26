from datetime import date, timedelta ,time
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import DailyMenu, StudentDailyRecord
from leave.models import LeaveRequest

def get_client_ip(request):                   #currently not used
    return request.META.get('REMOTE_ADDR')   

def verify_college_network(ip):                 #currently not used
    return ip.startswith("192.168.")  # example

@login_required
def student_food_attendance(request):

    student = Student.objects.get(user=request.user)

    now = timezone.localtime()
    student_deadline = time(20, 0)  # 8 PM
    warden_deadline = time(22, 0)   # 10 PM

    student_locked = now.time() > student_deadline

    today = date.today()
    tomorrow = today + timedelta(days=1)

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

        if student_locked:
            return redirect('student_food_attendance')

        if not leave_blocked:

            food_record.breakfast = request.POST.get('breakfast') == 'yes'
            food_record.lunch = request.POST.get('lunch') == 'yes'
            food_record.dinner = request.POST.get('dinner') == 'yes'
            food_record.marked_by = "student"
            food_record.save()

        return redirect('student_food_attendance')

    # ATTENDANCE SUBMIT
    if request.method == "POST" and 'status' in request.POST:

        if student_locked:
            return redirect('student_food_attendance')

        # attendance allowed only if food submitted
        if (
            food_record.breakfast is not None and
            food_record.lunch is not None and
            food_record.dinner is not None
        ):

            if attendance_record.present is None:
                attendance_record.present = request.POST.get('status') == 'present'
                attendance_record.marked_by = "student"
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
        'student_locked': student_locked,
        'today': today,
        'tomorrow': tomorrow,
    })
    
@login_required
def food_history(request):
    if request.user.role != 'student':
        return redirect('login')

    student = Student.objects.get(user=request.user)

    filter_month = request.GET.get('month', '').strip()
    filter_date  = request.GET.get('date', '').strip()
    filter_type  = request.GET.get('filter_type', '').strip()  # 'date' or 'month'

    # If both are somehow submitted, use filter_type hint to decide winner
    if filter_date and filter_month:
        if filter_type == 'month':
            filter_date = ''
        else:
            filter_month = ''

    records = StudentDailyRecord.objects.filter(student=student)

    if filter_date:
        try:
            from datetime import datetime as dt
            parsed = dt.strptime(filter_date, '%Y-%m-%d').date()
            records = records.filter(date=parsed)
            filter_label = f"Results for {parsed.strftime('%d %b %Y')}"
        except ValueError:
            filter_date = ''
            filter_label = ''
    elif filter_month:
        try:
            year, month = map(int, filter_month.split('-'))
            records = records.filter(date__year=year, date__month=month)
            import calendar
            filter_label = f"Results for {calendar.month_name[month]} {year}"
        except (ValueError, AttributeError):
            filter_month = ''
            filter_label = ''
    else:
        # Default: last 10 days
        last_10_days = date.today() - timedelta(days=10)
        records = records.filter(date__gte=last_10_days)
        filter_label = 'Last 10 days'

    records = records.order_by('-date')

    return render(request, "student/food_history.html", {
        "records": records,
        "filter_month": filter_month,
        "filter_date": filter_date,
        "filter_label": filter_label,
        "today": date.today().strftime('%Y-%m-%d'),
        "current_month": date.today().strftime('%Y-%m'),
    })
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Complaint, Student, Broadcast
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime
from food.models import StudentDailyRecord
from leave.models import LeaveRequest
 

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

         

        role = request.POST.get('role')

        if user is not None and user.role == role:

            login(request, user)
             

            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'warden':
                return redirect('warden_dashboard')
            elif user.role == 'mess':
                return redirect('mess_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')

    student = Student.objects.get(user=request.user)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    
    # ================= DASHBOARD STATS =================

 

    # ================= MONTHLY ATTENDANCE =================

    current_month = today.month
    current_year = today.year

    monthly_records = StudentDailyRecord.objects.filter(
        student=student,
        date__month=current_month,
        date__year=current_year
    )

    total_days = monthly_records.count()
    present_days = monthly_records.filter(present=True).count()

    attendance_percentage = 0
    if total_days > 0:
        attendance_percentage = round((present_days / total_days) * 100, 1)

    # Month name for dashboard
    import calendar
    month_name = calendar.month_name[current_month]

    # Tomorrow meals count
    tomorrow_record = StudentDailyRecord.objects.filter(
        student=student,
        date=tomorrow
    ).first()

    meals_selected = 0
    if tomorrow_record:
        meals_selected = sum([
            tomorrow_record.breakfast or False,
            tomorrow_record.lunch or False,
            tomorrow_record.dinner or False
        ])

    # Leave count
    leave_count = LeaveRequest.objects.filter(student=student).count()

    # ================= BROADCAST (24 HOUR ACTIVE) =================


    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)

    active_broadcasts = Broadcast.objects.filter(
        target_role="student",
        created_at__gte=last_24_hours
    ).order_by('-created_at')
     

    # Auto mark active broadcasts as read
    for broadcast in active_broadcasts:
        broadcast.read_by.add(request.user)

    active_broadcast_count = active_broadcasts.count()

    return render(request, 'student/dashboard.html', {
        'student': student, 
        'today': today,
        'attendance_percentage': attendance_percentage,
        'meals_selected': meals_selected,
        'leave_count': leave_count,
        'active_broadcasts': active_broadcasts,
        'active_broadcast_count': active_broadcast_count,
        'month_name': month_name,
    })

@login_required
def student_attendance_month(request):

    if request.user.role != "student":
        return redirect("login")

    import calendar
    from datetime import date

    student = Student.objects.get(user=request.user)

    month = request.GET.get("month")
    year = request.GET.get("year")

    monthly_calendar = None

    if month and year:

        month = int(month)
        year = int(year)

        days_in_month = calendar.monthrange(year, month)[1]

        records = StudentDailyRecord.objects.filter(
            student=student,
            date__month=month,
            date__year=year
        )

        record_dict = {
            record.date.day: record
            for record in records
        }

        monthly_calendar = []

        today = date.today()

        for day in range(1, days_in_month + 1):

            record = record_dict.get(day)

            day_date = date(year, month, day)

            # Future days should show "-"
            if day_date > today:
                record = None

            monthly_calendar.append({
                "day": day,
                "record": record
            })

    months = [
        (1,"January"),(2,"February"),(3,"March"),(4,"April"),
        (5,"May"),(6,"June"),(7,"July"),(8,"August"),
        (9,"September"),(10,"October"),(11,"November"),(12,"December")
    ]

    years = list(range(2023,2031))

    return render(request, "student/attendance_history.html", {
        "monthly_calendar": monthly_calendar,
        "months": months,
        "years": years,
        "selected_month": month,
        "selected_year": year
    })



 




@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login')
    return render(request, 'admin/admin_dashboard.html')

@login_required
def student_complaint(request):
    if request.user.role != 'student':
        return redirect('login')

    student = Student.objects.get(user=request.user)

    if request.method == "POST":
        message = request.POST.get('message')
        if message:
            Complaint.objects.create(
                student=student,
                message=message
            )
            return redirect('student_complaint')

    complaints = Complaint.objects.filter(student=student).order_by('-created_at')

    return render(request, 'student/complaint.html', {
        'complaints': complaints
    })

@login_required
def student_broadcast(request):
    broadcasts = Broadcast.objects.all().order_by('-created_at')

    return render(request, 'student/broadcast.html', {
        'broadcasts': broadcasts
    })
 
 

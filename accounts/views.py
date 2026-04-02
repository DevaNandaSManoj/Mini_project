from django.shortcuts import render, redirect, get_object_or_404
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

    # Get IDs of wardens in this student's block
    from accounts.models import Warden
    from django.db.models import Q
    block_warden_ids = Warden.objects.filter(
        hostel_block=student.hostel_block
    ).values_list('user_id', flat=True)

    # Admin/mess broadcasts → visible to all students
    # Warden broadcasts → only visible to students in that warden's block
    active_broadcasts = Broadcast.objects.filter(
        target_role="student",
        created_at__gte=last_24_hours
    ).filter(
        Q(sender__role__in=['admin', 'mess']) |
        Q(sender__role='warden', sender__id__in=block_warden_ids)
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
    year  = request.GET.get("year")

    monthly_calendar  = None
    total_present     = 0
    total_absent      = 0
    overall_pct       = 0
    avg_daily_pct     = 0
    consecutive_days  = 0
    punctuality       = 0.0
    start_weekday     = 0   # 0=Sun offset for the calendar grid
    start_weekday_range = []

    if month and year:
        month = int(month)
        year  = int(year)

        days_in_month = calendar.monthrange(year, month)[1]

        records = StudentDailyRecord.objects.filter(
            student=student,
            date__month=month,
            date__year=year
        )

        record_dict = {record.date.day: record for record in records}

        monthly_calendar = []
        today = date.today()

        for day in range(1, days_in_month + 1):
            record   = record_dict.get(day)
            day_date = date(year, month, day)

            if day_date > today:
                record = None

            monthly_calendar.append({
                "day":    day,
                "record": record,
            })

        # ── Stats ──────────────────────────────────────────────────────
        recorded_days = [d for d in monthly_calendar if d["record"] is not None]
        total_present = sum(1 for d in recorded_days if d["record"].present)
        total_absent  = sum(1 for d in recorded_days if not d["record"].present)
        total_recorded = len(recorded_days)

        if total_recorded > 0:
            overall_pct   = round((total_present / total_recorded) * 100)
            avg_daily_pct = overall_pct   # same for month view

        # Consecutive present streak (up to today)
        streak = 0
        for d in reversed(recorded_days):
            if d["record"].present:
                streak += 1
            else:
                break
        consecutive_days = streak

        # Punctuality rating: 5 * (present/recorded), max 5
        if total_recorded > 0:
            punctuality = round(5 * total_present / total_recorded, 1)

        # Calendar weekday offset: Python weekday() gives Mon=0; we want Sun=0
        first_weekday_py = date(year, month, 1).weekday()   # 0=Mon
        start_weekday = (first_weekday_py + 1) % 7          # 0=Sun
        start_weekday_range = list(range(start_weekday))     # for template iteration

    months = [
        (1,"January"),(2,"February"),(3,"March"),(4,"April"),
        (5,"May"),(6,"June"),(7,"July"),(8,"August"),
        (9,"September"),(10,"October"),(11,"November"),(12,"December")
    ]

    years = list(range(2023, 2031))

    return render(request, "student/attendance_history.html", {
        "monthly_calendar": monthly_calendar,
        "months":           months,
        "years":            years,
        "selected_month":   month,
        "selected_year":    year,
        # stats
        "total_present":    total_present,
        "total_absent":     total_absent,
        "overall_pct":      overall_pct,
        "avg_daily_pct":    avg_daily_pct,
        "consecutive_days": consecutive_days,
        "punctuality":      punctuality,
        "start_weekday":       start_weekday,
        "start_weekday_range": start_weekday_range,
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
            from accounts.ml_classifier import classify_complaint
            classification = classify_complaint(message)
            Complaint.objects.create(
                student=student,
                message=message,
                complaint_type=classification['complaint_type'],
                category=classification['category'],
            )
            return redirect('student_complaint')

    complaints = Complaint.objects.filter(student=student).order_by('-created_at')

    return render(request, 'student/complaint.html', {
        'complaints': complaints
    })


@login_required
def delete_complaint(request, complaint_id):
    if request.user.role != 'student':
        return redirect('login')
    student = Student.objects.get(user=request.user)
    complaint = get_object_or_404(Complaint, id=complaint_id, student=student)
    if request.method == 'POST':
        complaint.delete()
    return redirect('student_complaint')

@login_required
def student_broadcast(request):
    category_filter = request.GET.get('category', 'all')

    student = Student.objects.get(user=request.user)

    # Block-scoped: warden broadcasts only from the student's own block warden
    from accounts.models import Warden
    from django.db.models import Q
    block_warden_ids = Warden.objects.filter(
        hostel_block=student.hostel_block
    ).values_list('user_id', flat=True)

    broadcasts = Broadcast.objects.filter(
        target_role="student"
    ).filter(
        Q(sender__role__in=['admin', 'mess']) |
        Q(sender__role='warden', sender__id__in=block_warden_ids)
    ).order_by('-created_at')

    if category_filter and category_filter != 'all':
        broadcasts = broadcasts.filter(category=category_filter)

    return render(request, 'student/broadcast.html', {
        'broadcasts': broadcasts,
        'selected_category': category_filter,
    })

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('login')

    student = Student.objects.get(user=request.user)

    if request.method == "POST":
        # Photo upload is always allowed regardless of edit permission
        if 'profile_picture' in request.FILES:
            student.profile_picture = request.FILES['profile_picture']
            student.save()
            messages.success(request, "Profile photo updated successfully!")
            return redirect('student_profile')

        # Text field edits require warden's permission
        if not student.can_edit_profile:
            messages.error(request, "Editing is locked. Ask your warden to enable profile editing.")
            return redirect('student_profile')

        student.father_name = request.POST.get("father_name")
        student.mother_name = request.POST.get("mother_name")
        student.parent_phone_number = request.POST.get("parent_phone")
        student.address = request.POST.get("address")
        student.place = request.POST.get("place")
        student.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('student_profile')

    from accounts.models import Warden
    assigned_warden = Warden.objects.filter(hostel_block=student.hostel_block).first()

    return render(request, 'student/profile.html', {
        'student': student,
        'assigned_warden': assigned_warden,
    })

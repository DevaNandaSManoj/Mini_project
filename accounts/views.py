from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Complaint, Student
from .models import Broadcast
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

 

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

    from accounts.models import Student
    from food.models import DailyMenu, StudentDailyRecord
    from leave.models import LeaveRequest
    from datetime import date, timedelta, datetime

    student = Student.objects.get(user=request.user)

    today = date.today()
    tomorrow = today + timedelta(days=1)

     

    # ================= LEAVE BLOCK CHECK =================
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

    # ================= MENU =================
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

    # ================= FOOD =================
    if request.method == "POST" and request.POST.get("action") == "food":
        if not leave_blocked:
            food_record.breakfast = request.POST.get('breakfast') == 'yes'
            food_record.lunch = request.POST.get('lunch') == 'yes'
            food_record.dinner = request.POST.get('dinner') == 'yes'
            food_record.save()
        return redirect('student_dashboard')

    # ================= ATTENDANCE =================
    if request.method == "POST" and request.POST.get("action") == "attendance":
        if attendance_record.present is None:
            attendance_record.present = request.POST.get('status') == 'present'
            attendance_record.save()
        return redirect('student_dashboard')


    # ================= FLAGS =================
    food_submitted = (
        food_record.breakfast is not None and
        food_record.lunch is not None and
        food_record.dinner is not None
    )

    attendance_allowed = (
        (
            (food_submitted and not leave_blocked)
            or leave_blocked
        )
        and not leave_today
        and attendance_record.present is None
    )

 

    # ================= DASHBOARD STATS =================

    from food.models import StudentDailyRecord
    from leave.models import LeaveRequest

    # Attendance %
    total_days = StudentDailyRecord.objects.filter(student=student).count()
    present_days = StudentDailyRecord.objects.filter(
        student=student,
        present=True
    ).count()

    attendance_percentage = 0
    if total_days > 0:
        attendance_percentage = round((present_days / total_days) * 100, 1)

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
        created_at__gte=last_24_hours
    ).order_by('-created_at')
     

    # Auto mark active broadcasts as read
    for broadcast in active_broadcasts:
        broadcast.read_by.add(student)

    active_broadcast_count = active_broadcasts.count()

    return render(request, 'student/dashboard.html', {
        'student': student,
        'menu': menu,
        'food_record': food_record,
        'attendance_record': attendance_record,
        'leave_blocked': leave_blocked,
        'leave_today': leave_today,
        'attendance_allowed': attendance_allowed,
        'food_submitted': food_submitted,
        'today': today,
        'tomorrow': tomorrow,
        'attendance_percentage': attendance_percentage,
        'meals_selected': meals_selected,
        'leave_count': leave_count,
        'active_broadcasts': active_broadcasts,
        'active_broadcast_count': active_broadcast_count,
    })








@login_required
def warden_dashboard(request):
    if request.user.role != 'warden':
        return redirect('login')
    return render(request, 'warden_dashboard.html')


@login_required
def mess_dashboard(request):
    if request.user.role != 'mess':
        return redirect('login')
    return render(request, 'mess_dashboard.html')



@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login')
    return render(request, 'admin_dashboard.html')

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
 
@login_required
def warden_broadcast(request):
    from .models import Broadcast, BroadcastRead, Student

    broadcasts = Broadcast.objects.all().order_by('-created_at')
    total_students = Student.objects.count()

    broadcast_data = []

    for broadcast in broadcasts:
        reads = BroadcastRead.objects.filter(broadcast=broadcast)
        read_students = [read.student for read in reads]

        read_count = reads.count()

        read_percentage = 0
        if total_students > 0:
            read_percentage = round((read_count / total_students) * 100, 1)

        broadcast_data.append({
            'broadcast': broadcast,
            'total_students': total_students,
            'read_count': read_count,
            'read_percentage': read_percentage,
            'read_students': read_students,
        })

    return render(request, 'warden/broadcast.html', {
        'broadcast_data': broadcast_data
    })

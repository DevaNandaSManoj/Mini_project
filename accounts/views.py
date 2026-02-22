from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Complaint, Student
from .models import Broadcast
from django.contrib import messages
 

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

    leave_error = None

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

    # ================= APPLY LEAVE =================
    if request.method == "POST" and request.POST.get("action") == "apply_leave":

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')

        if from_date and to_date and reason:

            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()

            if from_date < today:
                messages.error(request, "Leave start date cannot be in the past.")
                return redirect('/student/?tab=leave')

            elif to_date < from_date:
                messages.error(request, "Leave end date cannot be before start date.")
                return redirect('/student/?tab=leave')

            else:
                overlap = LeaveRequest.objects.filter(
                    student=student,
                    status__in=["pending", "approved"],
                    from_date__lte=to_date,
                    to_date__gte=from_date
                ).exists()

                if overlap:
                    messages.error(request, "You already have a pending or approved leave during this period.")
                    return redirect('/student/?tab=leave')
                    
                else:
                    LeaveRequest.objects.create(
                        student=student,
                        from_date=from_date,
                        to_date=to_date,
                        reason=reason,
                        status='pending'
                    )
                    return redirect('/student/?tab=leave')

    # ================= CANCEL =================
    if request.method == "POST" and request.POST.get("action") == "cancel_leave":
        from food.models import StudentDailyRecord

        leave_id = request.POST.get("leave_id")
        leave = LeaveRequest.objects.filter(id=leave_id, student=student).first()

        if leave and leave.status in ["pending", "approved"]:

            # Delete related daily food records (Optimized way)
            StudentDailyRecord.objects.filter(
                student=student,
                date__range=[leave.from_date, leave.to_date]
            ).delete()

            # Delete leave request
            leave.delete()

        return redirect('/student/?tab=leave')
 
    # ================= SHORTEN / EXTEND =================
    if request.method == "POST" and request.POST.get("action") == "shorten_leave":
        from food.models import StudentDailyRecord
        from datetime import timedelta, datetime

        leave_id = request.POST.get("leave_id")
        new_to_date = request.POST.get("new_to_date")

        leave = LeaveRequest.objects.filter(id=leave_id, student=student).first()

        if leave and leave.status == "approved" and new_to_date:
            new_to_date = datetime.strptime(new_to_date, "%Y-%m-%d").date()

            if new_to_date >= leave.from_date:

                old_to_date = leave.to_date

                # 🔹 SHORTEN (Delete extra blocked days)
                if new_to_date < old_to_date:
                    StudentDailyRecord.objects.filter(
                        student=student,
                        date__range=[new_to_date + timedelta(days=1), old_to_date]
                    ).delete()

                # 🔹 EXTEND (Add new blocked days)
                elif new_to_date > old_to_date:
                    current_date = old_to_date + timedelta(days=1)

                    while current_date <= new_to_date:
                        StudentDailyRecord.objects.create(
                            student=student,
                            date=current_date,
                            breakfast=False,
                            lunch=False,
                            dinner=False,
                            present=False
                        )
                        current_date += timedelta(days=1)

                leave.to_date = new_to_date
                leave.save()

        return redirect('/student/?tab=leave')

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

    leave_requests = LeaveRequest.objects.filter(
        student=student
    ).order_by('-from_date')

    return render(request, 'student_dashboard.html', {
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
        'leave_requests': leave_requests,
        'leave_error': leave_error,
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
            return redirect('student_dashboard')

    return render(request, 'student_complaint.html')

@login_required
def student_broadcast(request):
    if request.user.role != 'student':
        return redirect('login')

    messages = Broadcast.objects.all().order_by('-created_at')

    return render(request, 'student_broadcast.html', {
        'messages': messages
    })
    
@login_required
def warden_broadcast(request):
    if request.user.role != 'warden':
        return redirect('login')

    if request.method == "POST":
        message = request.POST.get('message')
        if message:
            Broadcast.objects.create(message=message)
            return redirect('warden_dashboard')

    return render(request, 'warden_broadcast.html')

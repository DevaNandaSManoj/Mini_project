from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from leave.models import LeaveRequest
from accounts.models import Broadcast, Warden, Student ,Complaint
from food.models import StudentDailyRecord
from django.utils import timezone
from datetime import date, timedelta


@login_required
def dashboard(request):
    # Role protection
    if request.user.role != "warden":
        return redirect("login")

    # Get warden profile
    warden = Warden.objects.get(user=request.user)

    today = date.today()

    # ================= TOP STAT CARDS =================

    # Total students
    total_students = Student.objects.count()

    # Pending leave requests
    pending_leaves = LeaveRequest.objects.filter(status="pending").count()

    # Today's attendance %
    today_records = StudentDailyRecord.objects.filter(date=today)
    total_today = today_records.count()
    present_today = today_records.filter(present=True).count()

    attendance_percent = 0
    if total_today > 0:
        attendance_percent = round((present_today / total_today) * 100, 1)

    # ================= ATTENDANCE SUMMARY =================

    absent_today = total_today - present_today

    # ================= ADMIN → WARDEN BROADCAST (LAST 24 HRS) =================

    last_24 = timezone.now() - timedelta(hours=24)

    active_admin_broadcasts = Broadcast.objects.filter(
        target_role="warden",
        created_at__gte=last_24
    ).order_by("-created_at")

    admin_broadcast_count = active_admin_broadcasts.count()

    # ================= RENDER =================

    return render(request, "warden/dashboard.html", {
        "total_students": total_students,
        "pending_count": pending_leaves,
        "attendance_percent": attendance_percent,
        "present_today": present_today,
        "absent_today": absent_today,
        "admin_broadcast_count": admin_broadcast_count,
        "active_admin_broadcasts": active_admin_broadcasts,
    })

@login_required
def leave_requests(request):

    if request.user.role != "warden":
        return redirect("login")

    warden = Warden.objects.get(user=request.user)

    pending_requests = LeaveRequest.objects.filter(status='pending').select_related('student__user')
    processed_requests = LeaveRequest.objects.exclude(status='pending').select_related('student__user')

    return render(request, 'warden/leave_requests.html', {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
        'pending_count': pending_requests.count(),
    })

@login_required
def approve_leave(request, leave_id):
   

    leave = LeaveRequest.objects.get(id=leave_id)

    leave.status = 'approved'
    leave.save()

    # 🔹 Auto update food & attendance for all leave dates
    current_date = leave.from_date

    while current_date <= leave.to_date:
        record, _ = StudentDailyRecord.objects.get_or_create(
            student=leave.student,
            date=current_date
        )

        # Override any existing food selection
        record.breakfast = False
        record.lunch = False
        record.dinner = False

        # Mark attendance absent
        record.present = False
        record.marked_by = "auto"
        record.save()

        current_date += timedelta(days=1)

    return redirect('warden_leave_requests')



@login_required
def reject_leave(request, leave_id):
    leave = LeaveRequest.objects.get(id=leave_id)
    leave.status = 'rejected'
    leave.save()
    return redirect('warden_leave_requests')


@login_required
def warden_broadcast(request):

    if request.user.role != "warden":
        return redirect("login")

    warden = Warden.objects.get(user=request.user)

    # 🔹 Send Broadcast
    if request.method == "POST":
        message = request.POST.get("message")

        if message:
            Broadcast.objects.create(
                sender=request.user,
                message=message,
                target_role="student"
            )
            return redirect("warden_broadcast")

    # 🔥 NEW: Last 24 Hours Filter
    last_24_hours = timezone.now() - timedelta(hours=24)

    # 🔹 Only this warden's broadcasts to students (LAST 24 HOURS ONLY)
    broadcasts = Broadcast.objects.filter(
        sender=request.user,
        target_role="student",
        created_at__gte=last_24_hours
    ).prefetch_related("read_by").order_by("-created_at")

    # 🔹 Students in this block
    total_students = Student.objects.filter(
        hostel_block=warden.hostel_block
    ).count()

    broadcast_data = []

    for broadcast in broadcasts:
        read_count = broadcast.read_by.count()

        broadcast_data.append({
            "broadcast": broadcast,
            "read_count": read_count,
            "total_students": total_students,
        })
        
    pending_count = LeaveRequest.objects.filter(status="pending").count()

    return render(request, "warden/broadcast.html", {
        "broadcast_data": broadcast_data,
        "pending_count": pending_count,
    })

# ================= WARDEN ATTENDANCE =================
@login_required
def warden_attendance(request):
    if request.user.role != "warden":
        return redirect("login")

    today = date.today()

    # Alphabetical order
    students = Student.objects.all().order_by("user__username")

    # ================= MARK ATTENDANCE =================
    if request.method == "POST" and request.POST.get("action") == "mark":

        student_id = request.POST.get("student_id")
        status = request.POST.get("status")

        if student_id and status:
            student = Student.objects.filter(id=student_id).first()

            if student:
                record, created = StudentDailyRecord.objects.get_or_create(
                    student=student,
                    date=today
                )

                record.present = True if status == "present" else False

                # ✅ Marked by warden
                record.marked_by = "warden"

                record.save()

        return redirect("warden_attendance")

    # ================= TODAY SUMMARY =================
    today_records = StudentDailyRecord.objects.filter(date=today)

    total_students = students.count()
    present_count = today_records.filter(present=True).count()
    absent_count = today_records.filter(present=False).count()

    # If some students not marked yet → count as unmarked
    unmarked_count = total_students - (present_count + absent_count)

    # ================= DAILY SEARCH =================
    search_student_id = request.GET.get("search_student_id")
    search_date = request.GET.get("search_date")
    search_result = None

    if search_student_id and search_date:
        try:
            search_date_obj = date.fromisoformat(search_date)

            search_result = StudentDailyRecord.objects.filter(
                student_id=search_student_id,
                date=search_date_obj
            ).select_related("student")

        except ValueError:
            search_result = None

    # ================= MONTHLY CALENDAR =================
    import calendar

    month = request.GET.get("month")
    year = request.GET.get("year")
    monthly_calendar = None
    selected_student = None

    if month and year:
        try:
            month = int(month)
            year = int(year)

            days_in_month = calendar.monthrange(year, month)[1]

            calendar_student_id = request.GET.get("calendar_student_id")

            if calendar_student_id:
                selected_student = Student.objects.filter(id=calendar_student_id).first()

            if selected_student:
                records = StudentDailyRecord.objects.filter(
                    student=selected_student,
                    date__month=month,
                    date__year=year
                )

                record_dict = {
                    record.date.day: record
                    for record in records
                }

                monthly_calendar = []

                for day in range(1, days_in_month + 1):
                    monthly_calendar.append({
                        "day": day,
                        "record": record_dict.get(day)
                    })

        except:
            monthly_calendar = None

    pending_count = LeaveRequest.objects.filter(status="pending").count()

    warden = Warden.objects.get(user=request.user)

    # Generate a list of years for the dropdown (from 2000 to 2050)
    years = list(range(2000, 2051))

    return render(request, "warden/warden_attendance.html", {
        "students": students,
        "today_records": today_records,
        "present_count": present_count,
        "absent_count": absent_count,
        "unmarked_count": unmarked_count,
        "today": today,
        "search_result": search_result,
        "search_student_id": search_student_id,
        "monthly_calendar": monthly_calendar,
        "selected_student": selected_student,
        "active_page": "attendance",
        "pending_count": pending_count,
        "years": years,
    })

@login_required
def warden_mess(request):

    if request.user.role != "warden":
        return redirect("login")

    warden = Warden.objects.get(user=request.user)

    today = date.today()

    # 🔹 Block-based students only
    students = Student.objects.filter(
        hostel_block=warden.hostel_block
    ).order_by("user__username")

    selected_record = None
    selected_student_id = None
    leave_locked = False

    # ================= SAVE =================
    if request.method == "POST":

        student_id = request.POST.get("student_id")
        selected_date = request.POST.get("date")

        breakfast = request.POST.get("breakfast")
        lunch = request.POST.get("lunch")
        dinner = request.POST.get("dinner")

        if student_id and selected_date:

            selected_student_id = student_id
            selected_date_obj = date.fromisoformat(selected_date)

            student = Student.objects.filter(id=student_id).first()

            if student:

                # 🔒 Backend Leave Protection
                approved_leave = LeaveRequest.objects.filter(
                    student=student,
                    status="approved",
                    from_date__lte=selected_date_obj,
                    to_date__gte=selected_date_obj
                ).exists()

                if approved_leave:
                    # Don't allow saving if on leave
                    return redirect(f"{request.path}?student_id={student_id}&date={selected_date}")

                record, created = StudentDailyRecord.objects.get_or_create(
                    student=student,
                    date=selected_date_obj
                )

                record.breakfast = True if breakfast == "yes" else False
                record.lunch = True if lunch == "yes" else False
                record.dinner = True if dinner == "yes" else False

                record.save()
                
        return redirect(f"{request.path}?student_id={student_id}&date={selected_date}")

    # ================= LOAD =================
    selected_student_id = request.GET.get("student_id")
    selected_date = request.GET.get("date")

    if selected_student_id and selected_date:

        student = Student.objects.filter(id=selected_student_id).first()
        if student:
            selected_date_obj = date.fromisoformat(selected_date)
            # 🔒 Check approved leave
            approved_leave = LeaveRequest.objects.filter(
                student=student,
                status="approved",
                from_date__lte=selected_date_obj,
                to_date__gte=selected_date_obj
            ).exists()

            if approved_leave:
                leave_locked = True
            
            selected_record = StudentDailyRecord.objects.filter(
                student=student,
                date=selected_date_obj
            ).first()

    selected_date_for_count = request.GET.get("date") or today

    try:
        selected_date_obj = date.fromisoformat(str(selected_date_for_count))
    except:
        selected_date_obj = today

    daily_records = StudentDailyRecord.objects.filter(date=selected_date_obj)

    breakfast_count = daily_records.filter(breakfast=True).count()
    lunch_count = daily_records.filter(lunch=True).count()
    dinner_count = daily_records.filter(dinner=True).count()
    
    pending_count = LeaveRequest.objects.filter(status="pending").count()

    return render(request, "warden/warden_mess.html", {
        "leave_locked": leave_locked,
        "students": students,
        "today": today,
        "selected_record": selected_record,
        "selected_student_id": selected_student_id,
        "breakfast_count": breakfast_count,
        "lunch_count": lunch_count,
        "dinner_count": dinner_count,
        "pending_count": pending_count,
    })

from accounts.models import Complaint

@login_required
def warden_complaints(request):

    if request.user.role != "warden":
        return redirect("login")

    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")

        complaint = Complaint.objects.get(id=complaint_id)

        complaint.status = "resolved"
        complaint.save()

        return redirect("warden_complaints")

    warden = Warden.objects.get(user=request.user)

    complaints = Complaint.objects.filter(
        student__hostel_block=warden.hostel_block
    ).select_related("student__user").order_by("-created_at")

    # 🔹 Filtering logic
    status_filter = request.GET.get("status")

    if status_filter in ["pending", "resolved"]:
        complaints = complaints.filter(status=status_filter)

    # Mark as seen
    complaints.update(is_seen_by_warden=True)

    total_count = Complaint.objects.filter(
        student__hostel_block=warden.hostel_block
    ).count()

    pending_complaints_count = Complaint.objects.filter(
        student__hostel_block=warden.hostel_block,
        status="pending"
    ).count()

    resolved_count = total_count - pending_complaints_count
    
    pending_count = LeaveRequest.objects.filter(status="pending").count()

    return render(request, "warden/warden_complaints.html", {
        "complaints": complaints,
        "total_count": total_count,
        "pending_complaints_count": pending_complaints_count,
        "resolved_count": resolved_count,
        "active_filter": status_filter,
        "pending_count": pending_count,
    })
@login_required    
def resolve_complaint(request, complaint_id):

    if request.user.role != "warden":
        return redirect("login")

    complaint = Complaint.objects.filter(id=complaint_id).first()

    if complaint:
        complaint.status = "resolved"
        complaint.save()

    return redirect("warden_complaints")

from django.contrib import messages

@login_required
def resolve_complaint(request, complaint_id):

    complaint = Complaint.objects.get(id=complaint_id)

    complaint.status = "resolved"
    complaint.save()

    messages.success(
        request,
        f'Complaint from {complaint.student.user.username} marked as resolved.'
    )

    return redirect("warden_complaints")
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from leave.models import LeaveRequest
from accounts.models import Broadcast, Warden, Student
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
        "warden": warden,
        "total_students": total_students,
        "pending_leaves": pending_leaves,
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
        'warden': warden,
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

    return render(request, "warden/broadcast.html", {
        "warden": warden,
        "broadcast_data": broadcast_data,
    })
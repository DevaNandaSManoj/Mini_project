from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from leave.models import LeaveRequest
from accounts.models import Broadcast, Student
 



@login_required
def dashboard(request):
    if request.user.role != 'warden':
        return redirect('login')
    return render(request, 'warden/dashboard.html')

@login_required
def leave_requests(request):
    pending_requests = LeaveRequest.objects.filter(status='pending')

    return render(request, 'warden/leave_requests.html', {
        'leave_requests': pending_requests
    })

@login_required
def approve_leave(request, leave_id):
    from food.models import StudentDailyRecord
    from datetime import timedelta

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
     

    broadcasts = Broadcast.objects.all().prefetch_related('read_by').order_by('-created_at')
    total_students = Student.objects.count()

    broadcast_data = []

    for broadcast in broadcasts:
        read_students = broadcast.read_by.all()
        read_count = broadcast.read_count()

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
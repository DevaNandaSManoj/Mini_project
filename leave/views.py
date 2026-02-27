from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import LeaveRequest


@login_required
def apply_leave(request):
    student = Student.objects.get(user=request.user)
    # 🔄 Auto-expire pending leave whose period is over
    LeaveRequest.objects.filter(
        student=student,
        status="pending",
        to_date__lt=date.today()
    ).update(status="rejected")

    existing_leave = LeaveRequest.objects.filter(
        student=student
    ).exclude(
        status="approved",
        to_date__lt=date.today()
    ).exclude(
        status="rejected",
        seen_by_student=True
    ).order_by('-applied_on').first()

    # 👁 Mark rejected leave as seen (only once)
    if existing_leave and existing_leave.status == "rejected" and not existing_leave.seen_by_student:
        existing_leave.seen_by_student = True
        existing_leave.save()

    # 🚫 Check if student already has an active leave
    active_leave = LeaveRequest.objects.filter(
        student=student,
        status__in=["pending", "approved"],
        to_date__gte=date.today()
    ).exists()

    if request.method == "POST":
        if active_leave:
            return render(request, 'student/leave.html', {
            'error': 'You already have an active leave. Cancel or wait until it ends.',
            'leave': existing_leave
        })
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')
    
        # 🚨 Check missing fields (form tampering protection)
        if not from_date or not to_date or not reason:
            return render(request, 'student/leave.html', {
                'error': 'All fields are required.',
                'leave': existing_leave
            })

        # 🚨 Reason must not be empty or spaces
        if not reason.strip():
            return render(request, 'student/leave.html', {
                'error': 'Reason is required.',
                'leave': existing_leave
            })

        # 🚨 Reason must not be only numbers
        if reason.strip().isdigit():
            return render(request, 'student/leave.html', {
                'error': 'Reason must be valid text, not just numbers.',
                'leave': existing_leave
            })

        try:
            from_date_obj = date.fromisoformat(from_date)
            to_date_obj = date.fromisoformat(to_date)
        except ValueError:
            return render(request, 'student/leave.html', {
                'error': 'Invalid date format.',
                'leave': existing_leave
            })

    

        from_date_obj = date.fromisoformat(from_date)
        to_date_obj = date.fromisoformat(to_date)

            # 🚨 From date cannot be in the past
        if from_date_obj < date.today():
            return render(request, 'student/leave.html', {
                'error': 'From date cannot be in the past.',
                'leave': existing_leave
            })

        if from_date_obj > to_date_obj:
            return render(request, 'student/leave.html', {
                'error': 'From date cannot be after To date',
                'leave': existing_leave
            })

        if to_date_obj < date.today():
            return render(request, 'student/leave.html', {
                'error': 'Leave dates cannot be in the past',
                'leave': existing_leave
            })


        # 🚨 Check overlapping leave
        overlapping_leave = LeaveRequest.objects.filter(
            student=student,
            status__in=["pending", "approved"],
            from_date__lte=to_date_obj,
            to_date__gte=from_date_obj
        ).exists()

        if overlapping_leave:
            return render(request, 'student/leave.html', {
                'error': 'This leave overlaps with an existing leave request.',
                'leave': existing_leave
            })

        # ✅ Create leave
        LeaveRequest.objects.create(
            student=student,
            from_date=from_date_obj,
            to_date=to_date_obj,
            reason=reason.strip()
        )

        return redirect('apply_leave')

    return render(request, 'student/leave.html', {
        'leave': existing_leave
    })


@login_required
def warden_leave_requests(request):
    pending_requests = LeaveRequest.objects.filter(status='pending')

    return render(request, 'warden_leave_requests.html', {
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
def modify_leave(request, leave_id):
    student = Student.objects.get(user=request.user)
    leave = LeaveRequest.objects.get(id=leave_id, student=student)

    if request.method == "POST":

        # ✅ RESTORED ORIGINAL CANCEL LOGIC
        if request.POST.get("action") == "cancel":

            from food.models import StudentDailyRecord

            StudentDailyRecord.objects.filter(
                student=student,
                date__range=[leave.from_date, leave.to_date]
            ).delete()

            leave.delete()

            return redirect("apply_leave")

        new_end_date = request.POST.get("new_end_date")
        new_end_date_obj = date.fromisoformat(new_end_date)

        # Validation
        if new_end_date_obj < leave.from_date:
            return render(request, "student/leave.html", {
                "leave": leave,
                "error": "End date cannot be before leave start date."
            })

        if leave.status != "approved":
            return render(request, "student/leave.html", {
                "leave": leave,
                "error": "Only approved leave can be modified."
            })

        old_to_date = leave.to_date

        # SHORTEN
        if new_end_date_obj < old_to_date:
            leave.to_date = new_end_date_obj
            leave.save()

            from food.models import StudentDailyRecord

            StudentDailyRecord.objects.filter(
                student=student,
                date__gt=new_end_date_obj,
                date__lte=old_to_date
            ).delete()

        # EXTEND
        elif new_end_date_obj > old_to_date:
            leave.to_date = new_end_date_obj
            leave.save()

            from food.models import StudentDailyRecord

            current_date = old_to_date + timedelta(days=1)

            while current_date <= new_end_date_obj:
                StudentDailyRecord.objects.update_or_create(
                    student=student,
                    date=current_date,
                    defaults={
                        "breakfast": False,
                        "lunch": False,
                        "dinner": False,
                        "present": False
                    }
                )
                current_date += timedelta(days=1)

        return redirect("apply_leave")

    return render(request, "student/leave.html", {
        "leave": leave
    })

@login_required
def leave_history(request):
    student = Student.objects.get(user=request.user)

    # Get all leave records of this student
    leaves = LeaveRequest.objects.filter(
        student=student
    ).order_by('-applied_on')

    approved = leaves.filter(status="approved")
    rejected = leaves.filter(status="rejected")
    pending = leaves.filter(status="pending")

    context = {
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "approved_count": approved.count(),
        "rejected_count": rejected.count(),
        "pending_count": pending.count(),
    }

    return render(request, "student/leave_history.html", context)
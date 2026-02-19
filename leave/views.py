from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import LeaveRequest


@login_required
def apply_leave(request):
    student = Student.objects.get(user=request.user)

    existing_leave = LeaveRequest.objects.filter(
        student=student
    ).order_by('-applied_on').first()

    if request.method == "POST":
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')

        from_date_obj = date.fromisoformat(from_date)
        to_date_obj = date.fromisoformat(to_date)

        if from_date_obj > to_date_obj:
            return render(request, 'apply_leave.html', {
                'error': 'From date cannot be after To date',
                'leave': existing_leave
            })

        if to_date_obj < date.today():
            return render(request, 'apply_leave.html', {
                'error': 'Leave dates cannot be in the past',
                'leave': existing_leave
            })

        LeaveRequest.objects.create(
            student=student,
            from_date=from_date_obj,
            to_date=to_date_obj,
            reason=reason
        )

        return redirect('apply_leave')

    return render(request, 'apply_leave.html', {
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
        new_end_date = request.POST.get("new_end_date")
        new_end_date_obj = date.fromisoformat(new_end_date)

        # Validation
        if new_end_date_obj < leave.from_date:
            return render(request, "modify_leave.html", {
                "leave": leave,
                "error": "End date cannot be before leave start date."
            })

        if leave.status != "approved":
            return render(request, "modify_leave.html", {
                "leave": leave,
                "error": "Only approved leave can be modified."
            })

        old_to_date = leave.to_date

        # SHORTEN CASE
        if new_end_date_obj < old_to_date:
            leave.to_date = new_end_date_obj
            leave.save()

            from food.models import StudentDailyRecord

            StudentDailyRecord.objects.filter(
                student=student,
                date__gt=new_end_date_obj,
                date__lte=old_to_date
            ).delete()

        # EXTEND CASE
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

    return render(request, "modify_leave.html", {
        "leave": leave
    })


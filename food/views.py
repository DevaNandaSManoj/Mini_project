import math
from datetime import date, timedelta, time
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from .models import DailyMenu, StudentDailyRecord
from leave.models import LeaveRequest
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def send_absent_email(student, absence_date=None):
    """Send an absence notification email to the student's parent via SendGrid."""
    if not student.parent_email:
        return
    recipient = student.parent_email

    if absence_date is None:
        absence_date = date.today()

    formatted_date = absence_date.strftime("%B %d, %Y")

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto;
                border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
        <div style="background: #1a1f36; padding: 24px; text-align: center;">
            <h2 style="color: #38bdf8; margin: 0;">Optimess &mdash; Absence Alert</h2>
        </div>
        <div style="padding: 28px; background: #ffffff;">
            <p style="color: #333; font-size: 15px;">Dear Parent / Guardian,</p>
            <p style="color: #333; font-size: 15px;">
                This is an automated notification to inform you that your ward
                <strong>{student.name}</strong> was marked
                <span style="color: #e53e3e; font-weight: bold;">ABSENT</span>
                from the hostel on <strong>{formatted_date}</strong>.
            </p>
            <p style="color: #333; font-size: 15px;">
                If you have any questions, please contact the hostel administration.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px; text-align: center;">
                This is an automated message from the Optimess Hostel Management System.
                Please do not reply to this email.
            </p>
        </div>
    </div>
    """

    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=recipient,
        subject=f'Absence Notification - {formatted_date} - Optimess',
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"[Optimess] Error sending absence email for {student.name}: {e}")


def send_leave_email(student, from_date, to_date):
    """Send a single leave approval notification email to the student's parent."""
    if not student.parent_email:
        return
    recipient = student.parent_email

    fmt_from = from_date.strftime("%B %d, %Y")
    fmt_to   = to_date.strftime("%B %d, %Y")

    # Single-day leave vs. multi-day leave
    if from_date == to_date:
        date_text = f"on <strong>{fmt_from}</strong>"
        subject_suffix = fmt_from
    else:
        date_text = f"from <strong>{fmt_from}</strong> to <strong>{fmt_to}</strong>"
        subject_suffix = f"{fmt_from} to {fmt_to}"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto;
                border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
        <div style="background: #1a1f36; padding: 24px; text-align: center;">
            <h2 style="color: #38bdf8; margin: 0;">Optimess &mdash; Leave Approved</h2>
        </div>
        <div style="padding: 28px; background: #ffffff;">
            <p style="color: #333; font-size: 15px;">Dear Parent / Guardian,</p>
            <p style="color: #333; font-size: 15px;">
                This is to inform you that the leave request for your ward
                <strong>{student.name}</strong> has been
                <span style="color: #2563eb; font-weight: bold;">APPROVED</span>
                {date_text}.
            </p>
            <p style="color: #333; font-size: 15px;">
                Their attendance will be marked absent and meals will be cancelled
                for this period.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px; text-align: center;">
                This is an automated message from the Optimess Hostel Management System.
                Please do not reply to this email.
            </p>
        </div>
    </div>
    """

    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=recipient,
        subject=f'Leave Approved: {subject_suffix} - Optimess',
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"[Optimess] Error sending leave email for {student.name}: {e}")

def get_client_ip(request):                   #currently not used
    return request.META.get('REMOTE_ADDR')

def verify_college_network(ip):                 #currently not used
    return ip.startswith("192.168.")  # example


# ── Location validation constants ─────────────────────────────────────────────
COLLEGE_LAT        = 9.728714
COLLEGE_LNG        = 76.727813
ALLOWED_RADIUS_KM  = 0.35   # 350 m


def _haversine(lat1, lon1, lat2, lon2):
    """Return great-circle distance in km between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@login_required
def verify_location(request):
    """Guard endpoint: checks GPS coords before attendance is marked.
    Accepts POST with lat & lng. Returns JSON {status, message}.
    Does NOT read or write any attendance/food records.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        lat = float(request.POST.get('lat', ''))
        lng = float(request.POST.get('lng', ''))
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Invalid coordinates received.'}, status=400)

    distance_km = _haversine(lat, lng, COLLEGE_LAT, COLLEGE_LNG)

    if distance_km <= ALLOWED_RADIUS_KM:
        return JsonResponse({
            'status': 'allowed',
            'message': 'You are inside the college area.',
        })
    else:
        return JsonResponse({
            'status': 'blocked',
            'message': 'You are not in the college area. Attendance cannot be marked.',
        })

@login_required
def student_food_attendance(request):

    student = Student.objects.get(user=request.user)

    now = timezone.localtime()
    student_deadline = time(22, 0)  # 10 PM
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

                # Send absent email if student marked themselves absent
                if not attendance_record.present:
                    send_absent_email(student, absence_date=today)

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
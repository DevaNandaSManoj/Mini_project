from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Student, User, Broadcast
from leave.models import LeaveRequest
from food.models import StudentDailyRecord
from django.db import IntegrityError


# ================= ADMIN DASHBOARD =================
def admin_dashboard(request):

    total_students = Student.objects.count()

    total_wardens = User.objects.filter(role='warden').count()

    total_mess = User.objects.filter(role='mess').count()

    pending_leaves = LeaveRequest.objects.filter(status='pending').count()

    context = {
        "total_students": total_students,
        "total_wardens": total_wardens,
        "total_mess": total_mess,
        "pending_leaves": pending_leaves
    }

    return render(request, 'admin/admin_dashboard.html', context)


# ================= STUDENT MANAGEMENT =================
# ================= STUDENT MANAGEMENT =================
def manage_students(request):

    students = Student.objects.all()

    # -------- ADD STUDENT --------
    if request.method == "POST" and request.POST.get("action") == "add":

        username = request.POST.get("username", "").strip()
        full_name = request.POST.get("name")
        room = request.POST.get("room")
        block = request.POST.get("block")
        phone = request.POST.get("phone")
        department = request.POST.get("department")
        parent_email = request.POST.get("parent_email")

        if not username:
            return render(request, "admin/admin_students.html", {
                "students": students,
                "error": "Student ID cannot be empty."
            })

        if User.objects.filter(username=username).exists():
            return render(request, "admin/admin_students.html", {
                "students": students,
                "error": "Student ID already exists"
            })

        try:
            user = User.objects.create_user(
                username=username,
                password=username,
                role="student"
            )
            user.first_name = full_name
            user.save()

            Student.objects.create(
                user=user,
                hostel_block=block,
                room_no=room,
                phone_number=phone,
                department=department,
                parent_email=parent_email
            )
        except IntegrityError:
            # If the user was just created but the student creation failed, delete the user.
            if 'user' in locals():
                user.delete()
            return render(request, "admin/admin_students.html", {
                "students": students,
                "error": "Failed to add student. A constraint failed (e.g. duplicate username or missing field)."
            })


        return redirect('manage_students')


    # -------- DELETE STUDENT --------
    if request.method == "POST" and request.POST.get("action") == "delete":

        student_id = request.POST.get("student_id")

        student = get_object_or_404(Student, id=student_id)

        student.user.delete()

        return redirect('manage_students')


    # -------- UPDATE STUDENT --------
    if request.method == "POST" and request.POST.get("action") == "update":

        student_id = request.POST.get("student_id")

        student = get_object_or_404(Student, id=student_id)

        student.room_no = request.POST.get("room")
        student.hostel_block = request.POST.get("block")
        student.phone_number = request.POST.get("phone")
        student.department = request.POST.get("department")
        student.parent_email = request.POST.get("parent_email")

        student.save()

        return redirect('manage_students')


    return render(request, 'admin/admin_students.html', {
        "students": students
    })


from accounts.models import Warden

# ================= WARDEN MANAGEMENT =================
def manage_wardens(request):
    wardens = Warden.objects.all()

    # -------- ADD WARDEN --------
    if request.method == "POST" and request.POST.get("action") == "add":
        username = request.POST.get("username", "").strip()
        full_name = request.POST.get("name")
        hostel_block = request.POST.get("block")
        phone_number = request.POST.get("phone")

        if User.objects.filter(username=username).exists():
            return render(request, "admin/admin_wardens.html", {
                "wardens": wardens,
                "error": "Warden username already exists"
            })

        try:
            user = User.objects.create_user(
                username=username,
                password=username,
                role="warden"
            )
            user.first_name = full_name
            user.save()

            Warden.objects.create(
                user=user,
                hostel_block=hostel_block,
                phone_number=phone_number
            )
        except IntegrityError:
            return render(request, "admin/admin_wardens.html", {
                "wardens": wardens,
                "error": "Failed to add warden. Username might already be taken."
            })
            
        return redirect('manage_wardens')

    # -------- DELETE WARDEN --------
    if request.method == "POST" and request.POST.get("action") == "delete":
        warden_id = request.POST.get("warden_id")
        warden = get_object_or_404(Warden, id=warden_id)
        warden.user.delete()
        return redirect('manage_wardens')

    # -------- UPDATE WARDEN --------
    if request.method == "POST" and request.POST.get("action") == "update":
        warden_id = request.POST.get("warden_id")
        warden = get_object_or_404(Warden, id=warden_id)
        
        warden.hostel_block = request.POST.get("block")
        warden.phone_number = request.POST.get("phone")
        warden.save()
        return redirect('manage_wardens')

    return render(request, 'admin/admin_wardens.html', {
        "wardens": wardens
    })


# ================= MESS MANAGER MANAGEMENT =================
def manage_mess(request):
    mess_managers = User.objects.filter(role='mess')

    # -------- ADD MESS MANAGER --------
    if request.method == "POST" and request.POST.get("action") == "add":
        username = request.POST.get("username", "").strip()
        full_name = request.POST.get("name")

        if User.objects.filter(username=username).exists():
            return render(request, "admin/admin_mess_managers.html", {
                "mess_managers": mess_managers,
                "error": "Mess Manager username already exists"
            })

        try:
            user = User.objects.create_user(
                username=username,
                password=username,
                role="mess"
            )
            user.first_name = full_name
            user.save()
        except IntegrityError:
            return render(request, "admin/admin_mess_managers.html", {
                "mess_managers": mess_managers,
                "error": "Failed to add Mess Manager. Username might already be taken."
            })
            
        return redirect('manage_mess')

    # -------- DELETE MESS MANAGER --------
    if request.method == "POST" and request.POST.get("action") == "delete":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return redirect('manage_mess')

    # -------- UPDATE MESS MANAGER --------
    if request.method == "POST" and request.POST.get("action") == "update":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)
        user.first_name = request.POST.get("name")
        user.save()
        return redirect('manage_mess')

    return render(request, 'admin/admin_mess_managers.html', {
        "mess_managers": mess_managers
    })


# ================= LEAVE REQUESTS =================
def all_leaves(request):

    if request.method == "POST":
        action = request.POST.get("action")
        leave_id = request.POST.get("leave_id")
        if leave_id and action in ['approve', 'reject']:
            leave = get_object_or_404(LeaveRequest, id=leave_id)
            if action == 'approve':
                leave.status = 'approved'
            elif action == 'reject':
                leave.status = 'rejected'
            leave.seen_by_student = False  # To re-notify the student
            leave.save()
            return redirect('all_leaves')

    pending_leaves = LeaveRequest.objects.filter(status='pending').order_by('-applied_on')
    processed_leaves = LeaveRequest.objects.exclude(status='pending').order_by('-applied_on')

    return render(request, 'admin/all_leaves.html', {
        "pending_leaves": pending_leaves,
        "processed_leaves": processed_leaves
    })


# ================= BROADCASTS =================
def broadcasts(request):

    if request.method == "POST":
        message = request.POST.get("message")
        target_role = request.POST.get("target_role")
        if message and target_role:
            Broadcast.objects.create(
                sender=request.user,
                message=message,
                target_role=target_role
            )
            return redirect('broadcasts')

    broadcasts = Broadcast.objects.all().order_by('-created_at')

    return render(request, 'admin/admin_broadcasts.html', {
        "broadcasts": broadcasts,
        "total_students": Student.objects.count()
    })


# ================= ATTENDANCE REPORT =================
def attendance_report(request):

    records = StudentDailyRecord.objects.all()

    return render(request, 'admin/attendance.html', {
        "records": records
    })


from datetime import date
from django.utils.dateparse import parse_date
from django.db.models import Count, Q

# ================= FOOD REPORT =================
def food_report(request):
    # Filters
    selected_date_str = request.GET.get('date')
    selected_month_str = request.GET.get('month')
    student_id = request.GET.get('student_id')

    # Default to today if neither date nor month is provided
    if not selected_date_str and not selected_month_str:
        selected_date = date.today()
    else:
        selected_date = parse_date(selected_date_str) if selected_date_str else None

    # Base query
    records = StudentDailyRecord.objects.select_related('student__user').all()

    # Apply filters
    if selected_date:
        records = records.filter(date=selected_date)
    elif selected_month_str:
        try:
            year, month = map(int, selected_month_str.split('-'))
            records = records.filter(date__year=year, date__month=month)
        except ValueError:
            pass

    if student_id:
        records = records.filter(student_id=student_id)

    # All active students for dropdown
    all_students = Student.objects.select_related('user').all()
    total_active_students = all_students.count()

    # Metrics
    breakfast_count = 0
    lunch_count = 0
    dinner_count = 0
    selected_any_count = 0

    students_selected = []
    students_not_selected = []

    # If filtering by a specific month, aggregate data differently
    if selected_month_str and not selected_date:
        # For month view, we might just sum up the meal counts
        # and list students who had at least one meal vs none
        student_meal_counts = records.values('student').annotate(
            b_count=Count('id', filter=Q(breakfast=True)),
            l_count=Count('id', filter=Q(lunch=True)),
            d_count=Count('id', filter=Q(dinner=True)),
        )
        
        breakfast_count = sum(item['b_count'] for item in student_meal_counts)
        lunch_count = sum(item['l_count'] for item in student_meal_counts)
        dinner_count = sum(item['d_count'] for item in student_meal_counts)
        
        # Determine who selected any food during the month
        selected_student_ids = [
            item['student'] for item in student_meal_counts 
            if item['b_count'] > 0 or item['l_count'] > 0 or item['d_count'] > 0
        ]
        selected_any_count = len(selected_student_ids)
        
        for student in all_students:
            if student.id in selected_student_ids:
                students_selected.append(student)
            else:
                students_not_selected.append(student)

    else:
        # Daily view logic
        for r in records:
            has_meal = False
            if r.breakfast:
                breakfast_count += 1
                has_meal = True
            if r.lunch:
                lunch_count += 1
                has_meal = True
            if r.dinner:
                dinner_count += 1
                has_meal = True
                
            if has_meal:
                selected_any_count += 1
                students_selected.append(r.student)

        # Find students who didn't select food
        # This includes students who have a record with all False, OR students with no record for the day
        selected_student_ids = [s.id for s in students_selected]
        for student in all_students:
            if student.id not in selected_student_ids:
                students_not_selected.append(student)

    not_selected_count = total_active_students - selected_any_count

    context = {
        'records': records,
        'all_students': all_students,
        'selected_date_str': selected_date_str if selected_date_str else str(date.today()) if not selected_month_str else '',
        'selected_month_str': selected_month_str,
        'selected_student_id': int(student_id) if student_id else '',
        'breakfast_count': breakfast_count,
        'lunch_count': lunch_count,
        'dinner_count': dinner_count,
        'selected_any_count': selected_any_count,
        'not_selected_count': not_selected_count,
        'students_selected': students_selected,
        'students_not_selected': students_not_selected,
    }

    return render(request, 'admin/food_report.html', context)


# ================= MEAL ANALYSIS =================
def meal_analysis(request):

    records = StudentDailyRecord.objects.all()

    return render(request, 'admin/meal_analysis.html', {
        "records": records
    })
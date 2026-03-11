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


# ================= FOOD REPORT =================
def food_report(request):

    records = StudentDailyRecord.objects.all()

    return render(request, 'admin/food_report.html', {
        "records": records
    })


# ================= MEAL ANALYSIS =================
def meal_analysis(request):

    records = StudentDailyRecord.objects.all()

    return render(request, 'admin/meal_analysis.html', {
        "records": records
    })
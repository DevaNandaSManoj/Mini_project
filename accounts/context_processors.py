from .models import Student, Warden, Complaint

def global_context(request):

    if not request.user.is_authenticated:
        return {}

    # 🔹 STUDENT CONTEXT
    if request.user.role == "student":
        try:
            student = Student.objects.select_related("user").get(user=request.user)
            return {"student": student}
        except Student.DoesNotExist:
            return {}

    # 🔹 WARDEN CONTEXT
    if request.user.role == "warden":
        try:
            warden = Warden.objects.select_related("user").get(user=request.user)

            complaint_unseen_count = Complaint.objects.filter(
                student__hostel_block=warden.hostel_block,
                is_seen_by_warden=False
            ).count()

            return {
                "warden": warden,
                "complaint_unseen_count": complaint_unseen_count,
            }

        except Warden.DoesNotExist:
            return {}

    return {}
from .models import Student

def student_context(request):
    if request.user.is_authenticated and request.user.role == "student":
        try:
            student = Student.objects.select_related("user").get(user=request.user)
            return {"student": student}
        except Student.DoesNotExist:
            return {}
    return {}
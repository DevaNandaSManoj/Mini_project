from django.db import models
from accounts.models import Student

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    applied_on = models.DateTimeField(auto_now_add=True)
    seen_by_student = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.student.user.username} ({self.from_date} → {self.to_date})"

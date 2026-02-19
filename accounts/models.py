from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('warden', 'Warden'),
        ('mess', 'Mess Manager'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    def __str__(self):
        return self.username
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hostel_block = models.CharField(max_length=10)
    room_no = models.CharField(max_length=10)

    def __str__(self):
        return self.user.username

class Complaint(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.created_at}"
class Broadcast(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Broadcast - {self.created_at}"

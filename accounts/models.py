from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

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
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    department = models.CharField(max_length=100)
    

    parent_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Warden(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hostel_block = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username

class Complaint(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("resolved", "Resolved"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    is_seen_by_warden = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.status}"

        
BROADCAST_ROLE_CHOICES = (
    ('student', 'Student'),
    ('warden', 'Warden'),
    ('mess', 'Mess Manager'),
)
        
class Broadcast(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_broadcasts"
    )

    message = models.TextField()

    target_role = models.CharField(
        max_length=20,
        choices=BROADCAST_ROLE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # IMPORTANT CHANGE: track read for all users
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="read_broadcasts"
    )

    def __str__(self):
        return f"{self.sender.username} → {self.target_role}"

    def read_count(self):
        return self.read_by.count()

class Attendance(models.Model):
    STATUS_CHOICES = (
        ("present", "Present"),
        ("absent", "Absent"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="present"
    )
    
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.user.username} - {self.date} ({self.status})"

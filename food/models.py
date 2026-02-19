from django.db import models
from accounts.models import Student

class DailyMenu(models.Model):
    date = models.DateField(unique=True)
    breakfast = models.CharField(max_length=200)
    lunch = models.CharField(max_length=200)
    dinner = models.CharField(max_length=200)

    def __str__(self):
        return f"Menu for {self.date}"


class StudentDailyRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()

    # Food should also allow NULL (not selected yet)
    breakfast = models.BooleanField(null=True, blank=True)
    lunch = models.BooleanField(null=True, blank=True)
    dinner = models.BooleanField(null=True, blank=True)

    # Attendance
    present = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.date}"



from django.core.management.base import BaseCommand
from datetime import date
from accounts.models import Student
from food.models import StudentDailyRecord


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        today = date.today()

        students = Student.objects.all()

        for student in students:

            StudentDailyRecord.objects.get_or_create(
                student=student,
                date=today
            )

        self.stdout.write("Daily records generated")
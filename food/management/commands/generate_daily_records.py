from django.core.management.base import BaseCommand
from datetime import date, timedelta
from accounts.models import Student
from food.models import StudentDailyRecord, SystemLog


class Command(BaseCommand):
    help = "Generate daily records including tomorrow food records"

    def handle(self, *args, **kwargs):

        today = date.today()
        tomorrow = today + timedelta(days=1)

        log = SystemLog.objects.first()

        if not log:
            log = SystemLog.objects.create(last_run=today - timedelta(days=1))

        start_date = log.last_run + timedelta(days=1)

        current_date = start_date

        students = Student.objects.all()

        while current_date <= today:

            next_day = current_date + timedelta(days=1)

            for student in students:

                # today's attendance record
                StudentDailyRecord.objects.get_or_create(
                    student=student,
                    date=current_date,
                    defaults={
                        "breakfast": None,
                        "breakfast": None,
                        "lunch": None,
                        "dinner": None,
                    }
                )

                # tomorrow food record
                StudentDailyRecord.objects.get_or_create(
                    student=student,
                    date=next_day
                )

            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS("Attendance and food records generated"))
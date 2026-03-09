from django.core.management.base import BaseCommand
from datetime import date, timedelta
from food.models import StudentDailyRecord


class Command(BaseCommand):
    help = "Auto close attendance and food records"

    def handle(self, *args, **kwargs):

        today = date.today()
        yesterday = today - timedelta(days=1)

        # 1️⃣ Close yesterday attendance
        attendance_records = StudentDailyRecord.objects.filter(
            date=yesterday,
            present__isnull=True
        )

        for record in attendance_records:
            record.present = False
            record.marked_by = "auto"
            record.save()

        # 2️⃣ Close today food records
        food_records = StudentDailyRecord.objects.filter(
            date=today,
            breakfast__isnull=True
        ) | StudentDailyRecord.objects.filter(
            date=today,
            lunch__isnull=True
        ) | StudentDailyRecord.objects.filter(
            date=today,
            dinner__isnull=True
        )

        for record in food_records:

            changed = False

            if record.breakfast is None:
                record.breakfast = False
                changed = True

            if record.lunch is None:
                record.lunch = False
                changed = True

            if record.dinner is None:
                record.dinner = False
                changed = True

            if changed:
                record.save()

        self.stdout.write(self.style.SUCCESS("Daily records auto-closed"))
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from food.models import StudentDailyRecord, SystemLog


class Command(BaseCommand):
    help = "Auto close attendance and food records for all missed days"

    def handle(self, *args, **kwargs):

        today = date.today()

        # get last run date
        log = SystemLog.objects.first()

        if not log:
            # first run
            log = SystemLog.objects.create(last_run=today - timedelta(days=1))

        start_date = log.last_run + timedelta(days=1)

        current_date = start_date

        while current_date <= today:

            yesterday = current_date - timedelta(days=1)

            # close attendance
            attendance_records = StudentDailyRecord.objects.filter(
                date=yesterday,
                present__isnull=True
            )

            for record in attendance_records:
                record.present = False
                record.marked_by = "auto"
                record.save()

            # close food
            food_records = StudentDailyRecord.objects.filter(
                date=current_date
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

            current_date += timedelta(days=1)

        log.last_run = today
        log.save()

        self.stdout.write(self.style.SUCCESS("All missed days processed"))
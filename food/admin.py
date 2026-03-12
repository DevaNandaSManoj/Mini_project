from django.contrib import admin
from .models import DailyMenu, StudentDailyRecord, SystemLog

admin.site.register(DailyMenu)
admin.site.register(StudentDailyRecord)
admin.site.register(SystemLog)
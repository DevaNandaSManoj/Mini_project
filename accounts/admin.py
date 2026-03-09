from django.contrib import admin
from .models import Broadcast , Warden, Complaint, User, Student
 
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Broadcast)
admin.site.register(Warden)
admin.site.register(Complaint)

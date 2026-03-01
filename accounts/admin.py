from django.contrib import admin
from .models import User, Student
from .models import Broadcast , Warden
 
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Broadcast)
admin.site.register(Warden)
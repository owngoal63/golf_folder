#golf/admin.py
from django.contrib import admin

from golf.models import Course, Round, DiffAjustment, GolfGroup, Buddy

admin.site.register(Course)
admin.site.register(Round)
admin.site.register(DiffAjustment)
admin.site.register(GolfGroup)
admin.site.register(Buddy)
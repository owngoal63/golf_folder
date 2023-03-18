#golf/admin.py
from django.contrib import admin

from golf.models import *

admin.site.register(Course)
admin.site.register(Round)
admin.site.register(DiffAjustment)
admin.site.register(GolfGroup)
admin.site.register(Buddy)
admin.site.register(Score)
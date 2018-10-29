from django.contrib import admin

from .models import Concept, DailyInput
# Register your models here.
admin.site.register(Concept)
admin.site.register(DailyInput)

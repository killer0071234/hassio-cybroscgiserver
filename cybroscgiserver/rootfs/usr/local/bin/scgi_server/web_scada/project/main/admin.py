from django.contrib import admin
from project.main.models import *


class UpdatePeriodAdmin(admin.ModelAdmin):
    ordering = ("period",)


admin.site.register(CustomUser)
admin.site.register(Template)
admin.site.register(UserPermissions)
admin.site.register(Page)
admin.site.register(UpdatePeriod, UpdatePeriodAdmin)
admin.site.register(Alarm)
admin.site.register(Measurement)
admin.site.register(Controller)

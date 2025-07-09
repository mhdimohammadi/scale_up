from django.contrib import admin
from .models import Flag, FlagDependency,AuditLog


admin.site.register(FlagDependency)
admin.site.register(AuditLog)


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ['name','is_active']
    list_editable = ('is_active',)
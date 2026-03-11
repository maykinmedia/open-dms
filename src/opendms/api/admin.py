from django.contrib import admin

from .models import ZGWApiGroupConfig


@admin.register(ZGWApiGroupConfig)
class ZGWApiGroupConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "identifier",
        "zrc_service",
        "drc_service",
        "ztc_service",
    )
    search_fields = ("name", "identifier")
    prepopulated_fields = {"identifier": ["name"]}
    ordering = ("id", "name")

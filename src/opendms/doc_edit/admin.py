from django.contrib import admin

from .models import BaseDriveDocument, BaseDriveSubscription


@admin.register(BaseDriveSubscription)
class BaseDriveSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "subscription_id",
        "resource",
        "expiration_date_time",
        "updated_at",
        "created_at",
    ]
    search_fields = ["subscription_id", "resource", "notification_url"]
    readonly_fields = [
        "subscription_id",
        "client_state",
        "token",
        "resource",
        "notification_url",
        "expiration_date_time",
        "delta_url",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]


@admin.register(BaseDriveDocument)
class BaseDriveDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "document_id",
        "document_name",
        "updated_at",
        "created_at",
    ]
    readonly_fields = [
        "document_id",
        "document_name",
        "updated_at",
        "created_at",
    ]
    ordering = ["-created_at"]

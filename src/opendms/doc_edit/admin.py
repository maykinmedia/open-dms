from django.contrib import admin

from .backends.ms_graph_api.models import GraphSubscription


@admin.register(GraphSubscription)
class GraphSubscriptionAdmin(admin.ModelAdmin):
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

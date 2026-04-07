from django.db import models


class GraphSubscription(models.Model):
    subscription_id = models.CharField(max_length=255, unique=True)
    client_state = models.CharField(max_length=255)
    resource = models.CharField(max_length=255)
    notification_url = models.CharField(max_length=500)
    expiration_date_time = models.DateTimeField()
    delta_url = models.CharField(max_length=500, blank=True)
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "graph_subscriptions"

    def __str__(self):
        return f"{self.subscription_id} - {self.resource}"

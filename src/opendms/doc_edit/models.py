from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseDriveSubscription(models.Model):
    """
    Model representing a webhook subscription for any cloud storage driver.
    """

    subscription_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_(
            "Unique identifier returned by the storage provider when the subscription is created."
        ),
    )
    client_state = models.CharField(
        max_length=255,
        help_text=_(
            "Secret string used to validate that notifications are coming from the storage provider."
        ),
    )
    resource = models.CharField(
        max_length=255,
        help_text=_("The resource path being monitored, e.g. '/me/drive/root/'."),
    )
    notification_url = models.CharField(
        max_length=500,
        help_text=_(
            "The webhook URL where the storage provider sends change notifications."
        ),
    )
    expiration_date_time = models.DateTimeField(
        db_index=True,
        help_text=_(
            "Expiration timestamp of the subscription. Must be renewed before this date."
        ),
    )
    delta_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text=_(
            "The deltaLink URL returned by the last delta query. Used to fetch only changed items."
        ),
    )
    token = models.TextField(
        help_text=_(
            "OAuth2 access token used to authenticate requests to the storage provider."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "base drive subscription"
        verbose_name_plural = "base drive subscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subscription_id} - {self.resource}"

    @property
    def is_expired(self) -> bool:
        """Returns True if the subscription has already expired."""
        return self.expiration_date_time < timezone.now()

    @property
    def is_expiring_soon(self, threshold_hours: int = 24) -> bool:
        """Returns True if the subscription expires within the given threshold (default 24h)."""
        return self.expiration_date_time < timezone.now() + timezone.timedelta(
            hours=threshold_hours
        )


class BaseDriveDocument(models.Model):
    """
    Model representing a file tracked from any cloud storage driver.
    """

    document_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text=_("The unique identifier of the file on the storage provider."),
    )
    document_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=_(
            "The display name of the file as it appears on the storage provider."
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_(
            "Timestamp when this record was first created in the local database."
        ),
    )
    updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "Timestamp of the last detected modification on the remote file. Null if never updated."
        ),
    )

    class Meta:
        verbose_name = "base drive document"
        verbose_name_plural = "base drive documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.document_name

    @property
    def has_been_modified(self) -> bool:
        """Returns True if the document has been modified at least once since creation."""
        return self.updated_at is not None

from django.db import models
from django.utils.translation import gettext_lazy as _


class SortChoices(models.TextChoices):
    relevance = "relevance", _("Relevance")
    chronological = "chronological", _("Chronological")

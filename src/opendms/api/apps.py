from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    name = "opendms.api"
    verbose_name = _("API's Config")

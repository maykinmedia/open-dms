from django.db import models
from django.utils.translation import gettext_lazy as _

from zgw_consumers.constants import APITypes


class ZGWApiGroupConfig(models.Model):
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this set of ZGW APIs."),
    )
    identifier = models.SlugField(
        _("identifier"),
        blank=False,
        null=False,
        unique=True,
        help_text=_("A unique, human-friendly identifier to identify this group."),
    )
    zrc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Zaken API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="zgwset_zrc_config",
        null=False,
    )
    # Enforces a one-to-one constraint: each ZTC service can belong to only one group.
    ztc_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Catalogi API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.ztc},
        related_name="zgwset_ztc_config",
    )
    drc_service = models.ForeignKey(
        "zgw_consumers.Service",
        verbose_name=_("Documenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.drc},
        related_name="zgwset_drc_config",
        null=False,
    )

    class Meta:
        verbose_name = _("ZGW API groups")
        verbose_name_plural = _("ZGW API groups")

    def __str__(self):
        return self.name

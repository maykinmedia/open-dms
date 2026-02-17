from django.urls import path

from opendms.accounts.api.views import WhoAmIView

urlpatterns = [
    path("whoami", WhoAmIView.as_view(), name="whoami"),
]

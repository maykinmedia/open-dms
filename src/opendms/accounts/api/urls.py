from django.urls import path

from opendms.accounts.api.views import WhoAmIView, LoginView

app_name = "accounts:api"

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("whoami", WhoAmIView.as_view(), name="whoami"),
]

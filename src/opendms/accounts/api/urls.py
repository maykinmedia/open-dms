from django.urls import path

from opendms.accounts.api.views import LoginView, LogoutView, WhoAmIView

app_name = "accounts:api"


urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("whoami", WhoAmIView.as_view(), name="whoami"),
]

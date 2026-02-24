from django.urls import include, path, re_path

from vng_api_common import routers

from opendms.accounts.api.views import LoginView, LogoutView, WhoAmIView

app_name = "accounts"

router = routers.DefaultRouter()

urlpatterns = [
    re_path(
        r"^v(?P<version>\d+)/accounts/",
        include(
            [
                path("login", LoginView.as_view(), name="login"),
                path("logout", LogoutView.as_view(), name="logout"),
                path("whoami", WhoAmIView.as_view(), name="whoami"),
            ]
        ),
    ),
]

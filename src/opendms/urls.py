from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from maykin_2fa import monkeypatch_admin
from maykin_2fa.urls import urlpatterns, webauthn_urlpatterns
from maykin_common.accounts.views import PasswordResetView
from mozilla_django_oidc_db.views import AdminLoginFailure

from opendms.api.viewsets import MsAuthCallbackView

# Configure admin

monkeypatch_admin()

handler500 = "maykin_common.views.server_error"

admin.site.enable_nav_sidebar = False
admin.site.site_header = "opendms admin"
admin.site.site_title = "opendms admin"
admin.site.index_title = "opendms dashboard"

# URL routing

urlpatterns = [
    path(
        "admin/password_reset/",
        PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    # OIDC urls
    path("admin/login/failure/", AdminLoginFailure.as_view(), name="admin-oidc-error"),
    path("auth/oidc/", include("mozilla_django_oidc.urls")),
    # TODO check this url
    path("oidc/callback/", MsAuthCallbackView.as_view(), name="ms_auth_callback"),
    # Use custom login views for the admin + support hardware tokens
    path("admin/", include((urlpatterns, "maykin_2fa"))),
    path("admin/", include((webauthn_urlpatterns, "two_factor"))),
    path("admin/hijack/", include("hijack.urls")),
    path("admin/", admin.site.urls),
    path("ref/", include("vng_api_common.urls")),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("", include("maykin_common.health_checks.urls")),
    # API
    path("api/", include("opendms.api.urls", namespace="api")),
    # Handover to (React) frontend.
    re_path(
        r"^(?:.*)/?$", TemplateView.as_view(template_name="index.html"), name="frontend"
    ),
]

# NOTE: The staticfiles_urlpatterns also discovers static files (ie. no need to run
# collectstatic). Both the static folder and the media folder are only served via Django
# if DEBUG = True.
urlpatterns += staticfiles_urlpatterns() + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG and apps.is_installed("debug_toolbar"):
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

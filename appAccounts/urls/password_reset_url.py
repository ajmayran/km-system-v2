# Description: URL configuration for the registration view and account activations
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAccounts.views import (
    update_password_view,
    reset_pass_email_view,
    reset_password_view,
)

app_name = "appAccounts"

urlpatterns = (
    [
        path(
            "update-password/",
            update_password_view.update_password,
            name="update-password",
        ),
        path(
            "reset-pass?/<uidb64>/<token>",
            reset_pass_email_view.reset_pass_email,
            name="reset-pass-confirm",
        ),
        path("new-pass/", reset_password_view.reset_password, name="new-password"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

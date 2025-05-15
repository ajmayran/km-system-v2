# Add this to your appAccounts/urls.py file
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAccounts.views import cmi_change_pass_view

app_name = "appAccounts"

urlpatterns = (
    [
        path(
            "send-reset-password-link/",
            cmi_change_pass_view.send_reset_password_link,
            name="send-reset-password-link",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

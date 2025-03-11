# Description: URL configuration for the registration view and account activations
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAccounts.views import account_activate_view

app_name = "appAccounts"

urlpatterns = (
    [
        path(
            "activate/<uidb64>/<token>",
            account_activate_view.activate,
            name="activate-account",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

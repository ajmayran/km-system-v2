# Description: URL configuration for the registration view and account activations
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAccounts.views import request_new_activation_code_view

app_name = "appAccounts"

urlpatterns = (
    [
        path(
            "request-new-code?/",
            request_new_activation_code_view.request_new_activation_code,
            name="new-code",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import handler403, handler404

app_name = "appErrors"

urlpatterns = (
    [
        path("403/", handler403, name="error-403"),
        path("404/", handler404, name="error-404"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

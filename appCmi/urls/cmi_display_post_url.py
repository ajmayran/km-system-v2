from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_display_post

app_name = "appCmi"

urlpatterns = (
    [
        path(
            "knowledge-resources/post/<slug:slug>/",
            cmi_display_post,
            name="cmi-display-post",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

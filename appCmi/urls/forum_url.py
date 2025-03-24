from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import forum_view

app_name = "appCmi"

urlpatterns = (
    [
        path("forum/", forum_view.cmi_forum, name="cmi-forum"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

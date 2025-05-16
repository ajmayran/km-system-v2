from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import message_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("messages/", message_view.message_from_cmi, name="message-from-cmi"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

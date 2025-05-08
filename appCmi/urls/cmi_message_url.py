from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_message_view

app_name = "appCmi"

urlpatterns = (
    [
        path("message/", cmi_message_view.message, name="message"),
        path("message/submit/", cmi_message_view.send_message, name="send_message"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

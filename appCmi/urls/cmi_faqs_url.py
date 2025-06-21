from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_faqs_view

app_name = "appCmi"

urlpatterns = (
    [
        path("faqs/", cmi_faqs_view.faqs_view, name="faqs"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
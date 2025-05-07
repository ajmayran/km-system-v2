from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_knowledge_resources_view

app_name = "appCmi"

urlpatterns = (
    [
        path(
            "knowledge-resources/",
            cmi_knowledge_resources_view.cmi_knowledge_resources,
            name="all-knowledge-resources",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

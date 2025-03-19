from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import knowledge_resources_view

app_name = "appAdmin"

urlpatterns = (
    [
        path(
            "knowledge-resources/",
            knowledge_resources_view.admin_knowledge_resources,
            name="display-knowledge-resources",
        ),
        path(
            "new-knowledge-resources/",
            knowledge_resources_view.admin_add_knowledge_resource,
            name="add-knowledge-resources",
        ),
        path(
            "update-knowledge-resources/<str:slug>/",
            knowledge_resources_view.admin_edit_knowledge_resource,
            name="update-knowledge-resources",
        ),
        path(
            "delete-knowledge-resources/<str:slug>/",
            knowledge_resources_view.admin_delete_knowledge_resource,
            name="delete-knowledge-resources",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

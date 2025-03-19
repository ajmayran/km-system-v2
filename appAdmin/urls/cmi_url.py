from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import cmi_view

app_name = "appAdmin"

urlpatterns = (
    [
        path(
            "cmi/",
            cmi_view.admin_cmi,
            name="display-cmi",
        ),
        path(
            "new-cmi/",
            cmi_view.admin_add_cmi,
            name="add-cmi",
        ),
        path(
            "update-cmi/<str:slug>/",
            cmi_view.admin_edit_cmi,
            name="update-cmi",
        ),
        path(
            "delete-cmi/<str:slug>/",
            cmi_view.admin_delete_cmi,
            name="delete-cmi",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import commodities_view

app_name = "appAdmin"

urlpatterns = (
    [
        path(
            "commodities/",
            commodities_view.admin_commodities,
            name="display-commodities",
        ),
        path(
            "add-commodity/",
            commodities_view.admin_add_commodity,
            name="add-commodity",
        ),
        path(
            "edit-commodity/<str:slug>/",
            commodities_view.admin_edit_commodity,
            name="edit-commodity",
        ),
        path(
            "delete-commodity/<str:slug>/",
            commodities_view.admin_delete_commodity,
            name="delete-commodity",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

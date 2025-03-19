from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import useful_link_view

app_name = "appAdmin"

urlpatterns = (
    [
        path(
            "useful-links/",
            useful_link_view.admin_useful_links,
            name="admin-useful-links",
        ),
        path(
            "add-useful-links/",
            useful_link_view.admin_add_useful_link,
            name="add-useful-links",
        ),
        path(
            "update-useful-links/",
            useful_link_view.admin_edit_useful_link,
            name="update-useful-links",
        ),
        path(
            "delete-useful-links/",
            useful_link_view.admin_delete_useful_link,
            name="delete-useful-links",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

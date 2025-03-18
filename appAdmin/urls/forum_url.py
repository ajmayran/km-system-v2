from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import forum_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("forum/", forum_view.manage_forum, name="manage-forum"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import display_map_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("map/", display_map_view.display_map, name="display-map"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

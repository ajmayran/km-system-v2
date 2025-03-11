from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import home_view

app_name = "appCmi"

urlpatterns = (
    [
        path("home/", home_view.home, name="home"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

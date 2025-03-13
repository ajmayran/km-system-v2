from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import users_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("users/", users_view.display_users, name="display-users"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

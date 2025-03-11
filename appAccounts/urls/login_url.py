from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAccounts.views import login_view

app_name = "appAccounts"

urlpatterns = (
    [
        path("", login_view.login, name="login"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

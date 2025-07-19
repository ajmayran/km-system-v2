from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", include(("appAccounts.urls", "appAccounts"))),
    path("cmis/", include(("appCmi.urls", "appCmi"))),
    path("admin/", include(("appAdmin.urls", "appAdmin"))),
    path("errors/", include(("appErrors.urls", "appErrors"))),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

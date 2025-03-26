from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_commodities_view

app_name = "appCmi"

urlpatterns = (
    [
        path(
            "commodities/", cmi_commodities_view.all_commodities, name="all-commodities"
        ),
        path(
            "commodities/<slug:slug>/",
            cmi_commodities_view.display_commodity,
            name="display-commodity",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

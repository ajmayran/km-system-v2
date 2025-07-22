from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_about_view
from appCmi.views.cmi_about_view import cmi_project_detail

app_name = "appCmi"

urlpatterns = (
    [
        path('cmi-about', cmi_about_view.cmi_about, name='cmi-about'),
        path('cmis/project/<int:about_id>/', cmi_project_detail, name='project'),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

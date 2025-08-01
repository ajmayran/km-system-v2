from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views.project_view import project_detail, project_sub_view
from appCmi.views import home_view

app_name = "appCmi"

urlpatterns = [
    path("project/<int:about_id>/", project_detail, name="project"),
    path("project-sub/<int:sub_id>/", project_sub_view, name="project-sub"),
    path("home/", home_view.home, name="home"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
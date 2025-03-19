from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import about_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("about/", about_view.admin_about_page, name="about-page"),
        path("footer/", about_view.admin_about_footer, name="about-footer"),
        path("about/edit/", about_view.admin_about_page_edit, name="about-page-edit"),
        path(
            "footer/edit/", about_view.admin_about_footer_edit, name="about-footer-edit"
        ),
        path("upload-video/", about_view.admin_upload_video, name="admin-video-upload"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_user_profile_view

app_name = "appCmi"

urlpatterns = (
    [
        path(
            "profile/",
            cmi_user_profile_view.display_cmi_profile,
            name="cmi-profile",
        ),
        path(
            "upload-profile-picture/",
            cmi_user_profile_view.upload_profile_picture,
            name="upload-profile",
        ),
        path(
            "profile/update-user-info/",
            cmi_user_profile_view.update_user_info,
            name="update_user_info",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

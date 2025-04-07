from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import forum_view

app_name = "appAdmin"

urlpatterns = (
    [
        path("admin-forum/", forum_view.manage_forum, name="manage-forum"),
        path(
            "admin-forum/comments/<slug:slug>/",
            forum_view.get_comments_per_forum_post,
            name="get-comments-per-forum-post",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

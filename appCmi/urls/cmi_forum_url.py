from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_forum_view

app_name = "appCmi"

urlpatterns = (
    [
        path("forum/", cmi_forum_view.cmi_forum, name="cmi-forum"),
        path(
            "forum/post-question/",
            cmi_forum_view.forum_post_question,
            name="forum-post-question",
        ),
        path("forum/<slug:slug>/", cmi_forum_view.display_forum, name="display-forum"),
        path(
            "forum/<slug:slug>/add-comment/",
            cmi_forum_view.forum_add_comment,
            name="forum-add-comment",
        ),
        path(
            "forum/<slug:slug>/like/",
            cmi_forum_view.toggle_forum_like,
            name="toggle-forum-like",
        ),
        path(
            "forum/<slug:slug>/bookmark/",
            cmi_forum_view.toggle_forum_bookmark,
            name="toggle-forum-bookmark",
        ),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

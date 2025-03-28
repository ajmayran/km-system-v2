from utils.get_models import get_active_models
from django.shortcuts import render
from appCmi.forms import ForumForm, ForumCommentForm
from appCmi.models import Forum, ForumComment
from django.shortcuts import redirect, get_object_or_404
import logging
from django.contrib import messages
from appAdmin.models import Commodity
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def cmi_forum(request):
    """Handles forum data aggregation and rendering for the forum page."""

    # Fetch active models
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    # Fetch all discussions for display
    forums = Forum.objects.all().order_by("-date_posted")

    context = {
        "commodities": commodities,
        "useful_links": useful_links,
        "knowledge_resources": knowledge_resources,
        "forums": forums,
    }

    return render(request, "pages/cmi-forum.html", context)


def forum_post_question(request):
    if request.method == "POST":
        form = ForumForm(request.POST)
        if form.is_valid():
            try:
                forum = form.save(commit=False)
                forum.author = request.user
                forum.save()

                # Handle commodities
                commodity_ids = request.POST.get("commodity_ids", "")
                if commodity_ids:
                    _associate_commodities_with_forum(forum, commodity_ids)

                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "success": True,
                            "post": {
                                "title": forum.forum_title,
                                "question": forum.forum_question,
                                "author": f"{forum.author.first_name} {forum.author.last_name}",
                                "date": forum.date_posted.strftime("%B %d, %Y"),
                                "commodities": [
                                    str(c) for c in forum.commodity_id.all()
                                ],
                                "commodity_ids": commodity_ids,
                            },
                        }
                    )

                messages.success(request, "Your question has been posted successfully.")
                return redirect("appCmi:cmi-forum")
            except Exception as e:
                logger.error(f"Error in forum post: {str(e)}")
                return JsonResponse({"success": False, "message": str(e)})
        else:
            logger.error(f"Form invalid: {form.errors}")

    return render(request, "pages/cmi-forum.html", {"form": ForumForm()})


def _associate_commodities_with_forum(forum, commodity_ids_string):
    """
    Helper function to associate commodities with a forum post.

    Args:
        forum: The Forum model instance
        commodity_ids_string: Comma-separated string of commodity IDs
    """
    if not commodity_ids_string:
        return

    commodity_ids = commodity_ids_string.split(",")
    logger.debug(f"Processing commodity IDs: {commodity_ids}")

    # Bulk fetch commodities to minimize database queries
    if commodity_ids:
        selected_commodities = Commodity.objects.filter(commodity_id__in=commodity_ids)

        # Add all selected commodities to the forum in one operation
        forum.commodity_id.add(*selected_commodities)


def display_forum(request, slug):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    # Get the forum directly from the database using slug
    try:
        display_forum = Forum.objects.get(slug=slug)
        if request.user.is_authenticated:
            display_forum.is_liked_by = display_forum.is_liked_by(request.user)
            display_forum.is_bookmarked_by = display_forum.is_bookmarked_by(
                request.user
            )

        # Get all active comments for this forum
        comments = ForumComment.objects.filter(post=display_forum, status="active")
        comment_counts = comments.count()

    except Forum.DoesNotExist:
        return render(request, "404.html", status=404)

    context = {
        "display_forum": display_forum,
        "comments": comments,
        "comment_counts": comment_counts,
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-display-forum.html", context)


def forum_add_comment(request, slug):
    forum_post = get_object_or_404(Forum, slug=slug)

    if request.method == "POST":
        form = ForumCommentForm(request.POST, user=request.user, post=forum_post)
        if form.is_valid():
            form.save()
            return redirect("appCmi:display-forum", slug=slug)
    else:
        form = ForumCommentForm()

    # Get all comments with their replies for display
    comments = forum_post.post_comments.filter(
        parent=None
    )  # Get only top-level comments

    context = {
        "forum_post": forum_post,
        "comments": comments,
        "form": form,
    }
    return render(request, "cmi-display-forum.html", context)


@login_required
def toggle_forum_like(request, slug):
    try:
        forum = get_object_or_404(Forum, slug=slug)

        if forum.likes.filter(id=request.user.id).exists():
            forum.likes.remove(request.user)
            is_liked = False
        else:
            forum.likes.add(request.user)
            is_liked = True

        return JsonResponse(
            {"success": True, "is_liked": is_liked, "total_likes": forum.total_likes()}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def toggle_forum_bookmark(request, slug):
    try:
        forum = get_object_or_404(Forum, slug=slug)

        if forum.bookmark.filter(id=request.user.id).exists():
            forum.bookmark.remove(request.user)
            is_bookmarked = False
        else:
            forum.bookmark.add(request.user)
            is_bookmarked = True

        return JsonResponse({"success": True, "is_bookmarked": is_bookmarked})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

from utils.get_models import get_active_models
from django.shortcuts import render
from appCmi.forms import ForumForm
from appCmi.models import Forum
from django.shortcuts import redirect
import logging
from django.contrib import messages
from appAdmin.models import Commodity
from django.http import JsonResponse

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
    commodities = models.get("commodities", [])  # List of active commodities
    knowledge_resources = models.get("knowledge_resources", [])
    forums = Forum.objects.all()

    # Find the specific commodity in the list
    display_forum = next((f for f in forums if f.slug == slug), None)

    if not display_forum:
        return render(request, "404.html", status=404)  # Return a 404 page if not found

    context = {
        "display_forum": display_forum,
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-display-forum.html", context)

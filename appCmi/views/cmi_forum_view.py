from utils.get_models import get_active_models
from appCmi.models import Forum
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count


def cmi_forum(request):
    """Handles forum data aggregation and rendering for the forum page."""

    # Fetch active models
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    context = {
        "commodities": commodities,
        "useful_links": useful_links,
        "knowledge_resources": knowledge_resources,
    }

    return render(request, "pages/cmi-forum.html", context)

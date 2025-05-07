from utils.get_models import get_active_models
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


def cmi_knowledge_resources(request):
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
    return render(request, "pages/cmi-knowledge-resources.html", context)

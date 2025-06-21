from django.shortcuts import render
from utils.user_control import user_access_required
from utils.get_models import get_active_models

@user_access_required(["admin", "cmi"], error_type=404)
def faqs_view(request):
    """View function for the FAQs page."""
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    
    context = {
        "title": "FAQs",
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-faqs.html", context)

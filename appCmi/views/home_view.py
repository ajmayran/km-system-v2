from django.shortcuts import render
from utils.get_models import get_active_models


# Create your views here.
def home(request):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    context = {
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/home.html", context)

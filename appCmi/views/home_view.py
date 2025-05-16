from django.shortcuts import render
from utils.get_models import get_active_models
from utils.user_control import user_access_required


# Create your views here.
@user_access_required(["admin", "cmi"], error_type=404)
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

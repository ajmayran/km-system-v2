from django.shortcuts import render
from utils.get_models import get_active_models
from utils.user_control import user_access_required
from utils.search_function import find_similar_resources
from appCmi.models import FAQ
from django.db.models import Count



def home(request):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    top_faqs = FAQ.objects.filter(is_active=True).annotate(
        view_count=Count('views')
    ).order_by('-view_count')[:4]

    context = {
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "top_faqs": top_faqs, 
    }
    return render(request, "pages/home.html", context)


def get_input_from_search(request):
    query = request.GET.get("q", "").strip()  # safely get 'q' and remove whitespace

    if query:
        similar_resources = find_similar_resources(query)
    else:
        similar_resources = []

    context = {"query": query, "results": similar_resources}

    return render(request, "pages/cmi-search-result.html", context)

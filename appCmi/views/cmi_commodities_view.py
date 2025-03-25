from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils.get_models import get_active_models


def all_commodities(request):
    """
    View function for displaying all commodities.

    Fetches all active commodities from the database and displays them in a
    paginated grid layout with filtering options.
    """
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    # Pagination
    page = request.GET.get("page", 1)
    commodities_per_page = 9  # Adjust as needed
    paginator = Paginator(commodities, commodities_per_page)

    try:
        paginated_commodities = paginator.page(page)
    except PageNotAnInteger:
        paginated_commodities = paginator.page(1)
    except EmptyPage:
        paginated_commodities = paginator.page(paginator.num_pages)

    context = {
        "useful_links": useful_links,
        "commodities": paginated_commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/commodities/all-commodities.html", context)

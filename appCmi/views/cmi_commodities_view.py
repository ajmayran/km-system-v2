from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils.get_models import get_active_models
from appCmi.models import Forum
from utils.user_control import user_access_required
from appAdmin.models import About


@user_access_required(["admin", "cmi"], error_type=404)
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
    about_list = About.objects.all() 
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
        "about_list": about_list,
    }
    return render(request, "pages/cmi-commodities.html", context)


@user_access_required(["admin", "cmi"], error_type=404)
def display_commodity(request, slug):
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])  # List of active commodities
    knowledge_resources = models.get("knowledge_resources", [])

    # Find the specific commodity in the list
    display_commodity = next((c for c in commodities if c.slug == slug), None)

    if not display_commodity:
        return render(request, "404.html", status=404)  # Return a 404 page if not found

    context = {
        "display_commodity": display_commodity,
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-display-commodity.html", context)

from utils.get_models import get_active_models
from appAdmin.models import ResourceMetadata, Tag, KnowledgeResources
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from django.shortcuts import render
import logging
from appCmi.templatetags import get_knowledge_title

logger = logging.getLogger(__name__)


def cmi_knowledge_resources(request):
    """View function for the knowledge resources page."""

    # Fetch active models
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    # Get all approved resource metadata
    all_resources = ResourceMetadata.objects.filter(is_approved=True).order_by(
        "-created_at"
    )
    # Fetch resources by type
    events = (
        ResourceMetadata.objects.filter(resource_type="event", is_approved=True)
        .prefetch_related("event")
        .order_by("-created_at")
    )

    info_systems = (
        ResourceMetadata.objects.filter(resource_type="info_system", is_approved=True)
        .prefetch_related("information_system")
        .order_by("-created_at")
    )

    maps = (
        ResourceMetadata.objects.filter(resource_type="map", is_approved=True)
        .prefetch_related("map")
        .order_by("-created_at")
    )

    media = (
        ResourceMetadata.objects.filter(resource_type="media", is_approved=True)
        .prefetch_related("media")
        .order_by("-created_at")
    )

    news_items = (
        ResourceMetadata.objects.filter(resource_type="news", is_approved=True)
        .prefetch_related("news")
        .order_by("-created_at")
    )

    policies = (
        ResourceMetadata.objects.filter(resource_type="policy", is_approved=True)
        .prefetch_related("policy")
        .order_by("-created_at")
    )

    projects = (
        ResourceMetadata.objects.filter(resource_type="project", is_approved=True)
        .prefetch_related("project")
        .order_by("-created_at")
    )

    publications = (
        ResourceMetadata.objects.filter(resource_type="publication", is_approved=True)
        .prefetch_related("publication")
        .order_by("-created_at")
    )

    technologies = (
        ResourceMetadata.objects.filter(resource_type="technology", is_approved=True)
        .prefetch_related("technology")
        .order_by("-created_at")
    )

    trainings = (
        ResourceMetadata.objects.filter(resource_type="training", is_approved=True)
        .prefetch_related("training_seminar")
        .order_by("-created_at")
    )

    webinars = (
        ResourceMetadata.objects.filter(resource_type="webinar", is_approved=True)
        .prefetch_related("webinar")
        .order_by("-created_at")
    )

    products = (
        ResourceMetadata.objects.filter(resource_type="product", is_approved=True)
        .prefetch_related("product")
        .order_by("-created_at")
    )

    # Get featured resources
    featured_resources = ResourceMetadata.objects.filter(
        is_approved=True, is_featured=True
    ).order_by("-created_at")

    # Get all tags for filtering
    all_tags = Tag.objects.all()

    # Handle tag filtering if provided
    tag_filter = request.GET.get("tag")
    if tag_filter:
        try:
            tag = Tag.objects.get(slug=tag_filter)
            all_resources = all_resources.filter(tags=tag)
            events = events.filter(tags=tag)
            info_systems = info_systems.filter(tags=tag)
            maps = maps.filter(tags=tag)
            media = media.filter(tags=tag)
            news_items = news_items.filter(tags=tag)
            policies = policies.filter(tags=tag)
            projects = projects.filter(tags=tag)
            publications = publications.filter(tags=tag)
            technologies = technologies.filter(tags=tag)
            trainings = trainings.filter(tags=tag)
            webinars = webinars.filter(tags=tag)
            products = products.filter(tags=tag)
        except Tag.DoesNotExist:
            pass

    # Handle search query if provided
    search_query = request.GET.get("q")
    if search_query:
        all_resources = all_resources.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        events = events.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        info_systems = info_systems.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        maps = maps.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        media = media.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        news_items = news_items.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        policies = policies.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        projects = projects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        publications = publications.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        technologies = technologies.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        trainings = trainings.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        webinars = webinars.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        products = products.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        # Existing context
        "commodities": commodities,
        "useful_links": useful_links,
        "knowledge_resources": knowledge_resources,
        # All resources
        "all_resources": all_resources,
        # Resources by type
        "events": events,
        "info_systems": info_systems,
        "maps": maps,
        "media": media,
        "news_items": news_items,
        "policies": policies,
        "projects": projects,
        "publications": publications,
        "technologies": technologies,
        "trainings": trainings,
        "webinars": webinars,
        "products": products,
        # Additional context
        "featured_resources": featured_resources,
        "all_tags": all_tags,
        "current_tag": tag_filter,
        "search_query": search_query,
        # Resource counts for the template
        "events_count": events.count(),
        "info_systems_count": info_systems.count(),
        "maps_count": maps.count(),
        "media_count": media.count(),
        "news_count": news_items.count(),
        "policies_count": policies.count(),
        "projects_count": projects.count(),
        "publications_count": publications.count(),
        "technologies_count": technologies.count(),
        "trainings_count": trainings.count(),
        "webinars_count": webinars.count(),
        "products_count": products.count(),
    }

    return render(request, "pages/cmi-knowledge-resources.html", context)

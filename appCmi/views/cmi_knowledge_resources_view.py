from utils.get_models import get_active_models
from appAdmin.models import ResourceMetadata, Tag
from appCmi.models import ResourceBookmark, ResourceView
from appCmi.templatetags import get_knowledge_title
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
import logging
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
import datetime
from django.db import models
from appCmi.templatetags.custom_filters import get_knowledge_title
from utils.user_control import user_access_required
from appAdmin.models import About

logger = logging.getLogger(__name__)


@user_access_required(["admin", "cmi"], error_type=404)
def cmi_knowledge_resources(request):
    """View function for the knowledge resources page."""

    # Fetch active models
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    about_list = About.objects.all() 
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

    # Get user's bookmarked resources if user is authenticated
    user_bookmarked_resources = set()
    if request.user.is_authenticated:
        # Get the IDs of resources bookmarked by the current user
        user_bookmarked_resources = set(
            ResourceBookmark.objects.filter(user=request.user).values_list(
                "resource_id", flat=True
            )
        )

    # Check for bookmarks and add a bookmarked flag to each resource
    # For all_resources
    for resource in all_resources:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    # For featured resources
    for resource in featured_resources:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    # For each resource type
    for resource in events:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in info_systems:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in maps:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in media:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in news_items:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in policies:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in projects:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in publications:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in technologies:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in trainings:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in webinars:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

    for resource in products:
        resource.is_bookmarked = resource.id in user_bookmarked_resources

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
        # Add user bookmarks info
        "has_bookmarks": bool(user_bookmarked_resources),
        "about_list": about_list,
    }

    return render(request, "pages/cmi-knowledge-resources.html", context)


@user_access_required(["admin", "cmi"], error_type=404)
def record_resource_view(request, slug):
    """
    Records a view for a resource and returns JSON data for the modal.
    Simply records every view without duplicate checking.
    """
    resource = get_object_or_404(ResourceMetadata, slug=slug)

    # Get the IP address for anonymous users
    ip_address = request.META.get("REMOTE_ADDR")

    # Create a view record for every view
    view = ResourceView(resource=resource, ip_address=ip_address)

    if request.user.is_authenticated:
        view.user = request.user

    view.save()

    # Get the total view count
    view_count = ResourceView.objects.filter(resource=resource).count()

    # Check if the user has bookmarked this resource
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = ResourceBookmark.objects.filter(
            resource=resource, user=request.user
        ).exists()

    # Get specific resource data based on resource type
    resource_type = resource.resource_type
    specific_data = {}

    # Try to get the related specific resource object
    specific_model_name = resource_type.replace("-", "_")
    if hasattr(resource, specific_model_name):
        specific_resource = getattr(resource, specific_model_name)

        # Dynamically get fields from the specific resource model
        for field in specific_resource._meta.fields:
            if field.name not in ("id", "metadata", "slug"):
                field_value = getattr(specific_resource, field.name)

                # Handle various field types
                if isinstance(field_value, datetime.date) or isinstance(
                    field_value, datetime.datetime
                ):
                    field_value = field_value.isoformat()
                elif isinstance(field_value, models.Model):
                    field_value = str(field_value)

                specific_data[field.name] = field_value

    # Return JSON data for the modal
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Return JSON response for AJAX requests
        response_data = {
            "resource": {
                "id": resource.id,
                "title": resource.title,
                "description": resource.description,
                "resource_type": get_knowledge_title(resource.resource_type),
                "created_at": resource.created_at.isoformat(),
                "slug": resource.slug,
                "view_count": view_count,
                "is_bookmarked": is_bookmarked,
                "tags": [
                    {"id": tag.id, "name": tag.name} for tag in resource.tags.all()
                ],
                # Add other fields as needed
            },
            "specific_data": specific_data,
        }
        return JsonResponse(response_data)
    else:
        # For non-AJAX requests, redirect to a fallback page
        resource_type_url_mapping = {
            "event": "appCmi:event-detail",
            "info_system": "appCmi:info-system-detail",
            "map": "appCmi:map-detail",
            "media": "appCmi:media-detail",
            "news": "appCmi:news-detail",
            "policy": "appCmi:policy-detail",
            "project": "appCmi:project-detail",
            "publication": "appCmi:publication-detail",
            "technology": "appCmi:technology-detail",
            "training": "appCmi:training-detail",
            "webinar": "appCmi:webinar-detail",
            "product": "appCmi:product-detail",
        }

        url_name = resource_type_url_mapping.get(
            resource.resource_type, "appCmi:all-knowledge-resources"
        )

        try:
            return HttpResponseRedirect(reverse(url_name, kwargs={"slug": slug}))
        except:
            return HttpResponseRedirect(
                reverse("appCmi:all-knowledge-resources", kwargs={"slug": slug})
            )


@user_access_required(["admin", "cmi"], error_type=404)
def toggle_bookmark(request):
    """
    AJAX endpoint to toggle a resource bookmark.
    Expects a POST request with resource_slug.
    """

    # At the top of your view function
    print("Request method:", request.method)
    print("Headers:", request.headers)
    print("Content type:", request.headers.get("Content-Type"))
    print("POST data:", request.POST)
    print("Body:", request.body.decode("utf-8") if request.body else "Empty")

    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):

        resource_slug = request.POST.get("resource_slug")

        if not resource_slug:
            return JsonResponse(
                {"status": "error", "message": "Resource slug is required"}, status=400
            )

        try:
            resource = ResourceMetadata.objects.get(slug=resource_slug)

            # Check if bookmark already exists
            bookmark = ResourceBookmark.objects.filter(
                resource=resource, user=request.user
            ).first()

            if bookmark:
                # Remove bookmark
                bookmark.delete()
                return JsonResponse(
                    {
                        "status": "success",
                        "action": "removed",
                        "message": f"'{resource.title}' removed from bookmarks",
                    }
                )
            else:
                # Add bookmark
                ResourceBookmark.objects.create(resource=resource, user=request.user)
                return JsonResponse(
                    {
                        "status": "success",
                        "action": "added",
                        "message": f"'{resource.title}' added to bookmarks",
                    }
                )

        except ResourceMetadata.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Resource not found"}, status=404
            )

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

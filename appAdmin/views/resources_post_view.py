from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
import uuid
from utils.get_models import get_active_models
import json

from appAdmin.models import (
    ResourceMetadata,
    Event,
    InformationSystem,
    Map,
    Media,
    News,
    Policy,
    Project,
    Publication,
    Technology,
    TrainingSeminar,
    Webinar,
    Product,
    Tag,
    Commodity,
)
from appAdmin.forms import (
    ResourceMetadataForm,
    EventForm,
    InformationSystemForm,
    MapForm,
    MediaForm,
    NewsForm,
    PolicyForm,
    ProjectForm,
    PublicationForm,
    TechnologyForm,
    TrainingSeminarForm,
    WebinarForm,
    ProductForm,
    CommoditySelectForm,
    TagForm,
)
from utils.user_control import user_access_required


@user_access_required("admin")
def admin_resources_post(request):
    """
    View function to display all resource posts with filtering options.
    """

    models = get_active_models()  # Fetch active models
    commodities = models.get("commodities", [])  # List of active commodities
    knowledge_resources = models.get("knowledge_resources", [])

    # Get query parameters for filtering
    resource_type = request.GET.get("resource_type", "")
    commodity_id = request.GET.get("commodity", "")
    tag_id = request.GET.get("tag", "")
    search_query = request.GET.get("search", "")
    approval_status = request.GET.get("approval_status", "")

    total_resources = ResourceMetadata.objects.all().count()
    total_approved_resources = ResourceMetadata.objects.filter(is_approved=True).count()
    total_pending_resources = ResourceMetadata.objects.filter(is_approved=False).count()
    total_featured_resources = ResourceMetadata.objects.filter(is_featured=True).count()

    # Start with all resources
    resources = ResourceMetadata.objects.all().order_by("-created_at")

    # Apply filters
    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    if commodity_id:
        resources = resources.filter(commodities__id=commodity_id)

    if tag_id:
        resources = resources.filter(tags__id=tag_id)

    if search_query:
        resources = resources.filter(title__icontains=search_query) | resources.filter(
            description__icontains=search_query
        )

    if approval_status:
        if approval_status == "approved":
            resources = resources.filter(is_approved=True)
        elif approval_status == "pending":
            resources = resources.filter(is_approved=False)
        elif approval_status == "featured":
            resources = resources.filter(is_featured=True)

    # Pagination
    paginator = Paginator(resources, 10)  # Show 10 resources per page
    page = request.GET.get("page")

    try:
        resources_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        resources_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        resources_page = paginator.page(paginator.num_pages)

    # Get all resource types, commodities, and tags for filters
    resource_types = ResourceMetadata.RESOURCE_TYPES
    commodities = Commodity.objects.all()
    tags = Tag.objects.all()

    # Initialize forms for the modal
    metadata_form = ResourceMetadataForm()
    event_form = EventForm()
    information_system_form = InformationSystemForm()
    map_form = MapForm()
    media_form = MediaForm()
    news_form = NewsForm()
    policy_form = PolicyForm()
    project_form = ProjectForm()
    publication_form = PublicationForm()
    technology_form = TechnologyForm()
    training_seminar_form = TrainingSeminarForm()
    webinar_form = WebinarForm()
    product_form = ProductForm()

    context = {
        "knowledge_resources": knowledge_resources,
        "resources": resources_page,
        "resources_data": resources,
        "resource_types": resource_types,
        "commodities": commodities,
        "tags": tags,
        "metadata_form": metadata_form,
        "event_form": event_form,
        "information_system_form": information_system_form,
        "map_form": map_form,
        "media_form": media_form,
        "news_form": news_form,
        "policy_form": policy_form,
        "project_form": project_form,
        "publication_form": publication_form,
        "technology_form": technology_form,
        "training_seminar_form": training_seminar_form,
        "webinar_form": webinar_form,
        "product_form": product_form,
        "current_filters": {
            "resource_type": resource_type,
            "commodity": commodity_id,
            "tag": tag_id,
            "search": search_query,
            "approval_status": approval_status,
        },
        "total_resources": total_resources,
        "total_approved_resources": total_approved_resources,
        "total_pending_resources": total_pending_resources,
        "total_featured_resources": total_featured_resources,
    }

    return render(request, "pages/resources-post.html", context)


@user_access_required("admin")
@transaction.atomic
def admin_add_resources_post(request):
    """
    View for handling resource creation from the admin panel.
    """
    # Use the get_active_models utility to fetch required data
    models = get_active_models()
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    # For GET requests, just render the form
    if request.method == "GET":
        context = {
            "commodities": commodities,
            "knowledge_resources": knowledge_resources,
        }
        return render(request, "pages/resources-post.html", context)

    # For POST requests, process the form data
    elif request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        is_draft = request.POST.get("isDraft") == "true"

        try:
            # Get common metadata from the form
            resource_type_slug = request.POST.get("resourceType")
            resource_title = request.POST.get("resourceTitle")
            resource_description = request.POST.get("resourceDescription")
            is_approved = "is_approved" in request.POST
            is_featured = "is_featured" in request.POST

            # Find the actual resource type using the slug
            resource_type = None
            resource_machine_name = None
            for kr in knowledge_resources:
                if kr.slug == resource_type_slug:
                    resource_type = kr
                    # Extract the machine name from the data-fields-id attribute
                    # This should match with one of the resource type handlers
                    resource_machine_name = kr.machine_name
                    break

            if not resource_type:
                raise ValueError(
                    f"Resource type with slug '{resource_type_slug}' not found"
                )

            # Create resource metadata
            metadata = ResourceMetadata.objects.create(
                title=resource_title,
                description=resource_description,
                resource_type=resource_type,
                is_approved=is_approved,
                is_featured=is_featured,
                created_by=request.user,
            )

            # Process tags
            tags_string = request.POST.get("tags", "")
            if tags_string:
                tag_names = [tag.strip() for tag in tags_string.split(",")]
                for tag_name in tag_names:
                    if tag_name:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        metadata.tags.add(tag)

            # Process commodities
            commodity_ids = request.POST.get("commodity_ids", "")
            if commodity_ids:
                commodity_slugs = commodity_ids.split(",")
                for slug in commodity_slugs:
                    try:
                        commodity = Commodity.objects.get(slug=slug)
                        metadata.commodities.add(commodity)
                    except Commodity.DoesNotExist:
                        pass

            # Handle specific resource type fields
            if resource_machine_name:
                create_resource_specific_data(request, resource_machine_name, metadata)

            # Successful response
            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Resource created successfully!",
                        "redirect": f"appAdmin:display-resources-post",
                    }
                )
            else:
                messages.success(request, "Resource created successfully!")
                return redirect("appAdmin:display-resources-post")

        except Exception as e:
            # Handle errors
            if is_ajax:
                return JsonResponse(
                    {"success": False, "message": f"Error creating resource: {str(e)}"}
                )
            else:
                messages.error(request, f"Error creating resource: {str(e)}")
                context = {
                    "commodities": commodities,
                    "knowledge_resources": knowledge_resources,
                    "form_data": request.POST,
                    "error": str(e),  # Send the error to the template for debugging
                }
                return render(request, "pages/resources-post.html", context)

    # For other request methods
    return JsonResponse(
        {"success": False, "message": "Invalid request method"}, status=405
    )


@user_access_required("admin")
def create_resource_specific_data(request, resource_machine_name, metadata):
    """
    Helper function to create specific resource data based on machine name.
    """
    # Maps machine names to model handlers
    resource_handlers = {
        "events": create_event,
        "information_systemswebsites": create_information_system,
        "maps": create_map,
        "media": create_media,
        "news": create_news,
        "policies": create_policy,
        "projects": create_project,
        "publications": create_publication,
        "technologies": create_technology,
        "trainingseminars": create_training_seminar,
        "webinars": create_webinar,
        "products": create_product,
    }

    # Find and call the appropriate handler
    handler = resource_handlers.get(resource_machine_name)
    if handler:
        handler(request, metadata)
    else:
        raise ValueError(f"Unknown resource type: {resource_machine_name}")


# The following functions handle specific resource types


@user_access_required("admin")
def create_event(request, metadata):
    Event.objects.create(
        metadata=metadata,
        start_date=request.POST.get("eventStartDate"),
        end_date=request.POST.get("eventEndDate"),
        location=request.POST.get("eventLocation"),
        organizer=request.POST.get("eventOrganizer"),
        is_virtual="eventIsVirtual" in request.POST,
        event_file=request.FILES.get("eventFile"),
    )


@user_access_required("admin")
def create_information_system(request, metadata):
    InformationSystem.objects.create(
        metadata=metadata,
        website_url=request.POST.get("infoSystemUrl"),
        system_owner=request.POST.get("infoSystemOwner"),
        last_updated=request.POST.get("infoSystemLastUpdated") or None,
    )


@user_access_required("admin")
def create_map(request, metadata):
    Map.objects.create(
        metadata=metadata,
        map_url=request.POST.get("mapUrl"),
        map_file=request.FILES.get("mapFile"),
        latitude=request.POST.get("mapLatitude") or None,
        longitude=request.POST.get("mapLongitude") or None,
    )


@user_access_required("admin")
def create_media(request, metadata):
    Media.objects.create(
        metadata=metadata,
        media_type=request.POST.get("mediaType"),
        media_file=request.FILES.get("mediaFile"),
        media_url=request.POST.get("mediaUrl"),
        author=request.POST.get("mediaAuthor"),
    )


@user_access_required("admin")
def create_news(request, metadata):
    News.objects.create(
        metadata=metadata,
        publication_date=request.POST.get("newsPublishDate"),
        source=request.POST.get("newsSource"),
        external_url=request.POST.get("newsSourceUrl"),
        content=request.POST.get("newsContent"),
        featured_image=request.FILES.get("newsFeaturedImage"),
    )


@user_access_required("admin")
def create_policy(request, metadata):
    Policy.objects.create(
        metadata=metadata,
        policy_number=request.POST.get("policyNumber"),
        effective_date=request.POST.get("policyEffectiveDate"),
        issuing_body=request.POST.get("policyIssuingBody"),
        policy_file=request.FILES.get("policyFile"),
        policy_url=request.POST.get("policyUrl"),
        status=request.POST.get("policyStatus"),
    )


@user_access_required("admin")
def create_project(request, metadata):
    Project.objects.create(
        metadata=metadata,
        start_date=request.POST.get("projectStartDate"),
        end_date=request.POST.get("projectEndDate") or None,
        budget=request.POST.get("projectBudget") or None,
        funding_source=request.POST.get("projectFundingSource"),
        project_lead=request.POST.get("projectLead"),
        contact_email=request.POST.get("projectContactEmail"),
        status=request.POST.get("projectStatus"),
    )


@user_access_required("admin")
def create_publication(request, metadata):
    Publication.objects.create(
        metadata=metadata,
        authors=request.POST.get("publicationAuthors"),
        publication_date=request.POST.get("publicationDate"),
        publisher=request.POST.get("publicationPublisher"),
        doi=request.POST.get("publicationDOI"),
        isbn=request.POST.get("publicationISBN"),
        publication_type=request.POST.get("publicationType"),
        publication_file=request.FILES.get("publicationFile"),
    )


@user_access_required("admin")
def create_technology(request, metadata):
    Technology.objects.create(
        metadata=metadata,
        developer=request.POST.get("technologyDeveloper"),
        release_date=request.POST.get("technologyReleaseDate") or None,
        patent_number=request.POST.get("technologyPatentNumber"),
        license_type=request.POST.get("technologyLicenseType"),
    )


@user_access_required("admin")
def create_training_seminar(request, metadata):
    TrainingSeminar.objects.create(
        metadata=metadata,
        start_date=request.POST.get("trainingStartDate"),
        end_date=request.POST.get("trainingEndDate"),
        location=request.POST.get("trainingLocation"),
        trainers=request.POST.get("trainers"),
        target_audience=request.POST.get("trainingTargetAudience"),
    )


@user_access_required("admin")
def create_webinar(request, metadata):
    Webinar.objects.create(
        metadata=metadata,
        webinar_date=request.POST.get("webinarDate"),
        duration_minutes=request.POST.get("webinarDuration"),
        platform=request.POST.get("webinarPlatform"),
        presenters=request.POST.get("webinarPresenters"),
    )


@user_access_required("admin")
def create_product(request, metadata):
    Product.objects.create(
        metadata=metadata,
        manufacturer=request.POST.get("productManufacturer"),
        features=request.POST.get("productFeatures"),
        technical_specifications=request.POST.get("productTechSpecs"),
        price=request.POST.get("productPrice") or None,
    )


@user_access_required("admin")
def admin_edit_resources_post(request, slug):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_status = data.get("status")

            resource = ResourceMetadata.objects.get(slug=slug)
            resource.is_approved = new_status == "approved"
            resource.save()

            return JsonResponse({"success": True})
        except ResourceMetadata.DoesNotExist:
            return JsonResponse({"success": False, "error": "Resource not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})


@user_access_required("admin")
def admin_delete_resources_post(request, slug):
    resource_metadata_instance = ResourceMetadata.objects.get(slug=slug)
    resource_metadata_instance.delete()
    success_message = "Deleted successfully!"
    messages.success(request, success_message)
    return redirect("appAdmin:display-resources-post")

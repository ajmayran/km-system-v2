import json
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum
from appAdmin.models import (
    Commodity,
)
from appCmi.models import (
    Forum,
    FilteredCommodityFrequency,
)
from appAdmin.forms import CommodityForm
from django.contrib import messages
import logging
from django.urls import reverse
from utils.user_control import user_access_required

logger = logging.getLogger(__name__)  # Set up logging


@user_access_required("admin")
def admin_commodities(request):
    # Fetch all commodities with status categorization
    commodities = Commodity.objects.all()
    approvedcommodities = commodities.filter(status="active")
    pendingcommodities = commodities.filter(status="Pending")

    # Total commodity counts
    total_commodities = commodities.count()
    total_approved_commodities = approvedcommodities.count()
    total_pending_commodities = pendingcommodities.count()

    # Fetch the latest added commodity
    latest_commodity = Commodity.objects.order_by("-commodity_id").first()

    # Get frequency sum per commodity in bulk
    frequency_data = {
        item["commodity_id"]: item["total_frequency"]
        for item in FilteredCommodityFrequency.objects.values("commodity_id").annotate(
            total_frequency=Sum("frequency")
        )
    }

    # Get tagged counts per commodity in bulk
    tagged_data = {
        item["commodity_id"]: item["total_tags"]
        for item in Forum.objects.values("commodity_id").annotate(
            total_tags=Count("commodity_id")
        )
    }

    # Generate commodity data in a single iteration
    commodity_data = [
        {
            "commodity_name": commodity.commodity_name,
            "total_filter": frequency_data.get(commodity.commodity_id, 0),
            "total_tagged": tagged_data.get(commodity.commodity_id, 0),
        }
        for commodity in approvedcommodities
    ]

    commodity_data_json = json.dumps(commodity_data)

    # Render the template with all required data
    return render(
        request,
        "pages/commodities.html",
        {
            "total_commodities": total_commodities,
            "total_approved_commodities": total_approved_commodities,
            "total_pending_commodities": total_pending_commodities,
            "latest_commodity": latest_commodity,
            "frequency_sum": frequency_data,
            "tagged_counts": tagged_data,
            "approvedcommodities": approvedcommodities,
            "pendingcommodities": pendingcommodities,
            "commodity_data_json": commodity_data_json,
        },
    )


@user_access_required("admin")
def admin_add_commodity(request):  # Add commodity
    form = CommodityForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Commodity added successfully!")
            return redirect("appAdmin:display-commodities")
        else:
            logger.error(
                f"Form errors: {form.errors}"
            )  # Log errors instead of printing

    return render(request, "pages/commodities.html", {"form": form})


@user_access_required("admin")
def admin_edit_commodity(request, slug):
    commodity = get_object_or_404(Commodity, slug=slug)  # Fetch commodity using slug
    if request.method == "POST":
        form = CommodityForm(request.POST, request.FILES, instance=commodity)
        if form.is_valid():
            form.save()
            messages.success(request, "Commodity edited successfully!")
            return redirect("appAdmin:display-commodities")
    else:
        form = CommodityForm(instance=commodity)

    return render(request, "pages/commodities.html", {"form": form})


@user_access_required("admin")
def admin_delete_commodity(request, slug):
    commodity = get_object_or_404(
        Commodity, slug=slug
    )  # Fetch object by slug instead of ID
    commodity.delete()

    messages.success(request, "Deleted successfully!")
    return redirect(reverse("appAdmin:display-commodity"))

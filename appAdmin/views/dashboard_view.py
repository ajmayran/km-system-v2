from django.shortcuts import render, redirect
from utils.get_models import get_active_models
from utils.get_commodity_top_10 import get_top_10_tagged_commodities
from utils.forum_post_monthly_count import get_forum_posts_by_month_current_year
from appAdmin.models import ResourceMetadata
from django.utils import timezone
from utils.user_control import user_access_required


@user_access_required("admin")
def dashboard(request):
    models = get_active_models()  # Fetch active models
    top_10_commodities = get_top_10_tagged_commodities()

    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    cmis = models.get("cmis", [])
    accounts = models.get("accounts", [])
    notifications = models.get("notifications", [])

    messages_to_admin = notifications.order_by("-created_at")
    unread_count = notifications.count()

    total_commodities = commodities.count()
    total_cmis = cmis.count()
    total_accounts = accounts.count()
    total_resources = ResourceMetadata.objects.count()  # total resources

    # Get the current year
    current_year = timezone.now().year

    # Get posts by month data
    stats = get_forum_posts_by_month_current_year()

    context = {
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "cmis": cmis,
        "accounts": accounts,
        "total_commodities": total_commodities,
        "total_accounts": total_accounts,
        "total_cmis": total_cmis,
        "messages_to_admin": messages_to_admin,
        "unread_count": unread_count,
        "total_resources": total_resources,
        "top_10_commodities": top_10_commodities,
        "stats": stats,
        "current_year": current_year,
    }

    return render(request, "pages/dashboard.html", context)

from django.shortcuts import render, redirect
from utils.get_models import get_active_models


def dashboard(request):
    models = get_active_models()  # Fetch active models

    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    cmis = models.get("cmis", [])
    accounts = models.get("accounts", [])
    notifications = models.get("notifications", [])

    messages_to_admin = notifications.order_by("-created_at")
    unread_count = notifications.count()

    total_commodities = commodities.count()
    total_knowledge_resources = knowledge_resources.count()
    total_cmis = cmis.count()
    total_accounts = accounts.count()

    context = {
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "cmis": cmis,
        "accounts": accounts,
        "total_commodities": total_commodities,
        "total_accounts": total_accounts,
        "total_cmis": total_cmis,
        "total_knowledge_resources": total_knowledge_resources,
        "messages_to_admin": messages_to_admin,
        "unread_count": unread_count,
    }

    return render(request, "pages/dashboard.html", context)


# def dashboard(request):
#     return render(request, "base/admin-index.html")

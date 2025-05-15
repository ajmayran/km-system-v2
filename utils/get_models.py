def get_active_models():
    from appAdmin.models import Commodity, KnowledgeResources, UsefulLinks, CMI
    from appCmi.models import MessageToAdmin
    from appAccounts.models import CustomUser

    """
    Fetch all active records from Commodity, KnowledgeResources, and  Useful links models.
    Returns a dictionary containing the results.
    """
    return {
        "commodities": Commodity.objects.filter(status="active"),
        "knowledge_resources": KnowledgeResources.objects.filter(status="active"),
        "useful_links": UsefulLinks.objects.filter(status="active"),
        "cmis": CMI.objects.filter(status="active"),
        "accounts": CustomUser.objects.filter(user_type="cmi"),
        "notifications": MessageToAdmin.objects.filter(status="pending"),
    }

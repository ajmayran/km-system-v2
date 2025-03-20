from appAdmin.models import Commodity, KnowledgeResources, UsefulLinks


def get_active_models():
    """
    Fetch all active records from Commodity, KnowledgeResources, and  Useful links models.
    Returns a dictionary containing the results.
    """
    return {
        "commodities": Commodity.objects.filter(status="active"),
        "knowledge_resources": KnowledgeResources.objects.filter(status="active"),
        "useful_links": UsefulLinks.objects.filter(status="active"),
    }

from django import template
from appAdmin.models import KnowledgeResources
from django.contrib.auth.models import AnonymousUser

register = template.Library()


@register.filter
def get_knowledge_title(value):
    try:
        if "(" in str(value) and ")" in str(value):
            obj_id = int(str(value).split("(")[1].split(")")[0])
            knowledge_resource = KnowledgeResources.objects.get(knowledge_id=obj_id)
            return knowledge_resource.knowledge_title
        else:
            return str(value)  
    except (AttributeError, ValueError, KnowledgeResources.DoesNotExist):
        return str(value)  


@register.filter
def get_machine_name(value):
    """
    Extracts the machine name from a knowledge resource object or ID.
    Usage: {{ resource.resource_type|get_machine_name }}
    """
    try:
        # If the value is a string like "KnowledgeResources(123)",
        # extract the ID and look up the object
        if isinstance(value, str) and "(" in value and ")" in value:
            obj_id = int(str(value).split("(")[1].split(")")[0])
            knowledge_resource = KnowledgeResources.objects.get(knowledge_id=obj_id)
            return knowledge_resource.machine_name
        # If the value is a direct integer ID
        elif isinstance(value, int):
            knowledge_resource = KnowledgeResources.objects.get(knowledge_id=value)
            return knowledge_resource.machine_name
        # If the value is already a KnowledgeResources object
        elif hasattr(value, "machine_name"):
            return value.machine_name
        else:
            return str(value).lower().replace(" ", "_")
    except (AttributeError, ValueError, KnowledgeResources.DoesNotExist):
        # If we can't extract a machine name, convert the string to a
        # valid machine-readable format (lowercase with underscores)
        return str(value).lower().replace(" ", "_")

@register.filter
def is_reacted_by_user(faq, user):
    """Check if user has reacted to this FAQ"""
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    return faq.is_reacted_by(user)
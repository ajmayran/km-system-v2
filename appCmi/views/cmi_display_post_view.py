from django.shortcuts import render
from appAdmin.models import ResourceMetadata, Event, InformationSystem, Map
from utils.user_control import user_access_required

@user_access_required(["admin", "cmi"], error_type=404)
def cmi_display_post(request, slug):
    post = ResourceMetadata.objects.get(slug=slug)
    post_type = post.resource_type

    context = {"post": post}

    if post_type == "event":
        event = Event.objects.get(metadata=post)
        context["event"] = event
    elif post_type == "information_system":
        information_system = InformationSystem.objects.get(metadata=post)
        context["information_system"] = information_system
    elif post_type == "map":
        map = Map.objects.get(metadata=post)
        context["map"] = map

    return render(request, "pages/cmi-display-post.html", context)

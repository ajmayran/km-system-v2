from django.shortcuts import render
from appAdmin.models import About, UploadVideo, CMI
from utils.get_models import get_active_models
from utils.user_control import user_access_required


def about(request):
    contents = About.objects.all()
    videos = UploadVideo.objects.last()
    cmis = CMI.objects.filter(status="active")
    models = get_active_models()  # Fetch active models
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    context = {
        "contents": contents,
        "videos": videos,
        "cmis": cmis,
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
    }
    return render(request, "pages/cmi-about.html", context)

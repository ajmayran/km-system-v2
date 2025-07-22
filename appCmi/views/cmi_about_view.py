from django.shortcuts import render, get_object_or_404
from appAdmin.models import About, UploadVideo, CMI
from utils.get_models import get_active_models
from utils.user_control import user_access_required
from appAdmin.models import (
    About, AboutRationale, AboutObjective, AboutObjectiveDetail,
    AboutTeamMember, AboutSubProject, AboutTimeline, AboutTimelineBullet,
    AboutTimelineImage, AboutSubProjectObjective, AboutSubProjectRationale,
    AboutSubProjectTeamMember, AboutSubProjectTimeline, MainProgram, MainProgramImage, MainProgramObjective
    )

def cmi_about(request):
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])
    about_list = About.objects.all()
    about = About.objects.all()
    main = MainProgram.objects.first()
    images = MainProgramImage.objects.all() 
    objectives = MainProgramObjective.objects.prefetch_related(
        'title_bullets', 'target_bullets'
    )

    context = {
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "about_list": about_list,
        "images": images,
        "main": main,
        "about": about,
        "objectives": objectives
    }
    return render(request, "pages/cmi-about.html", context)


def cmi_project_detail(request, about_id):
    project = get_object_or_404(About, about_id=about_id)
    return render(request, "pages/cmi-project-detail.html", {"project": project})
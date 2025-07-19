from django.shortcuts import render, get_object_or_404
from appAdmin.models import About,AboutSubProject, UploadVideo, CMI, AboutRationale, AboutObjective, AboutObjectiveDetail, AboutActivity , AboutTimeline, AboutTeamMember, AboutTeamSocial
from utils.get_models import get_active_models
from utils.user_control import user_access_required
from appAdmin.models import (
    About, AboutRationale, AboutObjective, AboutObjectiveDetail,
    AboutTeamMember, AboutSubProject, AboutTimeline, AboutTimelineBullet,
    AboutTimelineImage, AboutSubProjectObjective, AboutSubProjectRationale,
    AboutSubProjectTeamMember, AboutSubProjectTimeline, MainProgram, MainProgramImage, MainProgramObjective
    )

@user_access_required(["admin", "cmi"], error_type=404)
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

# @user_access_required(["admin", "cmi"], error_type=404)
# def project_view(request, about_id):
#     project = get_object_or_404(About, pk=about_id)

#     context = {
#         'featured_about': project,
#         'project': project,
#         'rationales': AboutRationale.objects.filter(about=project),
#         'objectives': AboutObjective.objects.filter(about=project).prefetch_related('details'),
#         'team_members': AboutTeamMember.objects.filter(about=project).prefetch_related('socials'),
#         'subprojects': AboutSubProject.objects.filter(about=project),
#         'timeline_items': AboutTimeline.objects.filter(about=project).prefetch_related('bullets', 'images'),
#     }

#     return render(request, 'pages/project.html', context)
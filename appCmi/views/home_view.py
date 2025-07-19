from django.shortcuts import render, get_object_or_404
from appAdmin.models import About, MainProgram, MainProgramImage, MainProgramObjective,AboutRationale,AboutObjective,AboutTeamMember,AboutSubProject,AboutTimeline
from appAdmin.models import (
    About, AboutRationale, AboutObjective, AboutObjectiveDetail,
    AboutTeamMember, AboutSubProject, AboutTimeline, AboutTimelineBullet,
    AboutTimelineImage, AboutSubProjectObjective, AboutSubProjectRationale,
    AboutSubProjectTeamMember, AboutSubProjectTimeline
    )
from utils.get_models import get_active_models
from utils.user_control import user_access_required
from utils.search_function import find_similar_resources

@user_access_required(["admin", "cmi"], error_type=404)
def home(request):
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
    return render(request, "pages/home.html", context)

def get_input_from_search(request):
    query = request.GET.get("q", "").strip()
    
    if query:
        similar_resources = find_similar_resources(query)
    else:
        similar_resources = []
    
    context = {"query": query, "results": similar_resources}
    return render(request, "pages/cmi-search-result.html", context)

@user_access_required(["admin", "cmi"], error_type=404)
def project_view(request, about_id):
    project = get_object_or_404(About, pk=about_id)
    about = About.objects.all() 
    about_list = About.objects.all()
    context = {
        'featured_about': project,
        'project': project,
        'about': about,
        'about_list': about_list,
        'rationales': AboutRationale.objects.filter(about=project),
        'objectives': AboutObjective.objects.filter(about=project).prefetch_related('details'),
        'team_members': AboutTeamMember.objects.filter(about=project).prefetch_related('socials'),
        'subprojects': AboutSubProject.objects.filter(about=project),
        'timeline_items': AboutTimeline.objects.filter(about=project).prefetch_related('bullets', 'images'),
    }

    return render(request, 'pages/project.html', context)

@user_access_required(["admin", "cmi"], error_type=404)
def project_sub_view(request, sub_id):
    subproject = get_object_or_404(AboutSubProject, pk=sub_id)
    about = About.objects.all() 
    about_list = About.objects.all()
    context = {
        'featured_about': subproject,
        'project': subproject,
        'about': about,
        'about_list': about_list,
        'rationales': AboutSubProjectRationale.objects.filter(about=subproject),
        'objectives': AboutSubProjectObjective.objects.filter(about=subproject).prefetch_related('details'),
        'team_members': AboutSubProjectTeamMember.objects.filter(about=subproject).prefetch_related('socials'),
        'timeline_items': AboutSubProjectTimeline.objects.filter(about=subproject).prefetch_related('bullets', 'images'),
    }

    return render(request, 'pages/project-sub.html', context)


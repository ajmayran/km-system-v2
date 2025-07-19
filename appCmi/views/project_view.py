# appCmi/views/project_view.py
from django.shortcuts import render, get_object_or_404
from appAdmin.models import (
    About, AboutRationale, AboutObjective, AboutObjectiveDetail,
    AboutTeamMember, AboutSubProject, AboutTimeline, AboutTimelineBullet,
    AboutTimelineImage, AboutSubProjectObjective, AboutSubProjectRationale,
    AboutSubProjectTeamMember, AboutSubProjectTimeline
)
from utils.get_models import get_active_models
from utils.user_control import user_access_required

@user_access_required(["admin", "cmi"], error_type=404)
def project_detail(request, about_id):
    models = get_active_models()
    about = About.objects.all()
    # Get the main project
    featured_about = get_object_or_404(About, pk=about_id)
    
    rationales = AboutRationale.objects.filter(about=featured_about).order_by('rationale_id')
    
    objectives = AboutObjective.objects.filter(about=featured_about).prefetch_related('details').order_by('objective_id')
    
    team_members = AboutTeamMember.objects.filter(about=featured_about).prefetch_related('socials').order_by('member_id')
    
    try:
        subprojects = AboutSubProject.objects.filter(about=featured_about).order_by('sub_id')
    except:
        subprojects = []  # In case the model doesn't exist yet
    
    # Fetch timeline data with related bullets and images
    timeline_items = AboutTimeline.objects.filter(about=featured_about).prefetch_related('bullets', 'images').order_by('timeline_id')
    
    return render(request, 'pages/project.html', {
        'featured_about': featured_about,
        'rationales': rationales,
        'objectives': objectives,
        'team_members': team_members,
        'subprojects': subprojects,
        "about": about,
        'timeline_items': timeline_items,
    })

@user_access_required(["admin", "cmi"], error_type=404)
def project_sub_view(request, sub_id):
    """
    View for displaying subproject details
    """
    # Get the subproject
    subproject = get_object_or_404(AboutSubProject, pk=sub_id)
    
    # Get related data for the subproject
    rationales = AboutSubProjectRationale.objects.filter(about=subproject).order_by('rationale_id')
    
    objectives = AboutSubProjectObjective.objects.filter(about=subproject).prefetch_related('details').order_by('objective_id')
    
    team_members = AboutSubProjectTeamMember.objects.filter(about=subproject).prefetch_related('socials').order_by('member_id')
    
    # Fetch timeline data with related bullets and images
    timeline_items = AboutSubProjectTimeline.objects.filter(about=subproject).prefetch_related('bullets', 'images').order_by('timeline_id')
    
    context = {
        'featured_about': subproject,  # This will be used in the template
        'project': subproject,         # Additional reference
        'rationales': rationales,
        'objectives': objectives,
        'team_members': team_members,
        'timeline_items': timeline_items,
    }
    
    return render(request, 'pages/project-sub.html', context)

# @user_access_required(["admin", "cmi"], error_type=404)
# def project_sub_detail(request, sub_id):
#     models = get_active_models()
    
#     # Get the main project
#     featured_about = get_object_or_404(AboutSubProject, pk=sub_id)
    
#     rationales = AboutSubProjectRationale.objects.filter(about=featured_about).order_by('rationale_id')
    
#     objectives = AboutSubProjectObjective.objects.filter(about=featured_about).prefetch_related('details').order_by('objective_id')
    
#     team_members = AboutSubProjectTeamMember.objects.filter(about=featured_about).prefetch_related('socials').order_by('member_id')
  
#     # Fetch timeline data with related bullets and images
#     timeline_items = AboutSubProjectTimeline.objects.filter(about=featured_about).prefetch_related('bullets', 'images').order_by('timeline_id')
    
#     return render(request, 'pages/project-sub.html', {
#         'featured_about': featured_about,
#         'rationales': rationales,
#         'objectives': objectives,
#         'team_members': team_members,
#         'timeline_items': timeline_items,
#     })

@user_access_required(["admin", "cmi"], error_type=404)
def project_view(request, about_id):
    project = get_object_or_404(About, pk=about_id)

    context = {
        'featured_about': project,
        'project': project,
        'rationales': AboutRationale.objects.filter(about=project),
        'objectives': AboutObjective.objects.filter(about=project).prefetch_related('details'),
        'team_members': AboutTeamMember.objects.filter(about=project).prefetch_related('socials'),
        'subprojects': AboutSubProject.objects.filter(about=project),
        'timeline_items': AboutTimeline.objects.filter(about=project).prefetch_related('bullets', 'images'),
    }

    return render(request, 'pages/project.html', context)
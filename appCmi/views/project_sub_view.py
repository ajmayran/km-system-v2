from django.shortcuts import render, get_object_or_404
from appAdmin.models import (
    About, AboutRationale, AboutObjective, AboutObjectiveDetail,
    AboutTeamMember, AboutSubProject, AboutTimeline, AboutTimelineBullet,
    AboutTimelineImage,AboutSubProjectObjective,AboutSubProjectRationale,AboutSubProjectTeamMember,AboutSubProjectTimeline
)
from utils.get_models import get_active_models
from utils.user_control import user_access_required

@user_access_required(["admin", "cmi"], error_type=404)
def project_sub_detail(request, sub_id):
    models = get_active_models()
    
    # Get the main project
    subproject = get_object_or_404(AboutSubProject, pk=sub_id)
    
    rationales = AboutSubProjectRationale.objects.filter(about=subproject).order_by('rationale_id')
    
    objectives = AboutSubProjectObjective.objects.filter(about=subproject).prefetch_related('details').order_by('objective_id')
    
    team_members = AboutSubProjectTeamMember.objects.filter(about=subproject).prefetch_related('socials').order_by('member_id')
  
    # Fetch timeline data with related bullets and images
    timeline_items = AboutSubProjectTimeline.objects.filter(about=subproject).prefetch_related('bullets', 'images').order_by('timeline_id')
    
    return render(request, 'pages/project-sub.html', {
        'featured_about': subproject,  # This will be used in the template
        'project': subproject,         # Additional reference
        'rationales': rationales,
        'rationales': rationales,
        'objectives': objectives,
        'team_members': team_members,
        'timeline_items': timeline_items,
    })
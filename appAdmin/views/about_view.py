from django.shortcuts import render, redirect
from django.urls import reverse
from appAdmin.models import About,AboutRationale, AboutObjective, AboutObjectiveDetail, AboutActivity, AboutTimeline, AboutTeamMember,AboutTeamSocial, AboutFooter, UploadVideo
from appAdmin.forms import AboutForm, AboutRationaleForm, AboutObjectiveForm,  AboutActivityForm, AboutTimelineForm, AboutTeamMemberForm, AboutFooterForm, AboutTeamSocialForm, UploadForm
from appAdmin.models import MainProgram, MainTitleBullet, MainTargetBullet, MainProgramImage, MainProgramObjective,AboutTimelineImage,AboutTimelineBullet
from appAdmin.forms import MainProgramForm, MainTitleBulletForm, MainTargetBulletForm, MainProgramImageForm, MainProgramObjectiveForm
from django.contrib import messages
from django.shortcuts import get_object_or_404
from utils.user_control import user_access_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.conf import settings
import json
# from appAdmin.forms import AboutForm

@user_access_required("admin")
def admin_main_about_page(request):
    videos = UploadVideo.objects.last()
    footer_content = AboutFooter.objects.all()
    main_about_content = MainProgram.objects.all().order_by('-date_created')
    edit_forms = {item.id: MainProgramForm(instance=item) for item in main_about_content}
    form = MainProgramForm()
    context = {
             "main_about_content": MainProgram.objects.prefetch_related(
            'images',
            'objectives__title_bullets',
            'objectives__target_bullets'
        ).order_by('-date_created'),
            "footer_content": footer_content,
            "videos": videos,
            "form": form,
            'edit_forms': edit_forms,
        }

    return render(request, "pages/main-about.html", context)

@user_access_required("admin")
def admin_main_about_add(request):
    if request.method == "POST":
        form = MainProgramForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Main about project added successfully!")
            return redirect("appAdmin:main-about-page")
        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, "pages/main-about.html", {
                "form": form,
                "main_about_content": MainProgram.objects.all().order_by('-date_created'),
                "footer_content": AboutFooter.objects.all(),
                "videos": UploadVideo.objects.last(),
                "show_add_modal": True
            })
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
def admin_main_about_edit(request, about_id):
    main_about_instance = get_object_or_404(MainProgram, id=about_id)

    if request.method == "POST":
        form = MainProgramForm(request.POST, request.FILES, instance=main_about_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Main about project updated successfully!")
            return redirect("appAdmin:main-about-page")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MainProgramForm(instance=main_about_instance)

    context = {
        "form": form,
        "main_about_content": MainProgram.objects.all().order_by('-date_created'),
        "footer_content": AboutFooter.objects.all(),
        "videos": UploadVideo.objects.last(),
        "editing_item": main_about_instance,
        "show_edit_modal": True
    }

    return render(request, "pages/main-about.html", context)

@user_access_required("admin")
@require_POST
def admin_main_about_delete(request, about_id):
    try:
        main_about_instance = get_object_or_404(MainProgram, id=about_id)
        # project_name = about_instance.project_name
        main_about_instance.delete()
        messages.success(request, f"Main Project deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting project. Please try again.")
    
    return redirect("appAdmin:main-about-page")

# Add these views to your views.py file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse

# =============================================================================
# IMAGE CRUD VIEWS
# =============================================================================

@user_access_required("admin")
def admin_image_add(request, program_id):
    program = get_object_or_404(MainProgram, id=program_id)
    
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        
        if title and image:
            MainProgramImage.objects.create(
                main_program=program,  # not `program=program`
                title=title,
                description=description,
                image=image
            )
            messages.success(request, "Image added successfully!")
        else:
            messages.error(request, "Title and image are required.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
def admin_image_edit(request, image_id):
    image_obj = get_object_or_404(MainProgramImage, id=image_id)  # ✅ corrected model
    
    if request.method == "POST":
        image_obj.title = request.POST.get('title', image_obj.title)
        image_obj.description = request.POST.get('description', image_obj.description)
        
        if 'image' in request.FILES:
            image_obj.image = request.FILES['image']
        
        image_obj.save()
        messages.success(request, "Image updated successfully!")

    return redirect("appAdmin:main-about-page")


@user_access_required("admin")
@require_POST
def admin_image_delete(request, image_id):
    try:
        image_obj = get_object_or_404(MainProgramImage, id=image_id)  
        image_obj.delete()
        messages.success(request, "Image deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting image. Please try again.")

    return redirect("appAdmin:main-about-page")

# =============================================================================
# OBJECTIVE CRUD VIEWS
# =============================================================================

@user_access_required("admin")
def admin_main_objective_add(request, program_id):
    program = get_object_or_404(MainProgram, id=program_id)
    
    if request.method == "POST":
        title = request.POST.get('title')
        target = request.POST.get('target')
        title_bullets = request.POST.getlist('title_bullets[]')
        target_bullets = request.POST.getlist('target_bullets[]')

        if title:
            objective = MainProgramObjective.objects.create(
                main_program=program,
                title=title,
                target=target
            )

            # Save title bullets
            for tb in title_bullets:
                if tb.strip():
                    MainTitleBullet.objects.create(objective=objective, text=tb.strip())

            # Save target bullets
            for tb in target_bullets:
                if tb.strip():
                    MainTargetBullet.objects.create(objective=objective, text=tb.strip())

            messages.success(request, "Objective added successfully!")
        else:
            messages.error(request, "Title is required.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
def admin_main_objective_edit(request, objective_id):
    objective = get_object_or_404(MainProgramObjective, id=objective_id)
    
    if request.method == "POST":
        # Update basic fields
        title = request.POST.get('title')
        target = request.POST.get('target')
        
        if title:
            objective.title = title
            objective.target = target or ''
            objective.save()
            
            # Clear existing bullets and recreate them
            # This ensures we have a clean slate and handles all updates/deletions
            
            # Handle Title Bullets - Clear and recreate
            MainTitleBullet.objects.filter(objective=objective).delete()
            
            # Get all title bullet inputs (both existing and new)
            title_bullets = []
            
            # Collect existing title bullets that weren't deleted
            existing_title_bullets = request.POST.dict()
            for key, value in existing_title_bullets.items():
                if key.startswith('existing_title_bullets[') and value.strip():
                    title_bullets.append(value.strip())
            
            # Collect new title bullets
            new_title_bullets = request.POST.getlist('new_title_bullets[]')
            for bullet_text in new_title_bullets:
                if bullet_text.strip():
                    title_bullets.append(bullet_text.strip())
            
            # Create all title bullets
            for bullet_text in title_bullets:
                if bullet_text:
                    MainTitleBullet.objects.create(objective=objective, text=bullet_text)
            
            # Handle Target Bullets - Clear and recreate
            MainTargetBullet.objects.filter(objective=objective).delete()
            
            # Get all target bullet inputs (both existing and new)
            target_bullets = []
            
            # Collect existing target bullets that weren't deleted
            existing_target_bullets = request.POST.dict()
            for key, value in existing_target_bullets.items():
                if key.startswith('existing_target_bullets[') and value.strip():
                    target_bullets.append(value.strip())
            
            # Collect new target bullets
            new_target_bullets = request.POST.getlist('new_target_bullets[]')
            for bullet_text in new_target_bullets:
                if bullet_text.strip():
                    target_bullets.append(bullet_text.strip())
            
            # Create all target bullets
            for bullet_text in target_bullets:
                if bullet_text:
                    MainTargetBullet.objects.create(objective=objective, text=bullet_text)
            
            messages.success(request, "Objective updated successfully!")
        else:
            messages.error(request, "Title is required.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
@require_POST
def admin_main_objective_delete(request, objective_id):
    try:
        objective = get_object_or_404(MainProgramObjective, id=objective_id)
        objective.delete()
        messages.success(request, "Objective deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting objective. Please try again.")
    
    return redirect("appAdmin:main-about-page")

# =============================================================================
# BULLET CRUD VIEWS
# =============================================================================

@user_access_required("admin")
def admin_title_bullet_add(request, objective_id):
    objective = get_object_or_404(MainProgramObjective, id=objective_id)
    
    if request.method == "POST":
        text = request.POST.get('text')
        
        if text:
            MainTitleBullet.objects.create(
                objective=objective,
                text=text
            )
            messages.success(request, "Title bullet added successfully!")
        else:
            messages.error(request, "Text is required.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
@require_POST
def admin_title_bullet_delete(request, bullet_id):
    try:
        bullet = get_object_or_404(MainTitleBullet, id=bullet_id)
        bullet.delete()
        messages.success(request, "Title bullet deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting title bullet. Please try again.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
def admin_target_bullet_add(request, objective_id):
    objective = get_object_or_404(MainProgramObjective, id=objective_id)
    
    if request.method == "POST":
        text = request.POST.get('text')
        
        if text:
            MainTitleBullet.objects.create(
                objective=objective,
                text=text
            )
            messages.success(request, "Target bullet added successfully!")
        else:
            messages.error(request, "Text is required.")
    
    return redirect("appAdmin:main-about-page")

@user_access_required("admin")
@require_POST
def admin_target_bullet_delete(request, bullet_id):
    try:
        bullet = get_object_or_404(MainTitleBullet, id=bullet_id)
        bullet.delete()
        messages.success(request, "Target bullet deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting target bullet. Please try again.")
    
    return redirect("appAdmin:main-about-page")

# views.py

@user_access_required("admin")
def admin_about_page(request):
    about_content = About.objects.all().order_by('-date_created')
    
    # Create forms for adding and editing
    form = AboutForm()
    
    # Create edit forms for each item
    edit_forms = {}
    for item in about_content:
        edit_forms[item.about_id] = AboutForm(instance=item)
    
    context = {
        'about_content': about_content,
        'form': form,
        'edit_forms': edit_forms,
    }
    return render(request, 'admin/about_page.html', context)

@user_access_required("admin")
def admin_about_add(request):
    if request.method == "POST":
        form = AboutForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "About project added successfully!")
        else:
            messages.error(request, "Error adding project. Please check the form.")
            print(form.errors)
    return redirect("appAdmin:about-page")

@user_access_required("admin")
def admin_about_edit(request, about_id):
    about_instance = get_object_or_404(About, about_id=about_id)
    if request.method == "POST":
        form = AboutForm(request.POST, request.FILES, instance=about_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "About project updated successfully!")
        else:
            messages.error(request, "Error updating project.")
            print(form.errors)
    return redirect("appAdmin:about-page")


@user_access_required("admin")
def admin_about_page(request):
    """Main about page view"""
    # Create forms for all about items for the edit modals
    edit_forms = {}
    for item in About.objects.all():
        edit_forms[item.about_id] = AboutForm(instance=item)
    
    context = {
        "form": AboutForm(),  # For add modal
        "edit_forms": edit_forms,  # For edit modals
        "about_content": About.objects.all().order_by('-date_created'),
        "footer_content": AboutFooter.objects.all(),
        "videos": UploadVideo.objects.last(),
    }
    
    return render(request, "pages/about.html", context)

@user_access_required("admin")
def admin_about_add(request):
    """Add new about project"""
    if request.method == "POST":
        form = AboutForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "About project added successfully!")
                return redirect("appAdmin:about-page")
            except Exception as e:
                messages.error(request, f"Error saving: {str(e)}")
        else:
            # Debug form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect("appAdmin:about-page")

@user_access_required("admin")
def admin_about_footer(request):
    footer_content = AboutFooter.objects.all()
    existing_instance = AboutFooter.objects.first()

    form = AboutFooterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        print("FOOTER: ", form.cleaned_data)

        if existing_instance:
            return redirect("appAdmin:about-footer-edit")

        form.save()
        return redirect("appAdmin:about-page")

    if form.errors:
        print("FOOTER FORM ERRORS: ", form.errors)

    return render(
        request,
        "pages/about.html",
        {
            "form": form,
            "footer_content": footer_content,
            "form_action_footer": reverse(
                "appAdmin:about-footer-edit"
                if footer_content
                else "appAdmin:about-page"
            ),
        },
    )

@user_access_required("admin")
def admin_about_footer_edit(request):
    footer_instance = get_object_or_404(AboutFooter)
    form = AboutFooterForm(request.POST or None, instance=footer_instance)

    if request.method == "POST" and form.is_valid():
        print("EDIT FOOTER", form.cleaned_data)
        form.save()
        return redirect("appAdmin:about-page")

    if form.errors:
        print("FORM ERRORS:", form.errors)

    return render(request, "pages/about.html", {"form": form})

@user_access_required("admin")
def admin_upload_video(request):
    form = UploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Uploaded successfully!")
        return redirect("appAdmin:about-page")

    if form.errors:
        print("FORM ERRORS:", form.errors)

    return render(request, "pages/about.html", {"form": form})

# Edit About Project
@user_access_required("admin")
def admin_about_page_edit(request, about_id):
    about_instance = get_object_or_404(About, about_id=about_id)
    
    if request.method == "POST":
        form = AboutForm(request.POST, instance=about_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "About project updated successfully!")
            return redirect("appAdmin:about-page")
        else:
            messages.error(request, "Please correct the errors below.")

            # Repopulate necessary context for rendering about.html
            about_content = About.objects.all().order_by('-date_created')
            footer_content = AboutFooter.objects.all()
            videos = UploadVideo.objects.last()
            form = AboutForm(instance=about_instance)

            # ✅ Build edit_forms for all items
            edit_forms = {item.about_id: AboutForm(instance=item) for item in about_content}

            return render(request, "pages/about.html", {
                "form": AboutForm(),  # blank add form
                "about_content": about_content,
                "footer_content": footer_content,
                "videos": videos,
                "edit_forms": edit_forms,
                "show_edit_modal_id": about_id  # used to auto-open the modal
            })

    return redirect("appAdmin:about-page")

# Delete About Project
@user_access_required("admin")
@require_POST
def admin_about_delete(request, about_id):
    try:
        about_instance = get_object_or_404(About, about_id=about_id)
        project_name = about_instance.project_name
        about_instance.delete()
        messages.success(request, f"Project deleted successfully!")
    except Exception as e:
        messages.error(request, "Error deleting project. Please try again.")
    
    return redirect("appAdmin:about-page")

# Rationale View
@user_access_required("admin")
def about_rationale(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    rationale_items = AboutRationale.objects.filter(about_id=pk)

    form = AboutRationaleForm(initial={'about': about_instance})
    edit_forms = {item.rationale_id: AboutRationaleForm(instance=item) for item in rationale_items}

    context = {
        "about": about_instance,
        "rationale_items": rationale_items,
        "form": form,
        "edit_forms": edit_forms,
    }
    return render(request, "pages/about-rationale.html", context)


@user_access_required("admin")
def about_rationale_add(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)

    if request.method == "POST":
        form = AboutRationaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rationale added successfully!")
        else:
            messages.error(request, "Error adding rationale.")
    return redirect('appAdmin:about-rationale', pk=pk)


@user_access_required("admin")
def about_rationale_edit(request, rationale_id):
    rationale_item = get_object_or_404(AboutRationale, rationale_id=rationale_id)
    pk = rationale_item.about.about_id

    if request.method == "POST":
        form = AboutRationaleForm(request.POST, instance=rationale_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Rationale updated successfully!")
        else:
            messages.error(request, "Error updating rationale.")
    return redirect('appAdmin:about-rationale', pk=pk)


@user_access_required("admin")
@require_POST
def about_rationale_delete(request, rationale_id):
    rationale_item = get_object_or_404(AboutRationale, rationale_id=rationale_id)
    pk = rationale_item.about.about_id

    try:
        rationale_item.delete()
        messages.success(request, "Rationale deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting rationale.")
    
    return redirect('appAdmin:about-rationale', pk=pk)

# Objective View
@user_access_required("admin")
def about_objective(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    
    # Objective with details
    objective_items = AboutObjective.objects.filter(about_id=pk).prefetch_related('details')
    objective_form = AboutObjectiveForm(about_instance=about_instance, initial={'about': about_instance})
    objective_edit_forms = {
        item.objective_id: AboutObjectiveForm(instance=item, about_instance=about_instance)
        for item in objective_items
    }
    
    context = {
        "about": about_instance,
        "objective_items": objective_items,
        "objective_form": objective_form,
        "objective_edit_forms": objective_edit_forms,
    }
    return render(request, "pages/about-objective.html", context)

# Objective CRUD
@user_access_required("admin")
def about_objective_add(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    
    if request.method == "POST":
        # Create a custom form that handles POST data directly
        form = AboutObjectiveForm(about_instance=about_instance, initial={'about': about_instance})
        form.data = request.POST
        form.is_bound = True
        
        # Manually set the title field
        title = request.POST.get('title', '').strip()
        if title:
            form.cleaned_data = {'title': title, 'about': about_instance}
            
            # Collect detail data
            detail_data = {}
            for key, value in request.POST.items():
                if key.startswith('detail_') and value.strip():
                    try:
                        detail_index = int(key.split('_')[1])
                        detail_data[detail_index] = value.strip()
                    except (ValueError, IndexError):
                        continue
            
            # Validate
            if not title:
                messages.error(request, "Objective title is required.")
                return redirect('appAdmin:about-objective', pk=pk)
            
            if not detail_data:
                messages.error(request, "At least one detail is required for the objective.")
                return redirect('appAdmin:about-objective', pk=pk)
            
            try:
                # Create objective
                objective = AboutObjective.objects.create(
                    about=about_instance,
                    title=title
                )
                
                # Create details
                for index in sorted(detail_data.keys()):
                    detail_text = detail_data[index]
                    if detail_text:
                        AboutObjectiveDetail.objects.create(
                            objective=objective,
                            about=about_instance,
                            detail=detail_text
                        )
                
                messages.success(request, f"Objective added successfully with {len(detail_data)} details!")
                
            except Exception as e:
                messages.error(request, f"Error adding objective: {str(e)}")
        else:
            messages.error(request, "Objective title is required.")
    
    return redirect('appAdmin:about-objective', pk=pk)

@user_access_required("admin")
def about_objective_edit(request, pk):
    objective = get_object_or_404(AboutObjective, objective_id=pk)
    about_instance = objective.about
    
    if request.method == "POST":
        # Get the updated title
        title = request.POST.get('title', '').strip()
        
        if not title:
            messages.error(request, "Objective title is required.")
            return redirect('appAdmin:about-objective', pk=about_instance.about_id)
        
        # Collect detail data
        detail_data = {}
        for key, value in request.POST.items():
            if key.startswith('detail_') and value.strip():
                try:
                    detail_index = int(key.split('_')[1])
                    detail_data[detail_index] = value.strip()
                except (ValueError, IndexError):
                    continue
        
        # Validate that at least one detail exists
        if not detail_data:
            messages.error(request, "At least one detail is required for the objective.")
            return redirect('appAdmin:about-objective', pk=about_instance.about_id)
        
        try:
            # Update the objective title
            objective.title = title
            objective.save()
            
            # Clear existing details
            AboutObjectiveDetail.objects.filter(objective=objective).delete()
            
            # Create new details
            for index in sorted(detail_data.keys()):
                detail_text = detail_data[index]
                if detail_text:
                    AboutObjectiveDetail.objects.create(
                        objective=objective,
                        about=about_instance,
                        detail=detail_text
                    )
            
            messages.success(request, f"Objective '{objective.title}' updated successfully with {len(detail_data)} details!")
            
        except Exception as e:
            messages.error(request, f"Error updating objective: {str(e)}")
    
    return redirect('appAdmin:about-objective', pk=about_instance.about_id)

@user_access_required("admin")
@require_POST
def about_objective_delete(request, objective_id):
    objective_item = get_object_or_404(AboutObjective, objective_id=objective_id)
    pk = objective_item.about.about_id
    objective_title = objective_item.title
    
    try:
        # This will also delete related details due to CASCADE
        objective_item.delete()
        messages.success(request, f"Objective '{objective_title}' and all its details deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting objective: {str(e)}")
    
    return redirect('appAdmin:about-objective', pk=pk)
# Activity View

@user_access_required("admin")
def about_activity(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    activity_items = AboutActivity.objects.filter(about_id=pk)

    form = AboutActivityForm(initial={'about': about_instance})
    edit_forms = {item.activity_id: AboutActivityForm(instance=item) for item in activity_items}

    context = {
        "about": about_instance,
        "activity_items": activity_items,
        "form": form,
        "edit_forms": edit_forms,
    }
    return render(request, "pages/about-activity.html", context)


@user_access_required("admin")
def about_activity_add(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)

    if request.method == "POST":
        form = AboutActivityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Activity added successfully!")
        else:
            messages.error(request, "Error adding activity.")
    return redirect('appAdmin:about-activity', pk=pk)


@user_access_required("admin")
def about_activity_edit(request, activity_id):
    activity_item = get_object_or_404(AboutActivity, activity_id=activity_id)
    pk = activity_item.about.about_id

    if request.method == "POST":
        form = AboutActivityForm(request.POST, instance=activity_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Activity updated successfully!")
        else:
            messages.error(request, "Error updating activity.")
    return redirect('appAdmin:about-activity', pk=pk)


@user_access_required("admin")
@require_POST
def about_activity_delete(request, activity_id):
    activity_item = get_object_or_404(AboutActivity, activity_id=activity_id)
    pk = activity_item.about.about_id

    try:
        activity_item.delete()
        messages.success(request, "Activity deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting activity.")
    
    return redirect('appAdmin:about-activity', pk=pk)

# Timeline View

@user_access_required("admin")
def about_timeline(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    timeline_items = AboutTimeline.objects.filter(about_id=pk)

    form = AboutTimelineForm(initial={'about': about_instance})
    edit_forms = {item.timeline_id: AboutTimelineForm(instance=item) for item in timeline_items}

    context = {
        "about": about_instance,
        "timeline_items": timeline_items,
        "form": form,
        "edit_forms": edit_forms,
    }
    return render(request, "pages/about-timeline.html", context)


@user_access_required("admin")
def about_timeline_add(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)

    if request.method == "POST":
        form = AboutTimelineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Timeline added successfully!")
        else:
            messages.error(request, "Error adding timeline.")
    return redirect('appAdmin:about-timeline', pk=pk)


@user_access_required("admin")
def about_timeline_edit(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    pk = timeline_item.about.about_id

    if request.method == "POST":
        form = AboutTimelineForm(request.POST, instance=timeline_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Timeline updated successfully!")
        else:
            messages.error(request, "Error updating timeline.")
    return redirect('appAdmin:about-timeline', pk=pk)


@user_access_required("admin")
@require_POST
def about_timeline_delete(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    pk = timeline_item.about.about_id

    try:
        timeline_item.delete()
        messages.success(request, "Timeline deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting timeline.")
    
    return redirect('appAdmin:about-timeline', pk=pk)

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json

# Your existing imports and decorators should be included here

@user_access_required("admin")
@require_POST
def about_timeline_bullets_add(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    
    try:
        bullet_text = request.POST.get('bullet_text', '').strip()
        
        if not bullet_text:
            return JsonResponse({
                'success': False,
                'message': 'Bullet text is required.'
            })
        
        # Create new bullet
        bullet = AboutTimelineBullet.objects.create(
            timeline=timeline_item,
            details=bullet_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Bullet added successfully!',
            'bullet_id': bullet.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding bullet: {str(e)}'
        })


@user_access_required("admin")
@require_POST
def about_timeline_bullets_edit(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    
    try:
        bullet_id = request.POST.get('bullet_id')
        bullet_text = request.POST.get('bullet_text', '').strip()
        
        if not bullet_id or not bullet_text:
            return JsonResponse({
                'success': False,
                'message': 'Bullet ID and text are required.'
            })
        
        # Get and update the bullet
        bullet = get_object_or_404(AboutTimelineBullet, id=bullet_id, timeline=timeline_item)
        bullet.details = bullet_text
        bullet.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Bullet updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating bullet: {str(e)}'
        })


@user_access_required("admin")
@require_POST
def about_timeline_bullets_delete(request, bullet_id):
    try:
        bullet = get_object_or_404(AboutTimelineBullet, id=bullet_id)
        bullet.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Bullet deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting bullet: {str(e)}'
        })


@user_access_required("admin")
@require_POST
def about_timeline_images_add(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    
    try:
        image_file = request.FILES.get('image_file')
        
        if not image_file:
            return JsonResponse({
                'success': False,
                'message': 'Image file is required.'
            })
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'message': 'Please upload a valid image file.'
            })
        
        # Create new image
        image = AboutTimelineImage.objects.create(
            timeline=timeline_item,
            image=image_file
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Image added successfully!',
            'image_id': image.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding image: {str(e)}'
        })


@user_access_required("admin")
@require_POST
def about_timeline_images_edit(request, timeline_id):
    timeline_item = get_object_or_404(AboutTimeline, timeline_id=timeline_id)
    
    try:
        image_id = request.POST.get('image_id')
        image_file = request.FILES.get('image_file')
        
        if not image_id:
            return JsonResponse({
                'success': False,
                'message': 'Image ID is required.'
            })
        
        # Get the image
        image = get_object_or_404(AboutTimelineImage, id=image_id, timeline=timeline_item)
        
        # Update image file if provided
        if image_file:
            if not image_file.content_type.startswith('image/'):
                return JsonResponse({
                    'success': False,
                    'message': 'Please upload a valid image file.'
                })
            image.image = image_file
        
        # Update caption
        image.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Image updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating image: {str(e)}'
        })


@user_access_required("admin")
@require_POST
def about_timeline_images_delete(request, image_id):
    try:
        image = get_object_or_404(AboutTimelineImage, id=image_id)
        
        # Delete the image file from storage
        if image.image:
            image.image.delete(save=False)
        
        image.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Image deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting image: {str(e)}'
        })
   

# Team View

# @user_access_required("admin")
# def about_team(request, pk):
#     about_instance = get_object_or_404(About, about_id=pk)
#     team_items = AboutTeamMember.objects.filter(about_id=pk)

#     context = {
#         "about": about_instance,
#         "team_items": team_items,
#     }
#     return render(request, "pages/about-team.html", context)

@user_access_required("admin")
def about_team(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)
    team_items = AboutTeamMember.objects.filter(about_id=pk)

    form = AboutTeamMemberForm(initial={'about': about_instance})
    edit_forms = {item.member_id: AboutTeamMemberForm(instance=item) for item in team_items}

    # Socials form per team member
    social_forms = {item.member_id: AboutTeamSocialForm() for item in team_items}

    context = {
        "about": about_instance,
        "team_items": team_items,
        "form": form,
        "edit_forms": edit_forms,
        "social_forms": social_forms,
    }
    return render(request, "pages/about-team.html", context)


@user_access_required("admin")
def about_team_add(request, pk):
    about_instance = get_object_or_404(About, about_id=pk)

    if request.method == "POST":
        form = AboutTeamMemberForm(request.POST, request.FILES)  
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.about = about_instance 
            team_member.save()
            messages.success(request, "Team added successfully!")
        else:
            messages.error(request, "Error adding team.")
    return redirect('appAdmin:about-team', pk=pk)


@user_access_required("admin")
def about_team_edit(request, member_id):
    team_item = get_object_or_404(AboutTeamMember, member_id=member_id)
    pk = team_item.about.about_id

    if request.method == "POST":
        form = AboutTeamMemberForm(request.POST, request.FILES, instance=team_item)  
        if form.is_valid():
            form.save()
            messages.success(request, "Team updated successfully!")
        else:
            messages.error(request, "Error updating team.")
    return redirect('appAdmin:about-sub-project', pk=pk)


@user_access_required("admin")
@require_POST
def about_team_delete(request, member_id):
    team_item = get_object_or_404(AboutTeamMember, member_id=member_id)
    pk = team_item.about.about_id

    try:
        team_item.delete()
        messages.success(request, "Team deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting team.")
    
    return redirect('appAdmin:about-team', pk=pk)

@user_access_required("admin")
@require_POST
def about_team_social_add(request, member_id):
    member = get_object_or_404(AboutTeamMember, member_id=member_id)
    pk = member.about.about_id

    form = AboutTeamSocialForm(request.POST)
    if form.is_valid():
        social = form.save(commit=False)
        social.member = member
        social.save()
        messages.success(request, "Social link added successfully!")
    else:
        messages.error(request, "Error adding social link.")
    return redirect('appAdmin:about-team', pk=pk)

@user_access_required("admin")
@require_POST
def about_team_social_delete(request, social_id):
    social = get_object_or_404(AboutTeamSocial, social_id=social_id)
    pk = social.member.about.about_id
    social.delete()
    messages.success(request, "Social link deleted successfully!")
    return redirect('appAdmin:about-team', pk=pk)

# SUB PROJECTS
from appAdmin.models import AboutSubProject,AboutSubProjectRationale,AboutSubProjectObjective,AboutSubProjectObjectiveDetail,AboutSubProjectTimeline,AboutSubProjectTimelineBullet,AboutSubProjectTimelineImage,AboutSubProjectTeamSocial,AboutSubProjectTeamMember
from appAdmin.forms import AboutSubProjectForm,AboutSubProjectRationaleForm,AboutSubProjectObjectiveForm,AboutSubProjectTimelineForm,AboutSubProjectTeamMemberForm,AboutSubProjectTeamSocialForm

def about_sub_project(request, pk):
    """Display sub projects for a specific about page"""
    about = get_object_or_404(About, about_id=pk)
    sub_project_items = AboutSubProject.objects.filter(about=about).order_by('-date_created')
    
    # Create form for adding new sub project
    form = AboutSubProjectForm()
    
    # Create edit forms for each sub project
    edit_forms = {}
    for item in sub_project_items:
        edit_forms[item.sub_id] = AboutSubProjectForm(instance=item)
    
    context = {
        'about': about,
        'sub_project_items': sub_project_items,
        'form': form,
        'edit_forms': edit_forms,
    }
    return render(request, 'pages/about-sub-project.html', context)

def about_sub_project_add(request, about_id):
    """Add new sub project"""
    about = get_object_or_404(About, about_id=about_id)
    
    if request.method == 'POST':
        form = AboutSubProjectForm(request.POST, request.FILES)
        if form.is_valid():
            sub_project = form.save(commit=False)
            sub_project.about = about
            sub_project.save()
            messages.success(request, 'Sub project added successfully!')
            return redirect('appAdmin:about-sub-project', pk=about_id)
        else:
            messages.error(request, 'Please correct the errors below.')
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    return redirect('appAdmin:about-sub-project', pk=about_id)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages 

def about_sub_project_edit(request, sub_id):
    """Edit existing sub project"""
    sub_project = get_object_or_404(AboutSubProject, sub_id=sub_id)
    about_id = sub_project.about.about_id

    if request.method == 'POST':
        form = AboutSubProjectForm(request.POST, request.FILES, instance=sub_project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sub project updated successfully!')
            return redirect('appAdmin:about-sub-project', pk=about_id)
        else:
            messages.error(request, 'Please correct the errors below.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AboutSubProjectForm(instance=sub_project)

    return render(request, 'admin/about_sub_project_form.html', {
        'form': form,
        'sub_project': sub_project
    })


def about_sub_project_delete(request, sub_id):
    """Delete sub project"""
    sub_project = get_object_or_404(AboutSubProject, sub_id=sub_id)
    about_id = sub_project.about.about_id
    
    if request.method == 'POST':
        sub_project.delete()
        messages.success(request, 'Sub project deleted successfully!')
    
    return redirect('appAdmin:about-sub-project', pk=about_id)

# Sub Rationale View
@user_access_required("admin")
def about_sub_rationale(request, pk):
    """Display rationale items for a specific sub project"""
    # pk should be the sub_id, not about_id
    sub_project = get_object_or_404(AboutSubProject, sub_id=pk)
    rationale_items = AboutSubProjectRationale.objects.filter(about=sub_project).order_by('-rationale_id')
    
    # Create form for adding new rationale with pre-filled sub project
    form = AboutSubProjectRationaleForm(initial={'about': sub_project})
    
    # Create edit forms for each rationale item
    edit_forms = {}
    for item in rationale_items:
        edit_forms[item.rationale_id] = AboutSubProjectRationaleForm(instance=item)
    
    context = {
        'sub_project': sub_project,
        'about': sub_project.about,  # Include parent about for breadcrumb/navigation
        'rationale_items': rationale_items,
        'form': form,
        'edit_forms': edit_forms,
    }
    return render(request, 'pages/about-sub-rationale.html', context)

@user_access_required("admin")
def about_rationale_sub_add(request, pk):
    """Add new rationale for sub project"""
    sub_project = get_object_or_404(AboutSubProject, sub_id=pk)
    
    if request.method == "POST":
        form = AboutSubProjectRationaleForm(request.POST)
        if form.is_valid():
            rationale = form.save(commit=False)
            rationale.about = sub_project  # Set the sub project
            rationale.save()
            messages.success(request, "Rationale added successfully!")
        else:
            messages.error(request, "Error adding rationale.")
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    return redirect('appAdmin:about-sub-rationale', pk=pk)

@user_access_required("admin")
def about_rationale_sub_edit(request, rationale_id):
    """Edit existing rationale for sub project"""
    rationale_item = get_object_or_404(AboutSubProjectRationale, rationale_id=rationale_id)
    pk = rationale_item.about.sub_id  # Get the sub project ID
    
    if request.method == "POST":
        form = AboutSubProjectRationaleForm(request.POST, instance=rationale_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Rationale updated successfully!")
        else:
            messages.error(request, "Error updating rationale.")
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    return redirect('appAdmin:about-sub-rationale', pk=pk)

@user_access_required("admin")
@require_POST
def about_rationale_sub_delete(request, rationale_id):
    """Delete rationale for sub project"""
    rationale_item = get_object_or_404(AboutSubProjectRationale, rationale_id=rationale_id)
    pk = rationale_item.about.sub_id  # Get the sub project ID
    
    try:
        rationale_item.delete()
        messages.success(request, "Rationale deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting rationale: {str(e)}")
    
    return redirect('appAdmin:about-sub-rationale', pk=pk)


# Objective View for Sub Projects
@user_access_required("admin")
def about_sub_objective(request, pk):
    """Display sub project objectives page"""
    sub_project = get_object_or_404(AboutSubProject, sub_id=pk)
    about_instance = sub_project.about  # Get the main About instance
    objective_items = AboutSubProjectObjective.objects.filter(about=sub_project).prefetch_related('details')
    
    # Initialize form for adding new objective
    objective_form = AboutSubProjectObjectiveForm(about_instance=sub_project)
    
    context = {
        'sub_project': sub_project,
        'about': about_instance,
        'objective_items': objective_items,
        'objective_form': objective_form,
    }
    
    return render(request, 'pages/about-sub-objective.html', context)

@user_access_required("admin")
def about_objective_sub_add(request, pk):
    """Add new objective to sub project"""
    sub_project = get_object_or_404(AboutSubProject, sub_id=pk)
    
    if request.method == "POST":
        # Create form instance with the sub_project
        objective_form = AboutSubProjectObjectiveForm(request.POST, about_instance=sub_project)
        
        if objective_form.is_valid():
            # Get and validate title
            title = objective_form.cleaned_data['title']
            
            # Collect detail data
            detail_data = {}
            for key, value in request.POST.items():
                if key.startswith('detail_') and value.strip():
                    try:
                        detail_index = int(key.split('_')[1])
                        detail_data[detail_index] = value.strip()
                    except (ValueError, IndexError):
                        continue
            
            # Validate that at least one detail exists
            if not detail_data:
                messages.error(request, "At least one detail is required for the objective.")
                return redirect('appAdmin:about-sub-objective', pk=pk)
            
            try:
                # Create objective
                objective = AboutSubProjectObjective.objects.create(
                    about=sub_project,
                    title=title
                )
                
                # Create details
                for index in sorted(detail_data.keys()):
                    detail_text = detail_data[index]
                    if detail_text:
                        AboutSubProjectObjectiveDetail.objects.create(
                            objective=objective,
                            about=sub_project.about,  # Reference to main About instance
                            detail=detail_text
                        )
                
                messages.success(request, f"Objective added successfully with {len(detail_data)} details!")
                
            except Exception as e:
                messages.error(request, f"Error adding objective: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    
    return redirect('appAdmin:about-sub-objective', pk=pk)

@user_access_required("admin")
def about_objective_sub_edit(request, objective_id):
    """Edit existing objective"""
    objective = get_object_or_404(AboutSubProjectObjective, objective_id=objective_id)
    sub_project = objective.about
    
    if request.method == "POST":
        # Create form instance with the sub_project
        objective_form = AboutSubProjectObjectiveForm(request.POST, instance=objective, about_instance=sub_project)
        
        if objective_form.is_valid():
            # Get and validate title
            title = objective_form.cleaned_data['title']
            
            # Collect detail data
            detail_data = {}
            for key, value in request.POST.items():
                if key.startswith('detail_') and value.strip():
                    try:
                        detail_index = int(key.split('_')[1])
                        detail_data[detail_index] = value.strip()
                    except (ValueError, IndexError):
                        continue
            
            # Validate that at least one detail exists
            if not detail_data:
                messages.error(request, "At least one detail is required for the objective.")
                return redirect('appAdmin:about-sub-objective', pk=sub_project.sub_id)
            
            try:
                # Update the objective title
                objective.title = title
                objective.save()
                
                # Clear existing details and create new ones
                AboutSubProjectObjectiveDetail.objects.filter(objective=objective).delete()
                
                # Create new details
                for index in sorted(detail_data.keys()):
                    detail_text = detail_data[index]
                    if detail_text:
                        AboutSubProjectObjectiveDetail.objects.create(
                            objective=objective,
                            about=sub_project.about,  # Reference to main About instance
                            detail=detail_text
                        )
                
                messages.success(request, f"Objective '{objective.title}' updated successfully with {len(detail_data)} details!")
                
            except Exception as e:
                messages.error(request, f"Error updating objective: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    
    return redirect('appAdmin:about-sub-objective', pk=sub_project.sub_id)

@user_access_required("admin")
@require_POST
def about_objective_sub_delete(request, objective_id):
    """Delete objective and its details"""
    objective = get_object_or_404(AboutSubProjectObjective, objective_id=objective_id)
    sub_project = objective.about
    objective_title = objective.title
    
    try:
        # This will also delete related details due to CASCADE
        objective.delete()
        messages.success(request, f"Objective '{objective_title}' and all its details deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting objective: {str(e)}")
    
    return redirect('appAdmin:about-sub-objective', pk=sub_project.sub_id)


# Sub Timeline View
@user_access_required("admin")
def about_sub_timeline(request, pk):
    """Display timeline items for a sub project"""
    about_instance = get_object_or_404(AboutSubProject, sub_id=pk)
    timeline_items = AboutSubProjectTimeline.objects.filter(about__sub_id=pk)
    
    form = AboutSubProjectTimelineForm(initial={'about': about_instance})
    edit_forms = {item.timeline_id: AboutSubProjectTimelineForm(instance=item) for item in timeline_items}
    
    context = {
        "about": about_instance,
        "sub_about": about_instance,  # Template uses sub_about
        "timeline_items": timeline_items,  # Template uses timeline_items
        "form": form,
        "edit_forms": edit_forms,
    }
    return render(request, "pages/about-sub-timeline.html", context)

@user_access_required("admin")
def about_timeline_sub_add(request, pk):
    """Add new timeline item"""
    about_instance = get_object_or_404(AboutSubProject, sub_id=pk)
    
    if request.method == "POST":
        form = AboutSubProjectTimelineForm(request.POST)
        if form.is_valid():
            timeline_item = form.save(commit=False)
            timeline_item.about = about_instance
            timeline_item.save()
            messages.success(request, "Timeline added successfully!")
        else:
            messages.error(request, "Error adding timeline.")
    
    return redirect('appAdmin:about-sub-timeline', pk=pk)

@user_access_required("admin")
def about_timeline_sub_edit(request, timeline_id):
    """Edit existing timeline item"""
    timeline_item = get_object_or_404(AboutSubProjectTimeline, timeline_id=timeline_id)
    pk = timeline_item.about.sub_id
    
    if request.method == "POST":
        form = AboutSubProjectTimelineForm(request.POST, instance=timeline_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Timeline updated successfully!")
        else:
            messages.error(request, "Error updating timeline.")
    
    return redirect('appAdmin:about-sub-timeline', pk=pk)  # Fixed: use correct URL name

@user_access_required("admin")
@require_POST
def about_timeline_sub_delete(request, timeline_id):
    """Delete timeline item"""
    timeline_item = get_object_or_404(AboutSubProjectTimeline, timeline_id=timeline_id)
    pk = timeline_item.about.sub_id
    
    try:
        timeline_item.delete()
        messages.success(request, "Timeline deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting timeline.")
    
    return redirect('appAdmin:about-sub-timeline', pk=pk)  # Fixed: use correct URL name

# AJAX Views for Bullets and Images

@user_access_required("admin")
def timeline_bullet_add(request, timeline_id):
    """Add bullet to timeline via AJAX"""
    if request.method == 'POST':
        timeline_item = get_object_or_404(AboutSubProjectTimeline, timeline_id=timeline_id)
        bullet_text = request.POST.get('bullet_text', '').strip()
        
        if not bullet_text:
            return JsonResponse({'success': False, 'message': 'Bullet text is required'})
        
        try:
            bullet = AboutSubProjectTimelineBullet.objects.create(
                timeline=timeline_item,
                details=bullet_text
            )
            return JsonResponse({'success': True, 'message': 'Bullet added successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error adding bullet'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@user_access_required("admin")
def timeline_bullet_edit(request, timeline_id):
    """Edit bullet via AJAX"""
    if request.method == 'POST':
        bullet_id = request.POST.get('bullet_id')
        bullet_text = request.POST.get('bullet_text', '').strip()
        
        if not bullet_text:
            return JsonResponse({'success': False, 'message': 'Bullet text is required'})
        
        try:
            bullet = get_object_or_404(AboutSubProjectTimelineBullet, id=bullet_id)
            bullet.details = bullet_text
            bullet.save()
            return JsonResponse({'success': True, 'message': 'Bullet updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error updating bullet'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@user_access_required("admin")
@require_POST
def timeline_bullet_delete(request, bullet_id):
    """Delete bullet via AJAX"""
    try:
        bullet = get_object_or_404(AboutSubProjectTimelineBullet, id=bullet_id)
        bullet.delete()
        return JsonResponse({'success': True, 'message': 'Bullet deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error deleting bullet'})

@user_access_required("admin")
def timeline_image_add(request, timeline_id):
    """Add image to timeline via AJAX"""
    if request.method == 'POST':
        timeline_item = get_object_or_404(AboutSubProjectTimeline, timeline_id=timeline_id)
        image_file = request.FILES.get('image_file')
        
        if not image_file:
            return JsonResponse({'success': False, 'message': 'Image file is required'})
        
        try:
            image = AboutSubProjectTimelineImage.objects.create(
                timeline=timeline_item,
                image=image_file
            )
            return JsonResponse({'success': True, 'message': 'Image added successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error adding image'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@user_access_required("admin")
def timeline_image_edit(request, timeline_id):
    """Edit image via AJAX"""
    if request.method == 'POST':
        image_id = request.POST.get('image_id')
        image_file = request.FILES.get('image_file')
        
        try:
            image = get_object_or_404(AboutSubProjectTimelineImage, id=image_id)
            
            if image_file:
                # Delete old image if exists
                if image.image:
                    default_storage.delete(image.image.path)
                image.image = image_file
            
            image.save()
            return JsonResponse({'success': True, 'message': 'Image updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error updating image'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@user_access_required("admin")
@require_POST
def timeline_image_delete(request, image_id):
    """Delete image via AJAX"""
    try:
        image = get_object_or_404(AboutSubProjectTimelineImage, id=image_id)
        
        # Delete the actual image file
        if image.image:
            default_storage.delete(image.image.path)
        
        image.delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error deleting image'})
    

# TEAM SUB
@user_access_required("admin")
def about_sub_team(request, pk):
    about_instance = get_object_or_404(AboutSubProject, sub_id=pk)
    team_sub_items = AboutSubProjectTeamMember.objects.filter(about=about_instance)
    
    form = AboutSubProjectTeamMemberForm(initial={'about': about_instance})
    edit_forms = {item.member_id: AboutSubProjectTeamMemberForm(instance=item) for item in team_sub_items}
    
    # Socials form per team member
    social_forms = {item.member_id: AboutSubProjectTeamSocialForm() for item in team_sub_items}
    
    context = {
        "about": about_instance,
        "team_items": team_sub_items,
        "form": form,
        "edit_forms": edit_forms,
        "social_forms": social_forms,
    }
    return render(request, "pages/about-sub-team.html", context)


@user_access_required("admin")
def about_team_sub_add(request, pk):
    about_instance = get_object_or_404(AboutSubProject, sub_id=pk)
    
    if request.method == "POST":
        form = AboutSubProjectTeamMemberForm(request.POST, request.FILES)
        
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.about = about_instance
            team_member.save()
            messages.success(request, "Team member added successfully!")
        else:
            messages.error(request, "Error adding team member.")
    return redirect('appAdmin:about-sub-team', pk=pk)


@user_access_required("admin")
def about_team_sub_edit(request, member_id):
    team_item = get_object_or_404(AboutSubProjectTeamMember, member_id=member_id)
    pk = team_item.about.sub_id  # Fixed: should be sub_id, not about_id
    
    if request.method == "POST":
        form = AboutSubProjectTeamMemberForm(request.POST, request.FILES, instance=team_item)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Team member updated successfully!")
        else:
            messages.error(request, "Error updating team member.")
    return redirect('appAdmin:about-sub-team', pk=pk)


@user_access_required("admin")
@require_POST
def about_team_sub_delete(request, member_id):
    team_item = get_object_or_404(AboutSubProjectTeamMember, member_id=member_id)
    pk = team_item.about.sub_id  # Fixed: should be sub_id, not about_id
    
    try:
        team_item.delete()
        messages.success(request, "Team member deleted successfully!")
    except Exception:
        messages.error(request, "Error deleting team member.")
    
    return redirect('appAdmin:about-sub-team', pk=pk)


@user_access_required("admin")
@require_POST
def about_team_social_sub_add(request, member_id):
    member = get_object_or_404(AboutSubProjectTeamMember, member_id=member_id)
    pk = member.about.sub_id  # Fixed: should be sub_id, not about_id
    
    form = AboutSubProjectTeamSocialForm(request.POST)
    if form.is_valid():
        social = form.save(commit=False)
        social.member = member
        social.save()
        messages.success(request, "Social link added successfully!")
    else:
        messages.error(request, "Error adding social link.")
    return redirect('appAdmin:about-sub-team', pk=pk)


@user_access_required("admin")
@require_POST
def about_team_social_sub_delete(request, social_id):
    social = get_object_or_404(AboutSubProjectTeamSocial, social_id=social_id)
    pk = social.member.about.sub_id  # Fixed: should be sub_id, not about_id
    
    social.delete()
    messages.success(request, "Social link deleted successfully!")
    return redirect('appAdmin:about-sub-team', pk=pk)
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from utils.user_control import user_access_required
from utils.get_models import get_active_models
from appCmi.models import FAQ, FAQTag, FAQTagAssignment, FAQReaction, FAQImage
from appCmi.forms import FAQForm
import json

@user_access_required(["admin", "cmi"], error_type=404)
def faqs_view(request):
    """View function for the FAQs page."""
    models = get_active_models()
    useful_links = models.get("useful_links", [])
    commodities = models.get("commodities", [])
    knowledge_resources = models.get("knowledge_resources", [])

    form = FAQForm()
    
    search_query = request.GET.get('q', '').strip()
    
    tag_filter = request.GET.get('tag', 'all')
    
    if request.user.user_type == 'admin':
        # Admins can see all FAQs (active and inactive)
        faqs = FAQ.objects.all().select_related('created_by').prefetch_related('tag_assignments__tag', 'images')
    else:
        # Regular users only see active FAQs
        faqs = FAQ.objects.filter(is_active=True).select_related('created_by').prefetch_related('tag_assignments__tag', 'images')
    
    if search_query:
        faqs = faqs.filter(
            Q(question__icontains=search_query) | 
            Q(answer__icontains=search_query)
        )

    if tag_filter and tag_filter != 'all':
        faqs = faqs.filter(tag_assignments__tag__slug=tag_filter)
    
    if request.user.user_type == 'admin':
        tags_with_counts = FAQTag.objects.annotate(
            faq_count=Count('faq_assignments') 
        ).filter(faq_count__gt=0).order_by('name')
        total_faqs = FAQ.objects.count() 
    else:
        tags_with_counts = FAQTag.objects.annotate(
            faq_count=Count('faq_assignments', filter=Q(faq_assignments__faq__is_active=True))
        ).filter(faq_count__gt=0).order_by('name')
        total_faqs = FAQ.objects.filter(is_active=True).count() 
    
    all_tags = FAQTag.objects.all().order_by('name')

    user_faqs_count = 0
    if request.user.is_authenticated:
        user_faqs_count = FAQ.objects.filter(created_by=request.user).count()
    
    context = {
        "title": "FAQs",
        "useful_links": useful_links,
        "commodities": commodities,
        "knowledge_resources": knowledge_resources,
        "faqs": faqs,
        "tags_with_counts": tags_with_counts,
        "all_tags": all_tags,
        "total_faqs": total_faqs,
        "current_search": search_query,
        "current_tag": tag_filter,
        "form": form, 
        'user_faqs_count': user_faqs_count,
    }
    return render(request, "pages/cmi-faqs.html", context)

@user_access_required(["admin", "cmi"], error_type=404)
@require_POST
def add_faq(request):
    """Add a new FAQ"""
    try:
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        tag_ids = request.POST.getlist('tags')
        custom_tags = request.POST.get('custom_tags', '').strip()
        images = request.FILES.getlist('images')
        
        if not question or not answer:
            messages.error(request, 'Both question and answer are required.')
            return redirect('appCmi:faqs')
        
        # Create FAQ
        faq = FAQ.objects.create(
            question=question,
            answer=answer,
            created_by=request.user
        )
        
        # Add images
        for image in images:
            FAQImage.objects.create(faq=faq, image=image)
        
        # Add existing tags
        for tag_id in tag_ids:
            try:
                tag = FAQTag.objects.get(tag_id=tag_id)
                FAQTagAssignment.objects.create(faq=faq, tag=tag)
            except FAQTag.DoesNotExist:
                continue
        
        # Handle custom tags
        if custom_tags:
            # Split custom tags by comma and clean them
            custom_tag_names = [tag.strip() for tag in custom_tags.split(',') if tag.strip()]
            
            for tag_name in custom_tag_names:
                if len(tag_name) > 50:  # Check max length constraint
                    continue
                
                # Create or get the tag
                tag, created = FAQTag.objects.get_or_create(
                    name__iexact=tag_name,
                    defaults={'name': tag_name}
                )
                
                # Create assignment if it doesn't exist
                FAQTagAssignment.objects.get_or_create(faq=faq, tag=tag)
        
        messages.success(request, 'Successfully Added')
        
    except Exception as e:
        messages.error(request, f'❌ Error adding FAQ: {str(e)}')
    
    return redirect('appCmi:faqs')


@user_access_required(["admin", "cmi"], error_type=404)
@require_POST
def edit_faq(request, faq_id):
    """Edit an existing FAQ"""
    try:
        faq = get_object_or_404(FAQ, faq_id=faq_id)
        
        # Check permissions
        if not request.user.user_type == 'admin' and faq.created_by != request.user:
            messages.error(request, '❌ You can only edit your own FAQs.')
            return redirect('appCmi:faqs')
        
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        tag_ids = request.POST.getlist('tags')
        custom_tags = request.POST.get('custom_tags', '').strip()
        new_images = request.FILES.getlist('new_images')
        delete_image_ids = request.POST.getlist('delete_images')
        
        if not question or not answer:
            messages.error(request, '❌ Both question and answer are required.')
            return redirect('appCmi:faqs')
        
        # Store original question for success message
        original_question = faq.question
        
        # Update FAQ
        faq.question = question
        faq.answer = answer
        faq.updated_by = request.user
        faq.save()
        
        # Handle image deletions
        if delete_image_ids:
            deleted_count = faq.images.filter(image_id__in=delete_image_ids).count()
            faq.images.filter(image_id__in=delete_image_ids).delete()
        
        # Add new images
        new_images_count = len(new_images)
        for image in new_images:
            FAQImage.objects.create(faq=faq, image=image)
        
        # Update tags - clear existing assignments first
        faq.tag_assignments.all().delete()
        tags_added = 0
        
        # Add existing tags
        for tag_id in tag_ids:
            try:
                tag = FAQTag.objects.get(tag_id=tag_id)
                FAQTagAssignment.objects.create(faq=faq, tag=tag)
                tags_added += 1
            except FAQTag.DoesNotExist:
                continue
        
        # Handle custom tags
        custom_tags_added = 0
        if custom_tags:
            # Split custom tags by comma and clean them
            custom_tag_names = [tag.strip() for tag in custom_tags.split(',') if tag.strip()]
            
            for tag_name in custom_tag_names:
                if len(tag_name) > 50:  # Check max length constraint
                    continue
                
                # Create or get the tag
                tag, created = FAQTag.objects.get_or_create(
                    name__iexact=tag_name,
                    defaults={'name': tag_name}
                )
                
                # Create assignment if it doesn't exist
                FAQTagAssignment.objects.get_or_create(faq=faq, tag=tag)
                custom_tags_added += 1
        
        messages.success(request, 'Successfully Updated')
        
    except Exception as e:
        messages.error(request, f'❌ Error updating FAQ: {str(e)}')
    
    return redirect('appCmi:faqs')


@user_access_required(["admin", "cmi"], error_type=404)
def delete_faq(request, faq_id):
    """Delete an FAQ"""
    try:
        faq = get_object_or_404(FAQ, faq_id=faq_id)
        
        # Check permissions
        if not request.user.user_type == 'admin' and faq.created_by != request.user:
            messages.error(request, '❌ You can only delete your own FAQs.')
            return redirect('appCmi:faqs')
        
        question = faq.question
        images_count = faq.images.count()
        
        # Delete the FAQ (images will be deleted due to CASCADE)
        faq.delete()
        
        messages.success(request, 'Successfully Deleted')
        
    except Exception as e:
        messages.error(request, f'❌ Error deleting FAQ: {str(e)}')
    
    return redirect('appCmi:faqs')

@require_POST
def toggle_faq_status(request, faq_id):
    """Toggle FAQ active status (admin only)"""
    try:
        # Check if user is admin
        if request.user.user_type != 'admin':
            messages.error(request, '❌ Only administrators can toggle FAQ status.')
            return redirect('appCmi:faqs')
            
        faq = get_object_or_404(FAQ, faq_id=faq_id)
        
        old_status = faq.is_active
        faq.is_active = not faq.is_active
        faq.save()
        
        messages.success(request, 'Successfully Updated')
        
    except Exception as e:
        messages.error(request, f'❌ Error updating FAQ status: {str(e)}')
    
    return redirect('appCmi:faqs')

@user_access_required(["admin", "cmi"], error_type=404)
@require_POST
def toggle_faq_reaction(request, faq_id):
    """Toggle FAQ reaction"""
    try:
        faq = get_object_or_404(FAQ, faq_id=faq_id)
        
        reaction, created = FAQReaction.objects.get_or_create(
            faq=faq, 
            user=request.user
        )
        
        if not created:
            reaction.delete()
            reacted = False
        else:
            reacted = True
        
        return JsonResponse({
            'success': True,
            'reacted': reacted,
            'total_reactions': faq.total_reactions()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@user_access_required(["admin", "cmi"], error_type=404)
def get_faq_data(request, faq_id):
    """Get FAQ data for editing (AJAX)"""
    try:
        print(f"Getting FAQ data for ID: {faq_id}")  # Debug log
        faq = get_object_or_404(FAQ, faq_id=faq_id)
        tag_ids = list(faq.tag_assignments.values_list('tag__tag_id', flat=True))
        
        # Get existing images - FIXED: Use image_id instead of id
        images = []
        for img in faq.images.all():
            images.append({
                'id': img.image_id,  # Changed from img.id to img.image_id
                'url': img.image.url,
                'name': img.image.name
            })
        
        print(f"Found {len(images)} images for FAQ {faq_id}")  # Debug log
        
        response_data = {
            'success': True,
            'data': {
                'question': faq.question,
                'answer': faq.answer,
                'tag_ids': tag_ids,
                'images': images
            }
        }
        
        print(f"Returning data: {response_data}")  # Debug log
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error in get_faq_data: {str(e)}")  # Debug log
        return JsonResponse({'success': False, 'error': str(e)})
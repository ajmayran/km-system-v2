from django.shortcuts import render
from appAdmin.models import KnowledgeResources
from appAdmin.forms import KnowledgeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.urls import reverse
from utils.user_control import user_access_required


@user_access_required("admin")
def admin_knowledge_resources(request):
    knowledge_resources = KnowledgeResources.objects.filter(status="active")
    total_knowledge_resources = knowledge_resources.count()

    context = {
        "knowledge_resources": knowledge_resources,
        "total_knowledge_resources": total_knowledge_resources,
    }
    return render(request, "pages/knowledge-resources.html", context)


@user_access_required("admin")
def admin_add_knowledge_resource(request):
    if request.method == "POST":
        form = KnowledgeForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Knowledge Resources created successfully!"
            messages.success(request, success_message)
            return redirect("appAdmin:display-knowledge-resources")
        else:
            # Debugging: Check form errors when form is invalid
            print(form.errors)
    else:
        form = KnowledgeForm()
    return render(request, "pages/knowledge-resources.html", {"form": form})


@user_access_required("admin")
def admin_edit_knowledge_resource(request, slug):
    # Get the knowledge resource or return 404
    knowledge = get_object_or_404(KnowledgeResources, slug=slug)

    if request.method == "POST":
        form = KnowledgeForm(request.POST, instance=knowledge)
        if form.is_valid():
            knowledge = form.save(commit=False)  # Update instance
            knowledge.save()  # Save to the database

            # Success message
            messages.success(request, "Knowledge Resource edited successfully!")
            return redirect("appAdmin:display-knowledge-resources")
        else:
            print(form.errors)  # Debugging (remove in production)
    else:
        form = KnowledgeForm(instance=knowledge)

    return render(
        request,
        "pages/knowledge-resources.html",
        {"form": form, "knowledge": knowledge},
    )


@user_access_required("admin")
def admin_delete_knowledge_resource(request, slug):
    knowledge = get_object_or_404(
        KnowledgeResources, slug=slug
    )  # Fetch object by slug instead of ID
    knowledge.delete()

    messages.success(request, "Deleted successfully!")
    return redirect(reverse("appAdmin:display-knowledge-resources"))

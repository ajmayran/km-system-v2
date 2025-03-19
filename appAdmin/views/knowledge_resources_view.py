from django.shortcuts import render
from appAdmin.models import KnowledgeResources
from appAdmin.forms import KnowledgeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


def admin_knowledge_resources(request):
    knowledge_resources = KnowledgeResources.objects.filter(status="active")
    total_knowledge_resources = knowledge_resources.count()

    context = {
        "knowledge_resources": knowledge_resources,
        "total_knowledge_resources": total_knowledge_resources,
    }
    return render(request, "pages/knowledge-resources.html", context)


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


def admin_edit_knowledge_resource(request, slug):
    return render(request, "pages/knowledge-resources.html")


def admin_delete_knowledge_resource(request, slug):
    return render(request, "pages/knowledge-resources.html")

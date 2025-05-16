from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from appAdmin.models import CMI
from appAdmin.forms import CMIForm
from utils.user_control import user_access_required


@user_access_required("admin")
def admin_cmi(request):
    cmis = CMI.objects.filter(status="active")
    latest_resource = cmis.order_by("-date_created").first()
    pending_cmis = CMI.objects.filter(status="Pending")
    total_request_cmi = pending_cmis.count()
    total_approved_cmi = cmis.count()

    context = {
        "cmis": cmis,
        "latest_resource": latest_resource,
        "pending_cmis": pending_cmis,
        "total_request_cmi": total_request_cmi,
        "total_approved_cmi": total_approved_cmi,
    }
    return render(request, "pages/cmi.html", context)


@user_access_required("admin")
def admin_add_cmi(request):
    if request.method == "POST":
        form = CMIForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            success_message = "Added successfully!"
            messages.success(request, success_message)
            return redirect("appAdmin:display-cmi")
        else:
            print(form.errors)
    else:
        form = CMIForm()
    return render(request, "pages/cmi.html")


@user_access_required("admin")
def admin_edit_cmi(request, slug):
    cmi = get_object_or_404(CMI, slug=slug)  # Handle object not found properly

    if request.method == "POST":
        form = CMIForm(request.POST, request.FILES, instance=cmi)
        if form.is_valid():
            form.save()
            messages.success(request, "Edited successfully!")
            return redirect("appAdmin:display-cmi")
        else:
            messages.error(
                request, "There were errors in the form. Please check the fields below."
            )
    else:
        form = CMIForm(instance=cmi)

    return render(request, "pages/cmi.html", {"form": form, "cmi": cmi})


@user_access_required("admin")
def admin_delete_cmi(request, slug):
    cmi = get_object_or_404(CMI, slug=slug)  # Fetch object by slug instead of ID
    cmi.delete()

    messages.success(request, "Deleted successfully!")
    return redirect(reverse("appAdmin:display-cmi"))

from django.shortcuts import render
from appAdmin.models import UsefulLinks
from appAdmin.forms import UsefulLinksForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from utils.user_control import user_access_required


@user_access_required("admin")
def admin_useful_links(request):
    links = UsefulLinks.objects.all()
    latest_links = links.order_by("-date_created")

    context = {
        "latest_links": latest_links,
    }

    return render(request, "pages/useful-links.html", context)


@user_access_required("admin")
def admin_add_useful_link(request):
    if request.method == "POST":
        form = UsefulLinksForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            print(data)

            form.save()
            success_message = "Added successfully!"
            messages.success(request, success_message)
            return redirect("appAdmin:admin-useful-links")
        else:
            print(form.errors)
    else:
        form = UsefulLinksForm()
    return render(request, "pages/useful-links.html")


@user_access_required("admin")
def admin_edit_useful_link(request, id):
    link_instance = UsefulLinks.objects.get(link_id=id)

    if request.method == "POST":
        form = UsefulLinksForm(request.POST, instance=link_instance)
        if form.is_valid():
            data = form.cleaned_data
            print(data)

            form.save()
            success_message = "Edit successfully!"
            messages.success(request, success_message)
            return redirect("appAdmin:admin-useful-links")
        else:
            print(form.errors)
    else:
        form = UsefulLinksForm()
    return render(request, "pages/useful-links.html")


@user_access_required("admin")
def admin_delete_useful_link(request, id):
    link_instance = UsefulLinks.objects.get(link_id=id)
    link_instance.delete()
    success_message = "Deleted successfully!"
    messages.success(request, success_message)
    return redirect("appAdmin:admin-useful-links")

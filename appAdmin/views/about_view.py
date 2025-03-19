from django.shortcuts import render, redirect
from django.urls import reverse
from appAdmin.models import About, AboutFooter, UploadVideo
from appAdmin.forms import AboutForm, AboutFooterForm, UploadForm
from django.contrib import messages
from django.shortcuts import get_object_or_404


def admin_about_page(request):
    videos = UploadVideo.objects.last()
    about_content = About.objects.all()
    footer_content = AboutFooter.objects.all()
    existing_instance = About.objects.first()

    form = AboutForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        print("PAGE: ", form.cleaned_data)

        if existing_instance:
            return redirect("appAdmin:about-page-edit")

        form.save()
        return redirect("appAdmin:about-page")

    if form.errors:
        print("PAGE FORM ERRORS: ", form.errors)

    context = {
        "form": form,
        "about_content": about_content,
        "footer_content": footer_content,
        "videos": videos,
        "form_action": reverse(
            "appAdmin:about-page-edit" if about_content else "appAdmin:about-page"
        ),
        "form_action_footer": reverse(
            "appAdmin:about-footer-edit" if footer_content else "appAdmin:about-page"
        ),
    }

    return render(request, "pages/about.html", context)


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


def admin_about_page_edit(request):
    about_instance = get_object_or_404(About)
    form = AboutForm(request.POST or None, instance=about_instance)

    if request.method == "POST" and form.is_valid():
        print("EDIT PAGE", form.cleaned_data)
        form.save()
        return redirect("appAdmin:about-page")

    if form.errors:
        print("FORM ERRORS:", form.errors)

    return render(request, "pages/about.html", {"form": form})


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


def admin_upload_video(request):
    form = UploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Uploaded successfully!")
        return redirect("appAdmin:about-page")

    if form.errors:
        print("FORM ERRORS:", form.errors)

    return render(request, "pages/about.html", {"form": form})

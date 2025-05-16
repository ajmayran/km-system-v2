from django.shortcuts import render


# Create your views here.
def handler403(request, exception=None):
    return render(request, "pages/403.html", status=403)


def handler404(request, exception=None):
    return render(request, "pages/404.html", status=404)

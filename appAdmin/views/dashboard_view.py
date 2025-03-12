from django.shortcuts import render, redirect


def dashboard(request):
    return render(request, "pages/dashboard.html")


# def dashboard(request):
#     return render(request, "base/admin-index.html")

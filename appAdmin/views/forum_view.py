from django.shortcuts import render


def manage_forum(request):
    return render(request, "pages/admin-forum.html")

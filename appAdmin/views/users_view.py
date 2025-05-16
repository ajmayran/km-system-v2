from appAccounts.models import CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from utils.user_control import user_access_required


@user_access_required("admin")
def display_users(request):
    users = CustomUser.objects.all()
    return render(request, "pages/users.html", {"users": users})

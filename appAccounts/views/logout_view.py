from django.shortcuts import redirect
from django.contrib.auth import logout


def logout_user(request):
    logout(request)
    return redirect("appCmi:home") 

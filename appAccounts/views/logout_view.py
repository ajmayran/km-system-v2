from django.shortcuts import redirect
from django.contrib.auth import logout


def logout(request):
    logout(request)
    return redirect("appAccounts:login")

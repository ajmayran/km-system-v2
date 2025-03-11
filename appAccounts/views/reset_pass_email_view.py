from django.shortcuts import render


def reset_pass_email(request, uidb64, token):
    return render(request, "forgot-password/reset-pass.html")

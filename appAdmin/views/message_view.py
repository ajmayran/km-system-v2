from django.shortcuts import render
from utils.user_control import user_access_required


@user_access_required("admin")
def message_from_cmi(request):
    return render(request, "pages/message-to-admin.html")

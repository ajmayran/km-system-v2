from appAdmin.models import Commodity, CMI
from django.shortcuts import render
from utils.user_control import user_access_required


@user_access_required("admin")
def display_map(request):
    get_cmi = CMI.objects.all()
    get_commodity = Commodity.objects.all()

    context = {
        "get_cmi": get_cmi,
        "get_commodity": get_commodity,
    }
    return render(request, "pages/map.html", context)


@user_access_required("admin")
def map_add_cmi_commodity(request, name):
    get_cmi = CMI.objects.all()
    get_commodity = Commodity.objects.all()

    context = {
        "modal_name": name,
        "get_cmi": get_cmi,
        "get_commodity": get_commodity,
    }
    return render(request, "pages/map-add-cmi-commodity.html", context)

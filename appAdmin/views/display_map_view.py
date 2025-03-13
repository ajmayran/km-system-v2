from appAdmin.models import Commodity, CMI
from django.shortcuts import render


def display_map(request):
    get_cmi = CMI.objects.all()
    get_commodity = Commodity.objects.all()

    context = {
        "get_cmi": get_cmi,
        "get_commodity": get_commodity,
    }
    return render(request, "pages/map.html", context)

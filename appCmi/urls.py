from django.urls import path, include

urlpatterns = [
    path("cmis/", include("appCmi.urls")),  # ✅ Include appCmi URLs
]

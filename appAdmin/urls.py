from django.urls import path, include

urlpatterns = [
    path("admin/", include("appAdmin.urls")),  # ✅ Include appCmi URLs
]

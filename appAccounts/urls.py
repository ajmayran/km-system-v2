from django.urls import path, include

urlpatterns = [
    path("", include("appAccounts.urls")),  # ✅ Include appAccounts URLs
]

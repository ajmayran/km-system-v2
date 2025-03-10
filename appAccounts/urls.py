from django.urls import path, include

urlpatterns = [
    path("accounts/", include("appAccounts.urls")),  # ✅ Include appAccounts URLs
]

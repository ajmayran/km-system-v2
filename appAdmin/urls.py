from django.urls import path, include

urlpatterns = [
    path("admin/", include("appAdmin.urls")),  # ✅ Include appCmi URLs
]


# urls.py
# from django.urls import path
# from . import views

# app_name = "appAdmin"

# urlpatterns = [
#     path('about/', views.about_page_view, name='about-page'),
# ]


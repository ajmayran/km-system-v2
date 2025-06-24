from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appCmi.views import cmi_faqs_view

app_name = "appCmi"

urlpatterns = (
    [
        path("faqs/", cmi_faqs_view.faqs_view, name="faqs"),
        path("faqs/add/", cmi_faqs_view.add_faq, name="add-faq"),
        path("faqs/<int:faq_id>/edit/", cmi_faqs_view.edit_faq, name="edit-faq"),
        path("faqs/<int:faq_id>/delete/", cmi_faqs_view.delete_faq, name="delete-faq"),
        path("faqs/<int:faq_id>/toggle-status/", cmi_faqs_view.toggle_faq_status, name="toggle-faq-status"),
        path("faqs/<int:faq_id>/reaction/", cmi_faqs_view.toggle_faq_reaction, name="toggle-faq-reaction"),
        path("faqs/<int:faq_id>/data/", cmi_faqs_view.get_faq_data, name="get-faq-data"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
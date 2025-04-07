from .models import (
    Commodity,
    KnowledgeResources,
    About,
    AboutFooter,
    CMI,
    UploadVideo,
    UsefulLinks,
    ResourceMetadata,
    Event,
    InformationSystem,
    Map,
    Media,
    News,
    Policy,
    Project,
    Publication,
    Technology,
    TrainingSeminar,
    Webinar,
    Product,
    Tag,
)
from django import forms


class CommodityForm(forms.ModelForm):
    class Meta:
        model = Commodity
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CommodityForm, self).__init__(*args, **kwargs)
        self.fields["date_created"].required = False
        self.fields["commodity_img"].required = False
        self.fields["status"].required = False


class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = "__all__"


class AboutFooterForm(forms.ModelForm):
    class Meta:
        model = AboutFooter
        fields = "__all__"


class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = KnowledgeResources
        fields = ["knowledge_title", "knowledge_description"]


class CMIForm(forms.ModelForm):
    class Meta:
        model = CMI
        fields = [
            "cmi_name",
            "cmi_meaning",
            "cmi_description",
            "address",
            "contact_num",
            "email",
            "latitude",
            "longitude",
            "cmi_image",
            "url",
            "date_joined",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Making some fields optional
        for field in [
            "cmi_name",
            "cmi_meaning",
            "cmi_description",
            "address",
            "contact_num",
            "email",
            "latitude",
            "longitude",
            "url",
            "date_joined",
        ]:
            self.fields[field].required = False


class UploadForm(forms.ModelForm):
    class Meta:
        model = UploadVideo
        fields = "__all__"


class UsefulLinksForm(forms.ModelForm):
    class Meta:
        model = UsefulLinks
        fields = [
            "link_title",
            "link",
        ]

    def __init__(self, *args, **kwargs):
        super(UsefulLinksForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = False


class ResourceMetadataForm(forms.ModelForm):
    """Form for the common metadata fields for all resource types."""

    class Meta:
        model = ResourceMetadata
        fields = ["title", "description", "resource_type", "is_approved", "is_featured"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter resource title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Provide a detailed description",
                }
            ),
            "resource_type": forms.Select(
                attrs={"class": "form-select", "onchange": "showResourceFields()"}
            ),
            "is_approved": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "start_date",
            "end_date",
            "location",
            "organizer",
            "event_file",
            "is_virtual",
        ]
        widgets = {
            "start_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter event location"}
            ),
            "organizer": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter organizer name"}
            ),
            "event_file": forms.FileInput(attrs={"class": "form-control"}),
            "is_virtual": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class InformationSystemForm(forms.ModelForm):
    class Meta:
        model = InformationSystem
        fields = ["website_url", "system_owner", "last_updated"]
        widgets = {
            "website_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://example.com"}
            ),
            "system_owner": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter system owner"}
            ),
            "last_updated": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class MapForm(forms.ModelForm):
    class Meta:
        model = Map
        fields = ["map_file", "map_url", "latitude", "longitude"]
        widgets = {
            "map_file": forms.FileInput(attrs={"class": "form-control"}),
            "map_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/map",
                }
            ),
            "latitude": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.00000001"}
            ),
            "longitude": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.00000001"}
            ),
        }


class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ["media_type", "media_file", "media_url", "author"]
        widgets = {
            "media_type": forms.Select(attrs={"class": "form-select"}),
            "media_file": forms.FileInput(attrs={"class": "form-control"}),
            "media_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/media",
                }
            ),
            "author": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter media author/creator",
                }
            ),
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            "publication_date",
            "source",
            "external_url",
            "content",
            "featured_image",
        ]
        widgets = {
            "publication_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "source": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter news source"}
            ),
            "external_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/news",
                }
            ),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "featured_image": forms.FileInput(attrs={"class": "form-control"}),
        }


class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = [
            "policy_number",
            "effective_date",
            "issuing_body",
            "policy_file",
            "policy_url",
            "status",
        ]
        widgets = {
            "policy_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter policy reference number",
                }
            ),
            "effective_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "issuing_body": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter issuing authority",
                }
            ),
            "policy_file": forms.FileInput(attrs={"class": "form-control"}),
            "policy_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.com/policy",
                }
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "start_date",
            "end_date",
            "budget",
            "funding_source",
            "project_lead",
            "contact_email",
            "status",
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "budget": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "funding_source": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter funding source"}
            ),
            "project_lead": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project lead name",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Enter contact email"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            "authors",
            "publication_date",
            "publisher",
            "doi",
            "isbn",
            "publication_type",
            "publication_file",
        ]
        widgets = {
            "authors": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Comma-separated list of authors",
                }
            ),
            "publication_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "publisher": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter publisher name"}
            ),
            "doi": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., 10.1000/xyz123"}
            ),
            "isbn": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 978-3-16-148410-0",
                }
            ),
            "publication_type": forms.Select(attrs={"class": "form-select"}),
            "publication_file": forms.FileInput(attrs={"class": "form-control"}),
        }


class TechnologyForm(forms.ModelForm):
    class Meta:
        model = Technology
        fields = ["developer", "release_date", "patent_number", "license_type"]
        widgets = {
            "developer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter technology developer",
                }
            ),
            "release_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "patent_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter patent number if applicable",
                }
            ),
            "license_type": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter license type"}
            ),
        }


class TrainingSeminarForm(forms.ModelForm):
    class Meta:
        model = TrainingSeminar
        fields = ["start_date", "end_date", "location", "trainers", "target_audience"]
        widgets = {
            "start_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter training location",
                }
            ),
            "trainers": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "List of trainers/instructors",
                }
            ),
            "target_audience": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter target audience"}
            ),
        }


class WebinarForm(forms.ModelForm):
    class Meta:
        model = Webinar
        fields = ["webinar_date", "duration_minutes", "platform", "presenters"]
        widgets = {
            "webinar_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "duration_minutes": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "platform": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Zoom, Teams, etc.",
                }
            ),
            "presenters": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "List of presenters",
                }
            ),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["manufacturer", "features", "technical_specifications", "price"]
        widgets = {
            "manufacturer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter product manufacturer",
                }
            ),
            "features": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Key features of the product",
                }
            ),
            "technical_specifications": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Technical details",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Price in PHP",
                }
            ),
        }


class CommoditySelectForm(forms.Form):
    """Form for selecting multiple commodities."""

    commodities = forms.ModelMultipleChoiceField(
        queryset=Commodity.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        required=False,
    )


class TagForm(forms.ModelForm):
    """Form for creating new tags."""

    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter tag name"}
            )
        }

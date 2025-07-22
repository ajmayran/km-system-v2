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


# class AboutForm(forms.ModelForm):
#     class Meta:
#         model = About
#         fields = "__all__"


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
class CommonFormStyle:
    common_textarea_attrs = {
        'class': 'form-control',
        'rows': 3,
        'style': 'min-height: 36px;',
    }

    common_input_attrs = {
        'class': 'form-control',
        'style': 'min-height: 36px;',
    }

    
class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'widgets/custom_clearable_file_input.html'


from .models import (
    MainProgram,
    MainTitleBullet,
    MainTargetBullet,
    MainProgramImage,
    MainProgramObjective
)

class MainProgramObjectiveForm(forms.ModelForm, CommonFormStyle):
    class Meta:
        model = MainProgramObjective
        fields = ['title', 'target']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter objective title...',
                'required': True
            }),
            'target': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,
                'placeholder': 'Enter objective target...',
                'rows': 3
            }),
        }

# Combined bullet form for both title and target bullets
class ObjectiveBulletForm(forms.Form):
    # Title bullets
    title_bullets = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # Target bullets  
    target_bullets = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # For deletion tracking
    delete_title_bullets = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    delete_target_bullets = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )


# ✅ Main Program Form
class MainProgramForm(forms.ModelForm, CommonFormStyle):
    class Meta:
        model = MainProgram
        fields = ['project_rationale_desc', 'raise_project_desc', 'org_struct_image']
        widgets = {
            'project_rationale_desc': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,
                'placeholder': 'Enter project rationale...',
            }),
            'raise_project_desc': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,
                'placeholder': 'Enter raised project description...',
            }),
            'org_struct_image': CustomClearableFileInput(attrs={'class': 'form-control'}),
        }

# 📌 Form for MainTitleBullet
class MainTitleBulletForm(forms.ModelForm):
    class Meta:
        model = MainTitleBullet
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter title bullet...'
            }),
        }


# 🎯 Form for MainTargetBullet
class MainTargetBulletForm(forms.ModelForm):
    class Meta:
        model = MainTargetBullet
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter target bullet...'
            }),
        }

from django.core.exceptions import ValidationError
# 🖼️ Main Program Image Form with Custom File Inputclass MainProgramImageForm(forms.ModelForm):
class MainProgramImageForm(forms.ModelForm):
    class Meta:
        model = MainProgramImage
        fields = ['image', 'title', 'description']
        widgets = {
            'image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter description',
                'rows': 3
            }),
        }

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        word_count = len(description.split())

        if word_count > 100:
            raise ValidationError("Description must not exceed 100 words.")
        
        return description

from django import forms
from django import forms
from appAdmin.models import About

# Define icon choices outside Meta
ICON_CHOICES = [
    ('fas fa-heartbeat', 'Heartbeat'),
    ('fas fa-flask', 'Flask'),
    ('fas fa-lightbulb', 'Lightbulb'),
    ('fas fa-cogs', 'Cogs'),
    ('fas fa-seedling', 'Seedling'),
    ('fas fa-graduation-cap', 'Graduation Cap'),
    ('fas fa-rocket', 'Rocket'),
    ('fas fa-bolt', 'Bolt'),
    ('fas fa-chart-line', 'Chart Line'),
    ('fas fa-hands-helping', 'Helping Hands'),
]

# Define the AboutForm class with the custom widgets
from django import forms
from .models import (
    About,
    AboutRationale,
    AboutObjective,
    AboutObjectiveDetail,
    AboutActivity,
    AboutTimeline,
    AboutTeamMember,
    AboutTeamSocial,
    AboutTimeline, AboutTimelineBullet, AboutTimelineImage
)


# ✅ About Form

class AboutForm(forms.ModelForm, CommonFormStyle):
    class Meta:
        model = About
        fields = '__all__'
        widgets = {
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name...'
            }),
            'image': CustomClearableFileInput(attrs={'class': 'form-control'}),  # ✅ Fixed: Changed from 'profile_image' to 'image'
             'project_details': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project details...'
            }),
            'project_rationale_desc': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rationale...'
            }),
        }
    
    def clean_image(self):  # ✅ Fixed: Changed from clean_image to match field name
        image = self.cleaned_data.get('image')
        if image:
            # Add custom validation if needed
            print(f"Image received: {image}")  # Debug: Log the image
        return image
    
# ✅ About Rationale Form
class AboutRationaleForm(forms.ModelForm, CommonFormStyle):
    # icon = forms.ChoiceField(
    #     choices=ICON_CHOICES,
    #     widget=forms.Select(attrs={**CommonFormStyle.common_input_attrs})
    # )

    class Meta:
        model = AboutRationale
        fields = ['about', 
        # 'icon', 
        'title', 'detail']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={**CommonFormStyle.common_input_attrs, 'placeholder': 'Enter title...'}),
            'detail': forms.Textarea(attrs={**CommonFormStyle.common_textarea_attrs, 'placeholder': 'Enter detail...'}),
        }

# ✅ About Objective Form# ✅ About Objective Form with Dynamic Details
class AboutObjectiveForm(forms.ModelForm, CommonFormStyle):
    def __init__(self, *args, **kwargs):
        self.about_instance = kwargs.pop('about_instance', None)
        super().__init__(*args, **kwargs)

        if self.about_instance:
            self.fields['about'].initial = self.about_instance

        # Remove labels
        self.fields['about'].label = ''
        self.fields['title'].label = ''
        # Set default value for 'title' and hide it
        self.fields['title'].initial = 'Objective'
        self.fields['title'].widget = forms.HiddenInput()

    class Meta:
        model = AboutObjective
        fields = ['about', 'title']
        widgets = {
            'about': forms.HiddenInput(),
            # 'title' widget is overridden in __init__, so it's okay to skip styling here
        }



# ✅ About Objective Detail Form
class AboutObjectiveDetailForm(forms.ModelForm, CommonFormStyle):
     

    class Meta:
        model = AboutObjectiveDetail
        fields = ['about', 'detail']
        widgets = {
            'about': forms.HiddenInput(),
            'detail': forms.Textarea(attrs={**CommonFormStyle.common_textarea_attrs, 'placeholder': 'Enter detail...'}),
        }


# ✅ About Activity Form
class AboutActivityForm(forms.ModelForm, CommonFormStyle):
    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        widget=forms.Select(attrs={**CommonFormStyle.common_input_attrs})
    )

    class Meta:
        model = AboutActivity
        fields = ['about', 'icon', 'title', 'detail']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={**CommonFormStyle.common_input_attrs, 'placeholder': 'Enter title...'}),
            'detail': forms.Textarea(attrs={**CommonFormStyle.common_textarea_attrs, 'placeholder': 'Enter detail...'}),
        }


# ✅ About Timeline Formclass AboutTimelineForm(forms.ModelForm):
    class Meta:
        model = AboutTimeline
        fields = ['about', 'title', 'description', 'date_start', 'date_end']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter title...'
            }),
            'description': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter description...'
            }),
            'date_start': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
            'date_end': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
        }

    def clean(self):
        """Custom validation for the form"""
        cleaned_data = super().clean()
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')
        title = cleaned_data.get('title')
        
        # Validate that title is not empty
        if not title or not title.strip():
            raise forms.ValidationError("Title is required and cannot be empty.")
        
        # Validate date range
        if date_start and date_end:
            if date_start > date_end:
                raise forms.ValidationError("Start date must be before or equal to end date.")
        
        return cleaned_data

# forms.py - CORRECTED VERSION
class CommonFormStyle:
    """Common form styling attributes"""
    common_input_attrs = {
        'class': 'form-control',
    }
    common_textarea_attrs = {
        'class': 'form-control',
        'rows': 4,
    }

class AboutTimelineForm(forms.ModelForm):
    class Meta:
        model = AboutTimeline
        fields = ['about', 'title', 'description', 'date_start', 'date_end']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter title...'
            }),
            'description': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter description...'
            }),
            'date_start': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
            'date_end': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
        }

    def clean(self):
        """Custom validation for the form"""
        cleaned_data = super().clean()
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')
        title = cleaned_data.get('title')
        
        # Validate that title is not empty
        if not title or not title.strip():
            raise forms.ValidationError("Title is required and cannot be empty.")
        
        # Validate date range
        if date_start and date_end:
            if date_start > date_end:
                raise forms.ValidationError("Start date must be before or equal to end date.")
        
        return cleaned_data

class AboutTimelineBulletForm(forms.ModelForm):
    class Meta:
        model = AboutTimelineBullet
        fields = ['timeline', 'details']  # ✅ use 'details' instead of 'text'
        widgets = {
            'timeline': forms.HiddenInput(),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bullet point...'
            }),
        }


class AboutTimelineImageForm(forms.ModelForm):
    class Meta:
        model = AboutTimelineImage
        fields = ['timeline', 'image']  # ✅ only include actual fields
        widgets = {
            'timeline': forms.HiddenInput(),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
        }

# ✅ About Team Member Form

class AboutTeamMemberForm(forms.ModelForm):
    class Meta:
        model = AboutTeamMember
        fields = '__all__'
        labels = {
            'description': 'Specialization',
        }
        widgets = {
            'about': forms.HiddenInput(),
            'profile_image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name...'}),

             'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name...'}),
            'mid_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name (optional)...'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name...'}),


            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role...'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter specialization...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email...(optional)...'}),
        }

# ✅ About Team Social Form
SOCIAL_PLATFORM_CHOICES = [
    ('fab fa-facebook', 'Facebook'),
    ('fab fa-instagram', 'Instagram'),
    ('fab fa-tiktok', 'TikTok'),
    ('fab fa-twitter', 'Twitter'),
    ('fab fa-youtube', 'YouTube'),
    ('fab fa-github', 'GitHub'),
    ('fab fa-linkedin', 'LinkedIn'),
    ('fas fa-globe', 'Website'),
    ('fas fa-link', 'Other'),
]

class AboutTeamSocialForm(forms.ModelForm):
    platform = forms.ChoiceField(
        choices=SOCIAL_PLATFORM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Platform"
    )

    class Meta:
        model = AboutTeamSocial
        fields = ['platform', 'link']
        widgets = {
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Profile Link'}),
        }

# Sub Projects

from .models import (
    AboutSubProject,
    AboutSubProjectRationale,
    AboutSubProjectObjective,
    AboutSubProjectObjectiveDetail,
    AboutSubProjectTimeline,
    AboutSubProjectTimelineBullet,
    AboutSubProjectTimelineImage,
    AboutSubProjectTeamMember,
    AboutSubProjectTeamSocial
)


# ✅ About Form

class AboutSubProjectForm(forms.ModelForm, CommonFormStyle):
    class Meta:
        model = AboutSubProject
        fields = ['project_name', 'image', 'project_details', 'project_rationale_desc']
        widgets = {
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name...',
                'required': True
            }),
            'image': CustomClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'project_details': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project details...',
                'rows': 4
            }),
            'project_rationale_desc': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rationale...',
                'rows': 4
            }),
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate file size (optional)
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file size should not exceed 5MB")
            
            # Validate file type (optional)
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("Please upload a valid image file")
        
        return image
    
    def clean_project_name(self):
        project_name = self.cleaned_data.get('project_name')
        if not project_name or not project_name.strip():
            raise forms.ValidationError("Project name is required")
        return project_name.strip()
    
class AboutSubProjectRationaleForm(forms.ModelForm, CommonFormStyle):
    class Meta:
        model = AboutSubProjectRationale
        fields = ['about', 
        # 'icon', 
        'title', 'detail']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={**CommonFormStyle.common_input_attrs, 'placeholder': 'Enter title...'}),
            'detail': forms.Textarea(attrs={**CommonFormStyle.common_textarea_attrs, 'placeholder': 'Enter detail...'}),
        }


class AboutSubProjectObjectiveForm(forms.ModelForm, CommonFormStyle):
    def __init__(self, *args, **kwargs):
        self.about_instance = kwargs.pop('about_instance', None)
        super().__init__(*args, **kwargs)

        if self.about_instance:
            self.fields['about'].initial = self.about_instance

        # Hide title field with default value
        self.fields['title'].initial = 'Objective'
        self.fields['title'].widget = forms.HiddenInput()

        # Remove labels
        self.fields['about'].label = ''
        self.fields['title'].label = ''

    class Meta:
        model = AboutSubProjectObjective
        fields = ['about', 'title']
        widgets = {
            'about': forms.HiddenInput(),
            # 'title' widget is overridden above
        }


class AboutSubProjectObjectiveDetailForm(forms.ModelForm, CommonFormStyle):
    def __init__(self, *args, **kwargs):
        self.about_instance = kwargs.pop('about_instance', None)
        super().__init__(*args, **kwargs)
        if self.about_instance:
            self.fields['about'].initial = self.about_instance.about  # Reference to main About instance

    class Meta:
        model = AboutSubProjectObjectiveDetail
        fields = ['about', 'detail']
        widgets = {
            'about': forms.HiddenInput(),
            'detail': forms.Textarea(attrs={**CommonFormStyle.common_textarea_attrs, 'placeholder': 'Enter detail...'}),
        }

# SUB TIMELINE

class AboutSubProjectTimelineForm(forms.ModelForm):
    class Meta:
        model = AboutSubProjectTimeline
        fields = ['about', 'title', 'description', 'date_start', 'date_end']
        widgets = {
            'about': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter title...'
            }),
            'description': forms.Textarea(attrs={
                **CommonFormStyle.common_textarea_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'Enter description...'
            }),
            'date_start': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
            'date_end': forms.DateInput(attrs={
                **CommonFormStyle.common_input_attrs,  # Fixed: Use ** to unpack dictionary
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }),
        }

    def clean(self):
        """Custom validation for the form"""
        cleaned_data = super().clean()
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')
        title = cleaned_data.get('title')
        
        # Validate that title is not empty
        if not title or not title.strip():
            raise forms.ValidationError("Title is required and cannot be empty.")
        
        # Validate date range
        if date_start and date_end:
            if date_start > date_end:
                raise forms.ValidationError("Start date must be before or equal to end date.")
        
        return cleaned_data

class AboutSubProjectTimelineBulletForm(forms.ModelForm):
    class Meta:
        model = AboutSubProjectTimelineBullet
        fields = ['timeline', 'details']  # ✅ use 'details' instead of 'text'
        widgets = {
            'timeline': forms.HiddenInput(),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bullet point...'
            }),
        }


class AboutSubProjectTimelineImageForm(forms.ModelForm):
    class Meta:
        model = AboutSubProjectTimelineImage
        fields = ['timeline', 'image']  # ✅ only include actual fields
        widgets = {
            'timeline': forms.HiddenInput(),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
        }

# SUB TEAM

class AboutSubProjectTeamMemberForm(forms.ModelForm):
    class Meta:
        model = AboutSubProjectTeamMember
        fields = '__all__'
        labels = {
            'description': 'Specialization',
        }
        widgets = {
            'about': forms.HiddenInput(),
            'profile_image': CustomClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name...'}),

             'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name...'}),
            'mid_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name (optional)...'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name...'}),


            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role...'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter specialization...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email...(optional)...'}),
        }

class AboutSubProjectTeamSocialForm(forms.ModelForm):
    platform = forms.ChoiceField(
        choices=SOCIAL_PLATFORM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Platform"
    )

    class Meta:
        model = AboutSubProjectTeamSocial
        fields = ['platform', 'link']
        widgets = {
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Profile Link'}),
        }
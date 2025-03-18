from .models import Commodity, KnowledgeResources, About, AboutFooter, CMI
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
        super(CMIForm, self).__init__(*args, **kwargs)

        # Make specific fields not required
        for field_name in [
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
            self.fields[field_name].required = False

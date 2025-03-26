from .models import Forum
from django import forms
from appAdmin.models import Commodity


class ForumForm(forms.ModelForm):
    commodity_id = forms.ModelMultipleChoiceField(queryset=Commodity.objects.all())

    class Meta:
        model = Forum
        fields = ["forum_title", "forum_question", "commodity_id"]

from .models import Forum
from django import forms
from appAdmin.models import Commodity


class ForumForm(forms.ModelForm):

    class Meta:
        model = Forum
        fields = ["forum_title", "forum_question"]

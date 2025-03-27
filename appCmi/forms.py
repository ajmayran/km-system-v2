from .models import Forum, ForumComment
from django import forms
from appAdmin.models import Commodity


class ForumForm(forms.ModelForm):

    class Meta:
        model = Forum
        fields = ["forum_title", "forum_question"]


class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ["content", "parent"]
        widgets = {
            "content": forms.Textarea(attrs={"placeholder": "Write a comment..."}),
            "parent": forms.HiddenInput(),
        }
        labels = {
            "content": "",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.post = kwargs.pop("post", None)
        super(ForumCommentForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ForumCommentForm, self).save(commit=False)

        if self.user:
            instance.user = self.user

        if self.post:
            instance.post = self.post

        if commit:
            instance.save()

        return instance

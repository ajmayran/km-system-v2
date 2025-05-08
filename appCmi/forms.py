from .models import Forum, ForumComment, MessageToAdmin
from django import forms


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


class MessageToAdminForm(forms.ModelForm):
    class Meta:
        model = MessageToAdmin
        fields = ["subject", "message", "category"]
        widgets = {
            "subject": forms.TextInput(
                attrs={"placeholder": "What is your message about?"}
            ),
            "message": forms.Textarea(
                attrs={"rows": "5", "placeholder": "Type your message here..."}
            ),
        }
        labels = {"subject": "Subject", "message": "Message", "category": "Category"}
        help_texts = {
            "message": "Please provide as much detail as possible to help us assist you better."
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(MessageToAdminForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(MessageToAdminForm, self).save(commit=False)

        if self.user:
            instance.user = self.user
            instance.status = "pending"  # Set initial status

        if commit:
            instance.save()

        return instance

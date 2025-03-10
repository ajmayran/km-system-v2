from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm,
)
from .models import CustomUser, Profile


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a new user with necessary fields."""

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "middle_name",
            "institution",
            "position",
            "date_birth",
            "sex",
            "gender",
            "specialization",
            "highest_educ",
            "contact_num",
            "user_type",
        )
        widgets = {
            "date_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_email(self):
        """Ensure email is unique before saving."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class CustomUserUpdateForm(UserChangeForm):
    """Form for updating user information (excluding password)."""

    password = None  # Hides the password field

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "middle_name",
            "institution",
            "position",
            "date_birth",
            "sex",
            "gender",
            "specialization",
            "highest_educ",
            "contact_num",
            "user_type",
        )
        widgets = {
            "date_birth": forms.DateInput(attrs={"type": "date"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Form for changing a user's password securely."""

    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter current password"}
        ),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter new password"}
        ),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm new password"}
        ),
    )


class ProfileForm(forms.ModelForm):
    """Form for updating user profile picture."""

    class Meta:
        model = Profile
        fields = ("picture",)

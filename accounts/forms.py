from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Barangay, User


def normalize_mobile(value):
    """+639XXXXXXXXX and 09XXXXXXXXX are the same number: store the 09 form."""
    value = value.strip().replace(" ", "").replace("-", "")
    if value.startswith("+63"):
        value = "0" + value[3:]
    return value


class ContactCleanMixin:
    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_mobile_number(self):
        return normalize_mobile(self.cleaned_data["mobile_number"])


class RegistrationForm(ContactCleanMixin, forms.ModelForm):
    """Resident self-registration (BR-01 to BR-05)."""

    account_role = User.Role.RESIDENT

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email", "mobile_number", "barangay"]
        labels = {"full_name": "Full name", "mobile_number": "Mobile number"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barangay"].queryset = Barangay.objects.filter(is_active=True)
        self.fields["barangay"].empty_label = "Select your barangay"

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "The two password fields did not match.")
            else:
                try:
                    password_validation.validate_password(p1)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # hashed, never plain text
        user.role = self.account_role
        user.points_balance = 0
        if commit:
            user.save()
        return user


class StaffCreateForm(RegistrationForm):
    """BR-05: staff accounts are created only by a logged-in staff user."""

    account_role = User.Role.STAFF


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Invalid email or password. Please try again.",
        "inactive": "This account has been deactivated.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"


class ProfileForm(ContactCleanMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "mobile_number", "notification_pref"]
        labels = {"full_name": "Full name", "mobile_number": "Mobile number", "notification_pref": "Reminder channel"}

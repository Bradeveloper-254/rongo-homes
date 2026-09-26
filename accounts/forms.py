
from django import forms
from django.core.validators import RegexValidator
import re
from django.core.exceptions import ValidationError



strong_password_validator = RegexValidator(
    regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$",
    message=(
        "Password must contain at least one uppercase letter, "
        "one lowercase letter, one number, and one special character."
    ),
)



def validate_kenyan_phone(value):
    phone = value.strip()

    if phone.startswith("+254"):
        phone = "254" + phone[4:]
    elif phone.startswith("07") or phone.startswith("01"):
        phone = "254" + phone[1:]

    if not re.fullmatch(r"254(?:7|1)\d{8}", phone):
        raise ValidationError(
            "Enter a valid Kenyan mobile number."
        )


class RegistrationForm(forms.Form):

    full_name = forms.CharField(
        max_length=100,
        label="Full Name"
    )

    email = forms.EmailField(
        label="Email Address"
    )

    phone = forms.CharField(
        max_length=13,
        validators=[validate_kenyan_phone],
        widget=forms.TextInput(
            attrs={
                "maxlength": "13",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }
        ),
    )

    password = forms.CharField(
        min_length=8,
        label="Password",
        validators=[
            strong_password_validator
        ],
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter a strong password"
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm your password"
            }
        ),
        label="Confirm Password"
    )

    role = forms.ChoiceField(
        choices=[
            ("student", "Student"),
            ("owner", "Property Owner / Caretaker"),
        ],
        label="Account Type"
    )

    id_document = forms.FileField(
        required=False,
        label="Identification Document"
    )

    ownership_document = forms.FileField(
        required=False,
        label="Ownership / Management Document"
    )

    additional_document = forms.FileField(
        required=False,
        label="Additional Document"
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the Rongo Homes Terms and Conditions."
    )

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get(
            "password"
        )

        confirm_password = cleaned_data.get(
            "confirm_password"
        )

        role = cleaned_data.get(
            "role"
        )

        if password and confirm_password:

            if password != confirm_password:

                self.add_error(
                    "confirm_password",
                    "Passwords do not match."
                )

        if role == "owner":

            if not cleaned_data.get(
                "id_document"
            ):

                self.add_error(
                    "id_document",
                    "Identification document is required for owner accounts."
                )

            if not cleaned_data.get(
                "ownership_document"
            ):

                self.add_error(
                    "ownership_document",
                    "Ownership or management document is required for owner accounts."
                )

        return cleaned_data
    
    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        if phone.startswith("+254"):
            phone = "254" + phone[4:]
        elif phone.startswith("07") or phone.startswith("01"):
            phone = "254" + phone[1:]

        if not re.fullmatch(r"254(?:7|1)\d{8}", phone):
            raise forms.ValidationError(
                "Enter a valid Kenyan mobile number."
            )

        return phone
    


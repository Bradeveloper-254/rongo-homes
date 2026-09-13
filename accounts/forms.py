
from django import forms


class RegistrationForm(forms.Form):

    full_name = forms.CharField(
        max_length=100,
        label="Full Name"
    )

    email = forms.EmailField(
        label="Email Address"
    )

    phone = forms.CharField(
        max_length=20,
        label="Phone Number"
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password"
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
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

                raise forms.ValidationError(
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


from django import forms


from django import forms


class MultipleFileInput(
    forms.ClearableFileInput
):

    allow_multiple_selected = True


class PropertyPhotoForm(forms.Form):

    photos = forms.FileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "accept": "image/*",
                "multiple": True
            }
        )
    )
    
from django import forms


class PropertySearchForm(forms.Form):

    keyword = forms.CharField(
        required=False
    )

    location = forms.CharField(
        required=False
    )

    min_price = forms.FloatField(
        required=False,
        min_value=0
    )

    max_price = forms.FloatField(
        required=False,
        min_value=0
    )

    room_type = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any room type"),
            ("single", "Single Room"),
            ("bedsitter", "Bedsitter"),
            ("double", "Double Room"),
            ("self_contained", "Self Contained"),
        ]
    )

    amenities = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("wifi(self subscription)", "Wi-Fi(self subscription)"),
                        ("water", "Water"),
                        ("electricity", "Electricity"),
                        ("security", "Security"),
                        ("cctv", "CCTV"),
                        ("parking", "Parking"),
                        ("kitchen", "Kitchen"),
                        ("hot_shower", "Hot Shower"),
                        ("tap_water", "Tap Water"),
                        ("Borehole", "Borehole"),
                        ("Bed&Matress", "Bed&Matress"),
                        ("Study chair", "Study Chair"),
                        ("Study Table", "Study Table"), 
        ],
        widget=forms.CheckboxSelectMultiple
    )

    max_distance = forms.FloatField(
        required=False,
        min_value=0
    )
    
from django import forms


class PropertyReportForm(forms.Form):

    reason = forms.ChoiceField(
        choices=[
            (
                "fake_property",
                "Fake property"
            ),
            (
                "already_occupied",
                "Property is already occupied"
            ),
            (
                "incorrect_price",
                "Incorrect price"
            ),
            (
                "incorrect_location",
                "Incorrect location"
            ),
            (
                "misleading_information",
                "Misleading information"
            ),
            (
                "inappropriate_content",
                "Inappropriate content"
            ),
            (
                "other",
                "Other"
            ),
        ]
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder":
                    "Please explain the problem..."
            }
        )
    )
    

from django import forms


class PropertyForm(forms.Form):

    name = forms.CharField(
        max_length=200,
        required=True,
        label="Property Name"
    )

    description = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "maxlength": 2000,
                "placeholder": "Describe your property..."
            }
        )
    )

    area = forms.CharField(
        max_length=200,
        required=True,
        label="Area"
    )

    landmark = forms.CharField(
        max_length=200,
        required=False,
        label="Landmark"
    )

    latitude = forms.FloatField(
        required=False
    )

    longitude = forms.FloatField(
        required=False
    )

    distance_from_university = forms.FloatField(
        required=False,
        min_value=0
    )

    monthly_price = forms.FloatField(
        required=False,
        min_value=0
    )

    semester_price = forms.FloatField(
        required=False,
        min_value=0
    )
    Cost_Sharing= forms.FloatField(
        required=False,
        min_value=0
    )
    caretaker_name = forms.CharField(
    max_length=20,
    required=False
    )

    caretaker_contact = forms.CharField(
        max_length=30,
        required=False
    )

    landlord_name = forms.CharField(
        max_length=20,
        required=False
    )

    landlord_contact = forms.CharField(
        max_length=30,
        required=False
    )

    amenities = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("wifi(self subscription)", "Wi-Fi(self subscription)"),
            ("water", "Water"),
            ("electricity", "Electricity"),
            ("security", "Security"),
            ("cctv", "CCTV"),
            ("parking", "Parking"),
            ("kitchen", "Kitchen"),
            ("hot_shower", "Hot Shower"),
            ("tap_water", "Tap Water"),
            ("Borehole", "Borehole"),
            ("Bed&Matress", "Bed&Matress"),
            ("Study chair", "Study Chair"),
            ("Study Table", "Study Table"),
            
        ],
        widget=forms.CheckboxSelectMultiple
    )
from django import forms


class RoomForm(forms.Form):

    room_number = forms.CharField(
        max_length=50,
        required=True
    )

    room_type = forms.CharField(
        max_length=100,
        required=True
    )

    price = forms.FloatField(
        required=True,
        min_value=0
    )

    status = forms.ChoiceField(
        choices=[
            ("vacant", "Vacant"),
            ("occupied", "Occupied"),
            ("reserved", "Reserved"),
            ("maintenance", "Maintenance"),
        ],
        initial="vacant"
    )
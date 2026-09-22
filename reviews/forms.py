from django import forms


class ReviewForm(forms.Form):

    rating = forms.ChoiceField(
        choices=[
            (5, "★★★★★ Excellent"),
            (4, "★★★★ Very Good"),
            (3, "★★★ Good"),
            (2, "★★ Fair"),
            (1, "★ Poor"),
        ]
    )

    comment = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder":
                    "Tell other students about your experience..."
            }
        )
    )
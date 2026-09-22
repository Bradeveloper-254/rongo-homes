from django.db import models
from mongoengine import (
    Document,
    StringField,
    DateTimeField
)


class Report(Document):

    student_id = StringField(required=True)

    property_id = StringField(required=True)

    reason = StringField(
        required=True,
        max_length=200
        )

    description = StringField(
        required=False,
        max_length=2000
    )

    status = StringField(
        default="pending"
    )

    created_at = DateTimeField()

    meta = {
        "collection": "reports"
    }
    

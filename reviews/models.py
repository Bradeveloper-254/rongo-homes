from django.db import models
import datetime
from mongoengine import (
    Document,
    StringField,
    IntField,
    DateTimeField
)
class Review(Document):

    student_id = StringField(
        required=True
    )

    property_id = StringField(
        required=True
    )

    rating = IntField(
        required=True,
        min_value=1,
        max_value=5
    )

    comment = StringField()

    status = StringField(
        required=True,
        choices=[
            "pending",
            "approved",
            "rejected"
        ],
        default="pending"
    )

    created_at = DateTimeField()

    updated_at = DateTimeField()

    meta = {
        "collection": "reviews",

        "indexes": [
            {
                "fields": [
                    "student_id",
                    "property_id"
                ],
                "unique": True
            }
        ]
    }
    

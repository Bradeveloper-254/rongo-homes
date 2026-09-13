import datetime

from django.db import models

from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField,
)


class Notification(Document):
    recipient_id = StringField(required=True)
    user_id=StringField(required=True)
    recipient_role = StringField(
        required=True,
        choices=[
            "student",
            "owner",
            "admin",
        ]
    )

    notification_type = StringField(
        required=True,
          choices=[
        "owner_registered",
        "property_submitted",
        "report_submitted",
        "review_submitted",

        "owner_approved",
        "owner_rejected",
        "owner_suspended",

        "property_approved",
        "property_rejected",
        "property_suspended",
        "property_activated",

        "review_approved",
        "review_rejected",

        "announcement",
    ]

    )

    title = StringField(required=True)
    message = StringField(required=True)
    link = StringField(default="")
    related_id = StringField(required=False)

    is_read = BooleanField(default=False)

    created_at = DateTimeField(required=True)

    meta = {
        "collection": "notifications",
        "indexes": [
            "-created_at",
            "recipient_id",
            "is_read",
        ]
    }
from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField
)


class User(Document):

    full_name = StringField(
        required=True,
        max_length=100
    )
    
    email = StringField(
        required=True,
        unique=True
    )
    is_active = BooleanField(default=True)

    phone = StringField(
        required=True
    )

    password = StringField(
        required=True
    )

    role = StringField(
        required=True,
        choices=[
            "student",
            "owner",
            "admin"
        ]
    )

    status = StringField(
        required=True,
        choices=[
            "pending",
            "active",
            "rejected",
            "suspended"
        ],
        default="active"
    )

    is_verified = BooleanField(
        default=False
    )

    created_at = DateTimeField()

    updated_at = DateTimeField()

   
    
    id_document = StringField()

    ownership_document = StringField()

    additional_document = StringField()
    password_reset_token = StringField()
    password_reset_expires = DateTimeField()

    meta = {
        "collection": "users"
    }
from django.db import models

# Create your models here.
from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField
)


class Payment(Document):

    transaction_id = StringField(
        required=True,
        unique=True
    )

    student_id = StringField(
        required=True
    )

    property_id = StringField(
        required=True
    )

    amount = FloatField(
        required=True
    )

    currency = StringField(
        default="KES"
    )

    payment_method = StringField(
        default="mpesa"
    )

    status = StringField(
    choices=[
        "pending",
        "successful",
        "failed",
        "cancelled"
    ],
    default="pending"
  )
    payment_type = StringField(
    choices=[
        "contact_unlock",
        "reservation",
        "other"
    ],
    default="contact_unlock"
   )   
    mpesa_reference = StringField()
    
    merchant_request_id = StringField()

    phone_number = StringField()

    result_code = StringField()

    result_description = StringField()

    created_at = DateTimeField()

    updated_at = DateTimeField()
    
    checkout_request_id = StringField()

    meta = {
        "collection": "payments",

        "indexes": [
            "student_id",
            "property_id",
            "checkout_request_id",
            "merchant_request_id",
            "-created_at"
        ]
    }
from django.core.management.base import BaseCommand
from datetime import datetime

from payments.models import Payment


class Command(BaseCommand):

    help = "Insert a test payment"

    def handle(self, *args, **kwargs):

        payment = Payment(
            transaction_id="RHG-TEST-00001",

            student_id="STUDENT-00001",

            property_id="RGU-00001",

            amount=100,

            currency="KES",

            payment_method="mpesa",

            status="successful",

            mpesa_reference="TEST-MPESA-001",

            created_at=datetime.now()
        )

        payment.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Payment inserted successfully!"
            )
        )
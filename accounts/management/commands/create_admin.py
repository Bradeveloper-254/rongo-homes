from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from accounts.models import User


class Command(BaseCommand):

    help = "Create a Rongo Homes admin account"

    def handle(self, *args, **options):

        email = "admin@rongohomes.com"

        existing_admin = User.objects(
            email=email
        ).first()

        if existing_admin:

            self.stdout.write(
                self.style.WARNING(
                    "Admin account already exists."
                )
            )

            return

        admin = User(

            full_name="Rongo Homes Administrator",

            email=email,

            phone="0700000000",

            password=make_password(
                "AdminPassword123"
            ),

            role="admin",

            status="active",

            is_verified=True
        )

        admin.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Admin account created successfully."
            )
        )
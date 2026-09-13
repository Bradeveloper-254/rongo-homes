from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from datetime import datetime

from accounts.models import User


class Command(BaseCommand):

    help = "Insert sample users"

    def handle(self, *args, **kwargs):

        student = User(
            full_name="Brian Otieno",
            email="student@example.com",
            phone="0700000000",
            password=make_password("student123"),  # Hashed password
            role="student",
            status="active",
            is_active=True,
            created_at=datetime.now()
        )
        student.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Student inserted successfully!"
            )
        )
        
        owner = User(
            full_name="John Ochieng",
            email="owner@example.com",
            phone="0711111111",
            password=make_password("owner123"),  # Hashed password
            role="owner",
            status="active",
            is_active=True,
            created_at=datetime.now()
        )
        owner.save()
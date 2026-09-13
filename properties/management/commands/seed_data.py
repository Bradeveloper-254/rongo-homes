from django.core.management.base import BaseCommand
from datetime import datetime

from properties.models import Property, Location, Room, Photo


from django.core.management.base import BaseCommand
from datetime import datetime

from accounts.models import User
from properties.models import (
    Property,
    Location,
    Room,
    Photo,
)
from payments.models import Payment
from reports.models import Report
from reviews.models import Review
from notifications.models import Notification


class Command(BaseCommand):

    help = "Populate the development database with sample Rongo Homes data"

    def handle(self, *args, **kwargs):

        self.stdout.write("Starting seed process...")

        # --------------------------------------------------
        # 1. CREATE STUDENT
        # --------------------------------------------------

        student = User.objects(
            email="student@example.com"
        ).first()

        if not student:
            student = User(
                full_name="Brian Otieno",
                email="student@example.com",
                phone="0700000000",
                password="TEST_PASSWORD",
                role="student",
                is_active=True,
                created_at=datetime.now()
            )

            student.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Student created."
                )
            )
        else:
            self.stdout.write(
                "Student already exists."
            )

        # --------------------------------------------------
        # 2. CREATE OWNER
        # --------------------------------------------------

        owner = User.objects(
            email="owner@example.com"
        ).first()

        if not owner:

            owner = User(
                full_name="John Ochieng",
                email="owner@example.com",
                phone="0711111111",
                password="TEST_PASSWORD",
                role="owner",
                is_active=True,
                created_at=datetime.now()
            )

            owner.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Owner created."
                )
            )

        else:
            self.stdout.write(
                "Owner already exists."
            )

        # --------------------------------------------------
        # 3. CREATE PROPERTY
        # --------------------------------------------------

        property = Property.objects(
            property_id="RGU-00001"
        ).first()

        if not property:

            property = Property(
                property_id="RGU-00001",

                owner_id=str(owner.id),

                name="Green View Hostel",

                description=(
                    "Affordable student accommodation "
                    "near Rongo University."
                ),

                location=Location(
                    area="Rongo Town",
                    landmark="Near Rongo University",
                    latitude=-0.78,
                    longitude=34.59
                ),

                distance_from_university=1.2,

                monthly_price=4500,

                semester_price=18000,

                amenities=[
                    "wifi",
                    "water",
                    "electricity",
                    "security",
                    "study_table"
                ],

                photos=[
                    Photo(
                        url="green-view-exterior.jpg",
                        caption="Hostel exterior"
                    ),
                    Photo(
                        url="green-view-room.jpg",
                        caption="Student room"
                    )
                ],

                rooms=[
                    Room(
                        room_number="01",
                        room_type="single",
                        price=4500,
                        status="occupied"
                    ),
                    Room(
                        room_number="02",
                        room_type="single",
                        price=4500,
                        status="vacant"
                    ),
                    Room(
                        room_number="03",
                        room_type="single",
                        price=4500,
                        status="vacant"
                    )
                ],

                approval_status="approved",

                status="active",

                created_at=datetime.now(),

                updated_at=datetime.now()
            )

            property.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Property RGU-00001 created."
                )
            )

        else:

            self.stdout.write(
                "Property RGU-00001 already exists."
            )

        # --------------------------------------------------
        # 4. CREATE PAYMENT
        # --------------------------------------------------

        payment = Payment.objects(
            transaction_id="RHG-TEST-00001"
        ).first()

        if not payment:

            payment = Payment(
                transaction_id="RHG-TEST-00001",

                student_id=str(student.id),

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
                    "Test payment created."
                )
            )

        else:

            self.stdout.write(
                "Test payment already exists."
            )

        # --------------------------------------------------
        # 5. CREATE REPORT
        # --------------------------------------------------

        report = Report.objects(
            student_id=str(student.id),
            property_id="RGU-00001"
        ).first()

        if not report:

            report = Report(
                student_id=str(student.id),

                property_id="RGU-00001",

                reason="no_vacancy",

                description=(
                    "Test report for development."
                ),

                status="pending",

                created_at=datetime.now()
            )

            report.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Test report created."
                )
            )

        else:

            self.stdout.write(
                "Test report already exists."
            )

        # --------------------------------------------------
        # 6. CREATE REVIEW
        # --------------------------------------------------

        review = Review.objects(
            student_id=str(student.id),
            property_id="RGU-00001"
        ).first()

        if not review:

            review = Review(
                student_id=str(student.id),

                property_id="RGU-00001",

                rating=4,

                comment=(
                    "The property matched the listing."
                ),

                created_at=datetime.now()
            )

            review.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Test review created."
                )
            )

        else:

            self.stdout.write(
                "Test review already exists."
            )

        # --------------------------------------------------
        # 7. CREATE NOTIFICATION
        # --------------------------------------------------

        notification = Notification.objects(
            user_id=str(student.id),
            title="Payment successful"
        ).first()

        if not notification:

            notification = Notification(

                user_id=str(student.id),

                title="Payment successful",

                message=(
                    "Your contact for RGU-00001 "
                    "has been unlocked."
                ),

                notification_type="payment",

                is_read=False,

                created_at=datetime.now()
            )

            notification.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Test notification created."
                )
            )

        else:

            self.stdout.write(
                "Test notification already exists."
            )

        # --------------------------------------------------
        # FINISHED
        # --------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "RONGO HOMES SEED COMPLETE!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )
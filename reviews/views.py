from django.shortcuts import render

# Create your views here.
from datetime import datetime
from accounts.models import User
from django.shortcuts import (
    render,
    redirect
)
from notifications.utils import create_notification
from django.contrib import messages

from .models import Review
from .forms import ReviewForm

from properties.models import Property
from payments.models import Payment


def add_review(request, property_id):

    # Only students can review
    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

    # Find property
    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:student_home"
        )

     

    # Prevent duplicate reviews
    existing_review = Review.objects(
        student_id=student_id,
        property_id=property_id
    ).first()

    if existing_review:

        messages.info(
            request,
            "You have already reviewed this property."
        )

        return redirect(
            "properties:property_detail",
            property_id=property_id
        )

    if request.method == "POST":

        form = ReviewForm(
            request.POST
        )

        if form.is_valid():

            Review(
                student_id=student_id,
                property_id=property_id,
                rating=int(
                    form.cleaned_data["rating"]
                ),
                comment=form.cleaned_data[
                    "comment"
                ],
                status="pending",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            review = Review(
                student_id=student_id,

                property_id=property_id,

                rating=int(
                    form.cleaned_data["rating"]
                ),

                comment=form.cleaned_data[
                    "comment"
                ],

                status="pending",

                created_at=datetime.now(),

                updated_at=datetime.now()
            )

            review.save()


            # Notify all active admins about the new review
            admin_users = User.objects(
                role="admin",
                status="active"
            )

            for admin in admin_users:

                create_notification(
                    user_id=str(admin.id),
                    recipient_id=str(admin.id),
                    recipient_role="admin",
                    notification_type="review_submitted",
                    title="New Review Submitted",
                    message=(
                        f"A student has submitted a "
                        f"{review.rating}-star review for "
                        f"property #{property_id}. "
                        "The review is awaiting approval."
                    ),
                    related_id=str(property_id),
                )
            


            messages.success(
                request,
                "Your review has been submitted and is awaiting approval."
            )

            return redirect(
                "properties:property_detail",
                property_id=property_id
            )

    else:

        form = ReviewForm()

    return render(
        request,
        "reviews/add_review.html",
        {
            "property": property_obj,
            "form": form
        }
    )
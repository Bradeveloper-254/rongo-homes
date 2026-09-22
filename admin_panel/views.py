import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from mongoengine.queryset.visitor import Q

from accounts.models import User
from accounts.decorators import admin_required
from notifications.models import Notification
from notifications.utils import create_notification
from payments.models import Payment
from properties.models import Property
from reports.models import Report
from reviews.models import Review
import os

from django.conf import settings
from django.http import FileResponse, Http404, request
private_document_storage = FileSystemStorage(
    location=settings.PRIVATE_MEDIA_ROOT
)
# ============================================================
# ADMIN DASHBOARD
# ============================================================

@admin_required
def dashboard(request):

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    total_students = User.objects(
        role="student"
    ).count()

    total_owners = User.objects(
        role="owner"
    ).count()

    pending_owners = User.objects(
        role="owner",
        status="pending"
    ).count()

    active_owners = User.objects(
        role="owner",
        status="active"
    ).count()

    suspended_users = User.objects(
        status="suspended"
    ).count()

    # --------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------

    total_properties = Property.objects.count()

    pending_properties = Property.objects(
        approval_status="pending"
    ).count()

    approved_properties = Property.objects(
        approval_status="approved"
    ).count()

    active_properties = Property.objects(
        status="active"
    ).count()

    # --------------------------------------------------------
    # REPORTS
    # --------------------------------------------------------

    total_reports = Report.objects.count()

    pending_reports = Report.objects(
        status="pending"
    ).count()

    resolved_reports = Report.objects(
        status="resolved"
    ).count()

    rejected_reports = Report.objects(
        status="rejected"
    ).count()

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    total_payments = Payment.objects.count()

    successful_payments = Payment.objects(
        status="successful"
    ).count()

    pending_payments = Payment.objects(
        status="pending"
    ).count()

    successful_payment_records = Payment.objects(
        status="successful"
    )

    total_revenue = sum(
        (payment.amount or 0)
        for payment in successful_payment_records
    )

    # --------------------------------------------------------
    # REVIEWS
    # --------------------------------------------------------

    pending_reviews_count = Review.objects(
        status="pending"
    ).count()

    approved_reviews_count = Review.objects(
        status="approved"
    ).count()

    rejected_reviews_count = Review.objects(
        status="rejected"
    ).count()

    # --------------------------------------------------------
    # PENDING OWNERS
    # --------------------------------------------------------

    pending_owner_list = User.objects(
        role="owner",
        status="pending"
    ).order_by(
        "-created_at"
    )

    # --------------------------------------------------------
    # PENDING PROPERTIES
    # --------------------------------------------------------

    pending_property_list = Property.objects(
        approval_status="pending"
    ).order_by(
        "-created_at"
    )

    # --------------------------------------------------------
    # PENDING REPORTS
    # --------------------------------------------------------

    pending_report_list = Report.objects(
        status="pending"
    ).order_by(
        "-created_at"
    )
    
    # --------------------------------------------------------
    # ADMIN NOTIFICATIONS
    # --------------------------------------------------------

    admin_id = str(
        request.session.get("user_id")
    )

    admin_unread_notifications = Notification.objects(
        recipient_id=admin_id,
        recipient_role="admin",
        is_read=False
    ).count()



    # --------------------------------------------------------
    # RENDER DASHBOARD
    # --------------------------------------------------------

    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "total_students": total_students,
            "total_owners": total_owners,
            "pending_owners": pending_owners,
            "active_owners": active_owners,
            "suspended_users": suspended_users,

            "total_properties": total_properties,
            "pending_properties": pending_properties,
            "approved_properties": approved_properties,
            "active_properties": active_properties,

            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "resolved_reports": resolved_reports,
            "rejected_reports": rejected_reports,

            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "pending_payments": pending_payments,
            "total_revenue": total_revenue,

            "pending_reviews_count": pending_reviews_count,
            "approved_reviews_count": approved_reviews_count,
            "rejected_reviews_count": rejected_reviews_count,

            "pending_owner_list": pending_owner_list,
            "pending_property_list": pending_property_list,
            "pending_report_list": pending_report_list,
            "admin_unread_notifications": admin_unread_notifications,
        }
    )


# ============================================================
# OWNER MANAGEMENT
# ============================================================

@admin_required
def owners(request):

    search_query = request.GET.get(
        "search",
        ""
    ).strip()

    if search_query:

        owner_list = User.objects(
            Q(role="owner") &
            (
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        ).order_by(
            "-created_at"
        )

    else:

        owner_list = User.objects(
            role="owner"
        ).order_by(
            "-created_at"
        )

    return render(
        request,
        "admin_panel/owners.html",
        {
            "owners": owner_list,
            "search_query": search_query,
        }
    )


@admin_required
def approve_owner(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:dashboard")

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner account not found."
        )

        return redirect("admin_panel:owners")

    owner.status = "active"
    owner.is_active = True
    owner.is_verified = True
    owner.updated_at = datetime.datetime.now()

    owner.save()

    create_notification(
        user_id=str(owner.id),
        recipient_id=str(owner.id),
        recipient_role="owner",
        notification_type="owner_approved",
        title="Owner Account Approved",
        message=(
            "Your Rongo Homes owner account has been approved. "
            "You can now manage your properties."
        ),
        related_id=str(owner.id),
    )

    messages.success(
        request,
        f"{owner.full_name}'s owner account has been approved."
    )

    return redirect("admin_panel:owners")


@admin_required
def reject_owner(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:dashboard")

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner account not found."
        )

        return redirect("admin_panel:owners")

    owner.status = "rejected"
    owner.is_active = False
    owner.is_verified = False
    owner.updated_at = datetime.datetime.now()

    owner.save()

    create_notification(
        user_id=str(owner.id),
        recipient_id=str(owner.id),
        recipient_role="owner",
        notification_type="owner_rejected",
        title="Owner Application Rejected",
        message=(
            "Your Rongo Homes owner application "
            "has been rejected by the administrator."
        ),
        related_id=str(owner.id),
    )

    messages.warning(
        request,
        f"{owner.full_name}'s application has been rejected."
    )

    return redirect("admin_panel:owners")


@admin_required
def suspend_owner(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:owners")

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner account not found."
        )

        return redirect("admin_panel:owners")

    owner.status = "suspended"
    owner.is_active = False
    owner.updated_at = datetime.datetime.now()

    owner.save()

    create_notification(
        user_id=str(owner.id),
        recipient_id=str(owner.id),
        recipient_role="owner",
        notification_type="owner_suspended",
        title="Owner Account Suspended",
        message=(
            "Your Rongo Homes owner account has been suspended."
        ),
        related_id=str(owner.id),
    )

    messages.warning(
        request,
        f"{owner.full_name}'s account has been suspended."
    )

    return redirect("admin_panel:owners")


@admin_required
def activate_owner(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:owners")

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner account not found."
        )

        return redirect("admin_panel:owners")

    owner.status = "active"
    owner.is_active = True
    owner.is_verified = True
    owner.updated_at = datetime.datetime.now()

    owner.save()

    # IMPORTANT:
    # "owner_activated" is NOT currently allowed by the
    # Notification model. Use the existing "owner_approved"
    # notification type instead.
    create_notification(
        user_id=str(owner.id),
        recipient_id=str(owner.id),
        recipient_role="owner",
        notification_type="owner_approved",
        title="Owner Account Reactivated",
        message=(
            "Your Rongo Homes owner account has been reactivated. "
            "You can now manage your properties."
        ),
        related_id=str(owner.id),
    )

    messages.success(
        request,
        f"{owner.full_name}'s owner account has been reactivated."
    )

    return redirect("admin_panel:owners")



@admin_required
def owner_detail(request, user_id):

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:
        messages.error(
            request,
            "Owner account not found."
        )
        return redirect("admin_panel:owners")

    # Find all properties belonging to this owner
    owner_properties = Property.objects(
        owner_id=str(owner.id)
    ).order_by("-created_at")

    return render(
        request,
        "admin_panel/owner_detail.html",
        {
            "owner": owner,
            "owner_properties": owner_properties,
        }
    )


@admin_required
def view_owner_document(request, user_id, document_type):

    allowed_documents = {
        "id": "id_document",
        "ownership": "ownership_document",
        "additional": "additional_document",
    }

    field_name = allowed_documents.get(document_type)

    if not field_name:
        raise Http404("Invalid document type.")

    owner = User.objects(
        id=user_id,
        role="owner"
    ).first()

    if not owner:
        raise Http404("Owner account not found.")

    document_path = getattr(owner, field_name, None)

    if not document_path:
        raise Http404("Document not found.")

    private_root = os.path.abspath(
        settings.PRIVATE_MEDIA_ROOT
    )

    file_path = os.path.abspath(
        os.path.join(private_root, document_path)
    )

    # Prevent path traversal outside private_media/
    if os.path.commonpath(
        [private_root, file_path]
    ) != private_root:
        raise Http404("Invalid document path.")

    if not os.path.isfile(file_path):
        raise Http404("Document file not found.")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=False,
        filename=os.path.basename(file_path),
    )


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

@admin_required
def students(request):

    search_query = request.GET.get(
        "search",
        ""
    ).strip()

    if search_query:

        student_list = User.objects(
            Q(role="student") &
            (
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        ).order_by(
            "-created_at"
        )

    else:

        student_list = User.objects(
            role="student"
        ).order_by(
            "-created_at"
        )

    return render(
        request,
        "admin_panel/students.html",
        {
            "students": student_list,
            "search_query": search_query,
        }
    )


@admin_required
def suspend_student(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:students")

    student = User.objects(
        id=user_id,
        role="student"
    ).first()

    if not student:

        messages.error(
            request,
            "Student account not found."
        )

        return redirect("admin_panel:students")

    student.status = "suspended"
    student.is_active = False
    student.updated_at = datetime.datetime.now()

    student.save()

    messages.success(
        request,
        f"{student.full_name} has been suspended."
    )

    return redirect("admin_panel:students")


@admin_required
def activate_student(request, user_id):

    if request.method != "POST":
        return redirect("admin_panel:students")

    student = User.objects(
        id=user_id,
        role="student"
    ).first()

    if not student:

        messages.error(
            request,
            "Student account not found."
        )

        return redirect("admin_panel:students")

    student.status = "active"
    student.is_active = True
    student.updated_at = datetime.datetime.now()

    student.save()

    messages.success(
        request,
        f"{student.full_name} has been reactivated."
    )

    return redirect("admin_panel:students")


# ============================================================
# PROPERTY MANAGEMENT
# ============================================================

@admin_required
def properties(request):

    search_query = request.GET.get(
        "search",
        ""
    ).strip()

    if search_query:

        property_list = Property.objects(
            name__icontains=search_query
        ).order_by(
            "-created_at"
        )

    else:

        property_list = Property.objects.order_by(
            "-created_at"
        )

    return render(
        request,
        "admin_panel/properties.html",
        {
            "properties": property_list,
            "search_query": search_query,
        }
    )


@admin_required
def approve_property(request, property_id):

    if request.method != "POST":
        return redirect("admin_panel:properties")

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect("admin_panel:properties")

    property_obj.approval_status = "approved"
    property_obj.status = "active"

    if hasattr(property_obj, "updated_at"):
        property_obj.updated_at = datetime.datetime.now()

    property_obj.save()

    owner_id = getattr(
        property_obj,
        "owner_id",
        None
    )

    if owner_id:

        create_notification(
            user_id=str(owner_id),
            recipient_id=str(owner_id),
            recipient_role="owner",
            notification_type="property_approved",
            title="Property Approved",
            message=(
                f"Your property "
                f"'{getattr(property_obj, 'name', 'property')}' "
                "has been approved by the administrator."
            ),
            related_id=str(property_obj.property_id),
        )

    messages.success(
        request,
        "Property has been approved successfully."
    )

    return redirect("admin_panel:properties")


@admin_required
def reject_property(request, property_id):

    if request.method != "POST":
        return redirect("admin_panel:properties")

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect("admin_panel:properties")

    property_obj.approval_status = "rejected"
    property_obj.status = "inactive"

    if hasattr(property_obj, "updated_at"):
        property_obj.updated_at = datetime.datetime.now()

    property_obj.save()

    owner_id = getattr(
        property_obj,
        "owner_id",
        None
    )

    if owner_id:

        create_notification(
            user_id=str(owner_id),
            recipient_id=str(owner_id),
            recipient_role="owner",
            notification_type="property_rejected",
            title="Property Rejected",
            message=(
                f"Your property "
                f"'{getattr(property_obj, 'name', 'property')}' "
                "has been rejected by the administrator."
            ),
            related_id=str(property_obj.property_id),
        )

    messages.warning(
        request,
        "Property has been rejected."
    )

    return redirect("admin_panel:properties")


@admin_required
def suspend_property(request, property_id):

    if request.method != "POST":
        return redirect("admin_panel:properties")

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect("admin_panel:properties")

    property_obj.status = "suspended"

    if hasattr(property_obj, "updated_at"):
        property_obj.updated_at = datetime.datetime.now()

    property_obj.save()

    owner_id = getattr(
        property_obj,
        "owner_id",
        None
    )

    if owner_id:

        create_notification(
            user_id=str(owner_id),
            recipient_id=str(owner_id),
            recipient_role="owner",
            notification_type="property_suspended",
            title="Property Suspended",
            message=(
                f"Your property "
                f"'{getattr(property_obj, 'name', 'property')}' "
                "has been suspended by the administrator."
            ),
            related_id=str(property_obj.property_id),
        )

    messages.warning(
        request,
        "Property has been suspended."
    )

    return redirect("admin_panel:properties")


@admin_required
def activate_property(request, property_id):

    if request.method != "POST":
        return redirect("admin_panel:properties")

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect("admin_panel:properties")

    if property_obj.approval_status != "approved":

        messages.error(
            request,
            "This property must be approved before it can be activated."
        )

        return redirect("admin_panel:properties")

    property_obj.status = "active"

    if hasattr(property_obj, "updated_at"):
        property_obj.updated_at = datetime.datetime.now()

    property_obj.save()

    owner_id = getattr(
        property_obj,
        "owner_id",
        None
    )

    if owner_id:

        create_notification(
            user_id=str(owner_id),
            recipient_id=str(owner_id),
            recipient_role="owner",
            notification_type="property_activated",
            title="Property Activated",
            message=(
                f"Your property "
                f"'{getattr(property_obj, 'name', 'property')}' "
                "has been activated and is now available."
            ),
            related_id=str(property_obj.property_id),
        )

    messages.success(
        request,
        "Property has been activated successfully."
    )

    return redirect("admin_panel:properties")


# ============================================================
# PROPERTY DETAILS
# ============================================================

@admin_required
def property_detail(request, property_id):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect("admin_panel:properties")

    return render(
        request,
        "admin_panel/property_detail.html",
        {
            "property": property_obj
        }
    )



@admin_required
def view_property(request, property_id):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "admin_panel:properties"
        )

    return render(
        request,
        "admin_panel/property_detail.html",
        {
            "property": property_obj,
        }
    )




# ============================================================
# REPORT MANAGEMENT
# ============================================================

@admin_required
def reports(request):

    report_list = Report.objects.order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_panel/reports.html",
        {
            "reports": report_list
        }
    )


@admin_required
def resolve_report(request, report_id):

    if request.method != "POST":
        return redirect("admin_panel:reports")

    report = Report.objects(
        id=report_id
    ).first()

    if not report:

        messages.error(
            request,
            "Report not found."
        )

        return redirect("admin_panel:reports")

    report.status = "resolved"
    report.save()

    messages.success(
        request,
        "Report has been marked as resolved."
    )

    return redirect("admin_panel:reports")


@admin_required
def dismiss_report(request, report_id):

    if request.method != "POST":
        return redirect("admin_panel:reports")

    report = Report.objects(
        id=report_id
    ).first()

    if not report:

        messages.error(
            request,
            "Report not found."
        )

        return redirect("admin_panel:reports")

    report.status = "rejected"
    report.save()

    messages.success(
        request,
        "Report has been dismissed."
    )

    return redirect("admin_panel:reports")


@admin_required
def reject_report(request, report_id):

    if request.method != "POST":
        return redirect("admin_panel:reports")

    report = Report.objects(
        id=report_id
    ).first()

    if not report:

        messages.error(
            request,
            "Report not found."
        )

        return redirect("admin_panel:reports")

    report.status = "rejected"
    report.save()

    messages.success(
        request,
        "Report has been rejected."
    )

    return redirect("admin_panel:reports")


# ============================================================
# PAYMENT MANAGEMENT
# ============================================================

@admin_required
def payments(request):

    payment_list = Payment.objects.order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_panel/payments.html",
        {
            "payments": payment_list
        }
    )


# ============================================================
# REVIEW MANAGEMENT
# ============================================================

@admin_required
def reviews(request):

    pending_reviews = Review.objects(
        status="pending"
    ).order_by(
        "-created_at"
    )

    approved_reviews = Review.objects(
        status="approved"
    ).order_by(
        "-created_at"
    )

    rejected_reviews = Review.objects(
        status="rejected"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "admin_panel/reviews.html",
        {
            "pending_reviews": pending_reviews,
            "approved_reviews": approved_reviews,
            "rejected_reviews": rejected_reviews,
        }
    )


@admin_required
def approve_review(request, review_id):

    if request.method != "POST":
        return redirect("admin_panel:reviews")

    review = Review.objects(
        id=review_id
    ).first()

    if not review:

        messages.error(
            request,
            "Review not found."
        )

        return redirect("admin_panel:reviews")

    review.status = "approved"
    review.updated_at = datetime.datetime.now()

    review.save()

    create_notification(
        recipient_id=str(review.student_id),
        user_id=str(review.student_id),
        recipient_role="student",
        notification_type="review_approved",
        title="Review Approved",
        message=(
            "Your review has been approved "
            "and is now visible to other students."
        ),
        related_id=str(review.id),
    )

    messages.success(
        request,
        "Review approved successfully."
    )

    return redirect("admin_panel:reviews")


@admin_required
def reject_review(request, review_id):

    if request.method != "POST":
        return redirect("admin_panel:reviews")

    review = Review.objects(
        id=review_id
    ).first()

    if not review:

        messages.error(
            request,
            "Review not found."
        )

        return redirect("admin_panel:reviews")

    review.status = "rejected"
    review.updated_at = datetime.datetime.now()

    review.save()

    create_notification(
        recipient_id=str(review.student_id),
        user_id=str(review.student_id),
        recipient_role="student",
        notification_type="review_rejected",
        title="Review Rejected",
        message=(
            "Your review was reviewed by an administrator "
            "and was not approved for publication."
        ),
        related_id=str(review.id),
    )

    messages.warning(
        request,
        "Review rejected successfully."
    )

    return redirect("admin_panel:reviews")


# ============================================================
# ADMIN ANNOUNCEMENTS
# ============================================================

@admin_required
def send_announcement(request):

    if request.method == "POST":

        recipient_role = request.POST.get(
            "recipient_role"
        )

        title = request.POST.get(
            "title",
            ""
        ).strip()

        message = request.POST.get(
            "message",
            ""
        ).strip()
        if len(title) > 200:
            messages.error(
                request,
                "Announcement title is too long."
            )
            return redirect("admin_panel:send_announcement")

        if len(message) > 5000:
            messages.error(
                request,
                "Announcement message is too long."
            )
            return redirect("admin_panel:send_announcement")


            
        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if recipient_role not in [
            "student",
            "owner"
        ]:

            messages.error(
                request,
                "Please select a valid recipient group."
            )

            return redirect(
                "admin_panel:send_announcement"
            )

        if not title:

            messages.error(
                request,
                "Announcement title is required."
            )

            return redirect(
                "admin_panel:send_announcement"
            )

        if not message:

            messages.error(
                request,
                "Announcement message is required."
            )

            return redirect(
                "admin_panel:send_announcement"
            )

        # ----------------------------------------------------
        # GET RECIPIENTS
        # ----------------------------------------------------

        users = User.objects(
            role=recipient_role,
            is_active=True
        )

        sent_count = 0

        # ----------------------------------------------------
        # CREATE NOTIFICATION FOR EACH USER
        # ----------------------------------------------------

        for user in users:

            Notification(
                user_id=str(user.id),
                recipient_id=str(user.id),
                recipient_role=recipient_role,
                notification_type="announcement",
                title=title,
                message=message,
                link="",
                related_id=None,
                is_read=False,
                created_at=datetime.datetime.utcnow()
            ).save()

            sent_count += 1

        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        if recipient_role == "student":
            group_name = "students"
        else:
            group_name = "owners"

        messages.success(
            request,
            f"Announcement sent successfully to "
            f"{sent_count} {group_name}."
        )

        return redirect(
            "admin_panel:send_announcement"
        )

    # --------------------------------------------------------
    # DISPLAY FORM
    # --------------------------------------------------------

    return render(
        request,
        "admin_panel/send_announcement.html"
    )


@admin_required
def notifications(request):

    admin_id = str(request.session.get("user_id"))

    notification_list = Notification.objects(
        recipient_id=admin_id,
        recipient_role="admin"
    ).order_by("-created_at")

    unread_count = Notification.objects(
        recipient_id=admin_id,
        recipient_role="admin",
        is_read=False
    ).count()

    return render(
        request,
        "admin_panel/notifications.html",
        {
            "notifications": notification_list,
            "unread_count": unread_count,
        }
    )


@admin_required
def mark_notification_read(request, notification_id):

    if request.method != "POST":
        return redirect("admin_panel:notifications")

    admin_id = str(request.session.get("user_id"))

    notification = Notification.objects(
        id=notification_id,
        recipient_id=admin_id,
        recipient_role="admin"
    ).first()

    if notification:

        notification.is_read = True
        notification.save()

    return redirect("admin_panel:notifications")


@admin_required
def mark_all_notifications_read(request):

    if request.method != "POST":
        return redirect("admin_panel:notifications")

    admin_id = str(request.session.get("user_id"))

    Notification.objects(
        recipient_id=admin_id,
        recipient_role="admin",
        is_read=False
    ).update(
        set__is_read=True
    )

    messages.success(
        request,
        "All notifications have been marked as read."
    )

    return redirect("admin_panel:notifications")


from datetime import datetime, timedelta
import email
import os
import secrets
import uuid
from django.core.serializers import python
from notifications.utils import create_notification
from accounts.models import User
from django.contrib import messages
from django.contrib.auth.hashers import (
    make_password,
    check_password
)
from django.core.mail import send_mail
from django.shortcuts import (
    render,
    redirect
)
from django.utils import timezone

from properties.models import Property
from payments.models import Payment
from reports.models import Report

from django.core.files.storage import default_storage

from .decorators import admin_required
from .decorators import login_required
from .forms import RegistrationForm
from .models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
id_document = None
ownership_document = None
additional_document = None
private_document_storage = FileSystemStorage( location=settings.PRIVATE_MEDIA_ROOT )

# ==========================================
# REGISTER
# ==========================================



def register(request):

    # If user is already logged in, redirect to appropriate dashboard
    if request.session.get("user_id"):
        role = request.session.get("role")

        if role == "student":
            return redirect("properties:student_home")

        elif role == "owner":
            return redirect("owner_dashboard:dashboard")

        elif role == "admin":
            return redirect("accounts:admin_dashboard")

    if request.method == "POST":

        form = RegistrationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            email = form.cleaned_data["email"].lower().strip()

            existing_user = User.objects(
                email=email
            ).first()

            if existing_user:

                form.add_error(
                    "email",
                    "An account with this email already exists."
                )

            else:

                role = form.cleaned_data["role"]

                # Students become active immediately.
                # Owners/caretakers must wait for approval.
                if role == "student":
                    status = "active"
                else:
                    status = "pending"

                # Save uploaded documents
                id_document_path = None
                ownership_document_path = None
                additional_document_path = None

                if role == "owner":

                    id_document = form.cleaned_data.get(
                        "id_document"
                    )

                    ownership_document = form.cleaned_data.get(
                        "ownership_document"
                    )

                    additional_document = form.cleaned_data.get(
                        "additional_document"
                    )

                    if id_document:
                            id_document_path = private_document_storage.save(
                                f"owner_documents/{email}/id/{id_document.name}",
                                id_document
                            )

                    if ownership_document:
                        ownership_document_path = private_document_storage.save(
                            f"owner_documents/{email}/ownership/{ownership_document.name}",
                            ownership_document
                        )

                    if additional_document:
                        additional_document_path = private_document_storage.save(
                            f"owner_documents/{email}/additional/{additional_document.name}",
                            additional_document
                        )

                user = User(
                    full_name=form.cleaned_data[
                        "full_name"
                    ],

                    email=email,

                    phone=form.cleaned_data[
                        "phone"
                    ],

                    password=make_password(
                        form.cleaned_data[
                            "password"
                        ]
                    ),

                    role=role,

                    status=status,

                    is_verified=False,

                    is_active=True if role == "student" else False,

                    id_document=id_document_path,

                    ownership_document=ownership_document_path,

                    additional_document=additional_document_path,

                    created_at=datetime.now(),

                    updated_at=datetime.now()
                )

                user.save()

                # Notify active administrators about new owner applications
                if role == "owner":

                    admin_users = User.objects(
                        role="admin",
                        status="active"
                    )

                    for admin in admin_users:

                        create_notification(
                            user_id=str(admin.id),
                            recipient_id=str(admin.id),
                            recipient_role="admin",
                            notification_type="owner_registered",
                            title="New Owner Application",
                            message=(
                                f"{user.full_name} has submitted a new owner "
                                f"application using {user.email}."
                            ),
                            related_id=str(user.id),
                        )

                    messages.success(
                        request,
                        "Your Property Owner/Caretaker "
                        "account has been created and is "
                        "waiting for administrator approval."
                    )

                else:

                    messages.success(
                        request,
                        "Your student account has been created. "
                        "You can now log in."
                    )

                return redirect(
                    "accounts:login"
                )

    else:

        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )



# ==========================================
# LOGIN
# ==========================================

def login_view(request):
    # If user is already logged in, redirect to appropriate dashboard
    if request.session.get("user_id"):
        role = request.session.get("role")
        if role == "student":
            return redirect("properties:student_home")
        elif role == "owner":
            return redirect("owner_dashboard:dashboard")
        elif role == "admin":
            return redirect("accounts:admin_dashboard")

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).lower().strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = User.objects(
            email=email
        ).first()

        print("LOGIN EMAIL:", repr(email))
        print("USER FOUND:", user is not None)

        if user:
            print("DB EMAIL:", repr(user.email))
            print("STATUS:", user.status)
            print("ROLE:", user.role)
            print("PASSWORD CHECK:", check_password(password, user.password))

        if not user:

            messages.error(
                request,
                "Invalid email or password."
            )

            return render(
                request,
                "accounts/login.html"
            )

        if not check_password(
            password,
            user.password
        ):

            messages.error(
                request,
                "Invalid email or password."
            )

            return render(
                request,
                "accounts/login.html"
            )

        if user.status == "pending":

            messages.warning(
                request,
                "Your account is waiting for administrator approval."
            )

            return render(
                request,
                "accounts/login.html"
            )

        if user.status == "rejected":

            messages.error(
                request,
                "Your account application was rejected."
            )

            return render(
                request,
                "accounts/login.html"
            )

        if user.status == "suspended":

            messages.error(
                request,
                "Your account has been suspended."
            )

            return render(
                request,
                "accounts/login.html"
            )

        # Successful login - Save session explicitly
        request.session["user_id"] = str(user.id)
        request.session["role"] = user.role
        request.session["email"] = user.email
        request.session["full_name"] = user.full_name
        
        # Force session to save before redirect
        request.session.modified = True
        request.session.save()

        if user.role == "student":
            return redirect("properties:student_home")

        elif user.role == "owner":
            return redirect("owner_dashboard:dashboard")

        elif user.role == "admin":
            return redirect("accounts:admin_dashboard")

    return render(
        request,
        "accounts/login.html"
    )
    


# ==========================================
# FORGOT PASSWORD
# ==========================================

def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).lower().strip()

        user = User.objects(
            email=email
        ).first()

        # Always show the same response whether
        # the email exists or not.
        if user:

            token = secrets.token_urlsafe(32)

            user.password_reset_token = token

            user.password_reset_expires = (
                timezone.now()
                + timedelta(minutes=30)
            )

            user.save()

            reset_url = request.build_absolute_uri(
                f"/accounts/reset-password/{token}/"
            )

            send_mail(
                subject="Rongo Homes - Password Reset",
                message=(
                    f"Hello {user.full_name},\n\n"
                    "We received a request to reset your "
                    "Rongo Homes password.\n\n"
                    f"Reset your password using this link:\n"
                    f"{reset_url}\n\n"
                    "This link will expire in 30 minutes.\n\n"
                    "If you did not request a password reset, "
                    "you can safely ignore this email.\n\n"
                    "Rongo Homes"
                ),
                from_email="minyatabradley@gmail.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

        messages.success(
            request,
            "If an account exists with that email, "
            "a password reset link has been sent."
        )

        return redirect(
            "accounts:forgot_password"
        )

    return render(
        request,
        "accounts/forgot_password.html"
    )


# ==========================================
# RESET PASSWORD
# ==========================================


def reset_password(request, token):
    user = User.objects(password_reset_token=token).first()

    if not user:
        messages.error(
            request,
            "This password reset link is invalid or has expired."
        )
        return redirect("accounts:forgot_password")

    # MongoEngine may return the stored datetime as naive.
    # Make it timezone-aware before comparing it with timezone.now().
    expires_at = user.password_reset_expires

    if not expires_at:
        messages.error(
            request,
            "This password reset link is invalid or has expired."
        )
        return redirect("accounts:forgot_password")

    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(
            expires_at,
            timezone.get_current_timezone()
        )

    if expires_at < timezone.now():
        user.password_reset_token = None
        user.password_reset_expires = None
        user.save()

        messages.error(
            request,
            "This password reset link is invalid or has expired."
        )
        return redirect("accounts:forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(
                request,
                "accounts/reset_password.html",
                {"token": token}
            )

        if len(password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters long."
            )
            return render(
                request,
                "accounts/reset_password.html",
                {"token": token}
            )

        user.password = make_password(password)

        # Password reset token can only be used once.
        user.password_reset_token = None
        user.password_reset_expires = None

        user.updated_at = datetime.now()
        user.save()

        messages.success(
            request,
            "Your password has been changed successfully. "
            "You can now log in with your new password."
        )

        return redirect("accounts:login")

    return render(
        request,
        "accounts/reset_password.html",
        {"token": token}
    )


# ==========================================
# LOGOUT
# ==========================================
from django.views.decorators.http import require_POST

@require_POST
def logout_view(request):

    request.session.flush()

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        "accounts:login"
    )

# ==========================================
# PROFILE
# ==========================================

@login_required
def profile(request):

    user = request.current_user

    return render(
        request,
        "accounts/profile.html",
        {
            "user": user
        }
    )
    
# ==========================================
# ADMIN DASHBOARD
# ==========================================
@admin_required
def admin_dashboard(request):

    # ==============================
    # USER STATISTICS
    # ==============================

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


    # ==============================
    # PROPERTY STATISTICS
    # ==============================

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


    # ==============================
    # REPORT STATISTICS
    # ==============================

    total_reports = Report.objects.count()

    pending_reports = Report.objects(
        status="pending"
    ).count()


    # ==============================
    # PAYMENT STATISTICS
    # ==============================

    total_payments = Payment.objects.count()

    successful_payments = Payment.objects(
        status="successful"
    ).count()


    # ==============================
    # REVENUE
    # ==============================

    successful_payment_records = Payment.objects(
        status="successful"
    )

    total_revenue = sum(
        payment.amount
        for payment in successful_payment_records
    )


    # ==============================
    # PENDING OWNERS
    # ==============================

    pending_owner_list = User.objects(
        role="owner",
        status="pending"
    ).order_by(
        "-created_at"
    )


    # ==============================
    # PENDING PROPERTIES
    # ==============================

    pending_property_list = Property.objects(
        approval_status="pending"
    ).order_by(
        "-created_at"
    )


    # ==============================
    # PENDING REPORTS
    # ==============================

    pending_report_list = Report.objects(
        status="pending"
    ).order_by(
        "-created_at"
    )


    return render(
        request,
        "accounts/admin_dashboard.html",
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

            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "total_revenue": total_revenue,

            "pending_owner_list": pending_owner_list,
            "pending_property_list": pending_property_list,
            "pending_report_list": pending_report_list,
        }
    )
# ==========================================
# APPROVE OWNER
# ==========================================
@admin_required
def approve_owner(request, owner_id):

    owner = User.objects(
        id=owner_id,
        role="owner",
        status="pending"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner application could not be found."
        )

        return redirect(
            "accounts:admin_dashboard"
        )

    owner.status = "active"

    owner.is_verified = True

    owner.updated_at = datetime.now()

    owner.save()

    messages.success(
        request,
        f"{owner.full_name} has been approved successfully."
    )

    return redirect(
        "accounts:admin_dashboard"
    )
    
# ==========================================
# REJECT OWNER
# ==========================================
@admin_required
def reject_owner(request, owner_id):

    user_id = request.session.get("user_id")

    role = request.session.get("role")

    if not user_id:

        return redirect(
            "accounts:login"
        )

    if role != "admin":

        messages.error(
            request,
            "You do not have permission to perform this action."
        )

        return redirect(
            "accounts:profile"
        )

    owner = User.objects(
        id=owner_id,
        role="owner",
        status="pending"
    ).first()

    if not owner:

        messages.error(
            request,
            "Owner application could not be found."
        )

        return redirect(
            "accounts:admin_dashboard"
        )

    owner.status = "rejected"

    owner.updated_at = datetime.now()

    owner.save()

    messages.success(
        request,
        f"{owner.full_name}'s application has been rejected."
    )

    return redirect(
        "accounts:admin_dashboard"
    )


# ==========================================
# TERMS AND CONDITIONS
# ==========================================

def terms(request):

    return render(
        request,
        "accounts/terms.html"
    )


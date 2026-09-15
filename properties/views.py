import os
import uuid
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from accounts.models import User
from accounts.decorators import owner_required
from notifications.models import Notification
from notifications.utils import create_notification
from payments.models import Payment
from reports.models import Report
from reviews.models import Review
from .forms import (
    PropertyForm,
    PropertyPhotoForm,
    PropertyReportForm,
    PropertySearchForm,
    RoomForm,
)
from .models import (
    AvailabilityAlert,
    Favourite,
    Location,
    Photo,
    Property,
    Room,
    PropertyView,
)


# ============================================================
# STUDENT HOME
# ============================================================


def student_home(request):
    if request.session.get("role") != "student":
        return redirect("accounts:login")

    student_id = request.session.get("user_id")

    # ---------------------------------------------------------
    # AVAILABLE PROPERTIES
    # ---------------------------------------------------------

    properties = Property.objects(
        approval_status="approved",
        status="active"
    )

    available_properties = []

    for property_obj in properties:

        vacant_rooms = [
            room
            for room in property_obj.rooms
            if room.status == "vacant"
        ]

        if vacant_rooms:

            available_properties.append(
                {
                    "property": property_obj,
                    "vacant_rooms": vacant_rooms,
                    "cover_photo": get_cover_photo(property_obj),
                }
            )

    # ---------------------------------------------------------
    # PAYMENT HISTORY
    # ---------------------------------------------------------

    payment_history = Payment.objects(
        student_id=student_id
    ).order_by("-created_at")

    # ---------------------------------------------------------
    # UNLOCKED CONTACTS
    #
    # Only successful contact-unlock payments give access.
    # ---------------------------------------------------------

    unlocked_payments = Payment.objects(
        student_id=student_id,
        status="successful",
        payment_type="contact_unlock"
    ).order_by("-created_at")

    unlocked_contacts = []

    for payment in unlocked_payments:

        property_obj = Property.objects(
            property_id=payment.property_id
        ).first()

        if property_obj:

            unlocked_contacts.append(
                {
                    "property": property_obj,
                    "payment": payment,
                }
            )

    # ---------------------------------------------------------
    # REPORTED PROPERTIES
    # ---------------------------------------------------------

    reports = Report.objects(
        student_id=student_id
    ).order_by("-created_at")

    reported_properties = []

    for report in reports:

        property_obj = Property.objects(
            property_id=report.property_id
        ).first()

        reported_properties.append(
            {
                "report": report,
                "property": property_obj,
            }
        )

    # ---------------------------------------------------------
    # DASHBOARD COUNTS
    # ---------------------------------------------------------

    favourite_count = Favourite.objects(
        student_id=student_id
    ).count()

    payment_count = Payment.objects(
        student_id=student_id
    ).count()

    review_count = Review.objects(
        student_id=student_id
    ).count()

    report_count = Report.objects(
        student_id=student_id
    ).count()

    compare_count = len(
        request.session.get("compare_properties", [])
    )

    unread_notifications = Notification.objects(
        user_id=student_id,
        is_read=False
    ).count()
    

    # ---------------------------------------------------------
    # RENDER DASHBOARD
    # ---------------------------------------------------------
    
    # --------------------------------------------------------
    # FAVOURITES
    # --------------------------------------------------------

    favourite_count = Favourite.objects(
        student_id=student_id
    ).count()

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    payment_count = Payment.objects(
        student_id=student_id
    ).count()

    successful_payment_count = Payment.objects(
        student_id=student_id,
        status="successful"
    ).count()

    # --------------------------------------------------------
    # REVIEWS
    # --------------------------------------------------------

    review_count = Review.objects(
        student_id=student_id
    ).count()

    # --------------------------------------------------------
    # REPORTS
    # --------------------------------------------------------

    report_count = Report.objects(
        student_id=student_id
    ).count()

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    unread_notifications = Notification.objects(
        recipient_id=student_id,
        is_read=False
    ).count()

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    compare_properties = request.session.get(
        "compare_properties",
        []
    )

    compare_count = len(
        compare_properties
    )

    return render(
        request,
        "properties/student_home.html",
        {
            "properties": available_properties,

            "favourite_count": favourite_count,

            "payment_count": payment_count,

            "successful_payment_count":
                successful_payment_count,

            "review_count": review_count,

            "report_count": report_count,

            "unread_notifications":
                unread_notifications,

            "compare_count":
                compare_count,
                
              
                        "payment_history": payment_history,
                        "unlocked_contacts": unlocked_contacts,
                        "reported_properties": reported_properties,
                    }
                )
   



# ============================================================
# PROPERTY LIST
# ============================================================

def property_list(request):

    form = PropertySearchForm(
        request.GET or None
    )

    properties = Property.objects(
        approval_status="approved",
        status="active"
    )

    available_properties = []

    for property_obj in properties:

        if property_obj.vacant_room_count <= 0:
            continue

        available_properties.append(
            property_obj
        )

    # --------------------------------------------------------
    # SEARCH AND FILTERS
    # --------------------------------------------------------

    if form.is_valid():

        keyword = form.cleaned_data.get(
            "keyword"
        )

        location = form.cleaned_data.get(
            "location"
        )

        min_price = form.cleaned_data.get(
            "min_price"
        )

        max_price = form.cleaned_data.get(
            "max_price"
        )

        room_type = form.cleaned_data.get(
            "room_type"
        )

        amenities = form.cleaned_data.get(
            "amenities"
        )

        max_distance = form.cleaned_data.get(
            "max_distance"
        )

        # ----------------------------------------------------
        # KEYWORD
        # ----------------------------------------------------

        if keyword:

            keyword = keyword.lower()

            available_properties = [
                property_obj
                for property_obj in available_properties
                if (
                    keyword in (
                        property_obj.name or ""
                    ).lower()
                    or
                    keyword in (
                        property_obj.description or ""
                    ).lower()
                )
            ]

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        if location:

            location = location.lower()

            available_properties = [
                property_obj
                for property_obj in available_properties
                if (
                    property_obj.location
                    and
                    location in (
                        property_obj.location.area or ""
                    ).lower()
                )
            ]

        # ----------------------------------------------------
        # MINIMUM PRICE
        # ----------------------------------------------------

        if min_price is not None:

            available_properties = [
                property_obj
                for property_obj in available_properties
                if (
                    property_obj.monthly_price is not None
                    and
                    property_obj.monthly_price >= min_price
                )
            ]

        # ----------------------------------------------------
        # MAXIMUM PRICE
        # ----------------------------------------------------

        if max_price is not None:

            available_properties = [
                property_obj
                for property_obj in available_properties
                if (
                    property_obj.monthly_price is not None
                    and
                    property_obj.monthly_price <= max_price
                )
            ]

        # ----------------------------------------------------
        # ROOM TYPE
        # ----------------------------------------------------

        if room_type:

            room_type = room_type.lower()

            available_properties = [
                property_obj
                for property_obj in available_properties
                if any(
                    (
                        room.room_type
                        and
                        room.room_type.lower()
                        == room_type
                        and
                        room.status == "vacant"
                    )
                    for room in property_obj.rooms
                )
            ]

        # ----------------------------------------------------
        # AMENITIES
        # ----------------------------------------------------

        if amenities:

            available_properties = [
                property_obj
                for property_obj in available_properties
                if all(
                    amenity.lower()
                    in [
                        item.lower()
                        for item in (
                            property_obj.amenities or []
                        )
                    ]
                    for amenity in amenities
                )
            ]

        # ----------------------------------------------------
        # DISTANCE
        # ----------------------------------------------------

        if max_distance is not None:

            available_properties = [
                property_obj
                for property_obj in available_properties
                if (
                    property_obj.distance_from_university
                    is not None
                    and
                    property_obj.distance_from_university
                    <= max_distance
                )
            ]

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort_by = request.GET.get(
        "sort",
        "latest"
    )

    if sort_by == "price":

        # Cheapest first
        available_properties.sort(
            key=lambda property_obj: (
                property_obj.monthly_price
                if property_obj.monthly_price is not None
                else float("inf")
            )
        )

    elif sort_by == "price_high":

        # Most expensive first
        available_properties.sort(
            key=lambda property_obj: (
                property_obj.monthly_price
                if property_obj.monthly_price is not None
                else float("-inf")
            ),
            reverse=True
        )

    elif sort_by == "distance":

        # Nearest to university first
        available_properties.sort(
            key=lambda property_obj: (
                property_obj.distance_from_university
                if property_obj.distance_from_university is not None
                else float("inf")
            )
        )

    else:

        # Latest properties first
        available_properties.sort(
            key=lambda property_obj: (
                property_obj.created_at
                if property_obj.created_at is not None
                else datetime.min
            ),
            reverse=True
        )

        sort_by = "latest"

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {
        "properties": available_properties,
        "form": form,
        "sort_by": sort_by,
    }

    # --------------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------------

    return render(
        request,
        "properties/property_list.html",
        context
    )




# ============================================================
# PROPERTY DETAIL
# ============================================================

def property_detail(
    request,
    property_id
):
    property_obj = Property.objects(
        property_id=property_id,
        approval_status="approved",
        status="active"
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found."
        )
        return redirect(
            "properties:property_list"
        )
        # --------------------------------------------------------
    # PROPERTY VIEW ANALYTICS
    # --------------------------------------------------------

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    # Make sure a session exists for anonymous visitors
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Do not count property owner's own views
    is_owner = (
        role == "owner"
        and str(user_id) == str(property_obj.owner_id)
    )

    if not is_owner:

        # Prevent repeated refreshes from being counted
        # repeatedly during the same session.
        existing_view = PropertyView.objects(
            property_id=property_id,
            session_key=session_key
        ).first()

        if not existing_view:

            PropertyView(
                property_id=property_id,
                student_id=(
                    str(user_id)
                    if role == "student" and user_id
                    else ""
                ),
                session_key=session_key,
                viewed_at=datetime.now()
            ).save()

    vacant_rooms = [
        room
        for room in property_obj.rooms
        if room.status == "vacant"
    ]

    user_id = request.session.get("user_id")

    is_favourite = False

    # --------------------------------------------------------
    # FAVOURITE STATUS
    # --------------------------------------------------------
    if (
        user_id
        and
        request.session.get("role") == "student"
    ):
        existing_favourite = Favourite.objects(
            student_id=user_id,
            property_id=property_id
        ).first()

        is_favourite = (
            existing_favourite is not None
        )

    # --------------------------------------------------------
    # PAYMENT / UNLOCK STATUS
    # --------------------------------------------------------
    unlocked = False

    if user_id:
        existing_payment = Payment.objects(
            student_id=user_id,
            property_id=property_id,
            status="successful"
        ).first()

        unlocked = (
            existing_payment is not None
        )

    # --------------------------------------------------------
    # COVER PHOTO
    # --------------------------------------------------------
    cover_photo = get_cover_photo(
        property_obj
    )

    # --------------------------------------------------------
    # APPROVED REVIEWS
    # --------------------------------------------------------
    approved_reviews = Review.objects(
        property_id=property_id,
        status="approved"
    ).order_by("-created_at")

    return render(
        request,
        "properties/property_detail.html",
        {
            "property": property_obj,
            "vacant_rooms": vacant_rooms,
            "cover_photo": cover_photo,
            "unlocked": unlocked,
            "is_favourite": is_favourite,
            "approved_reviews": approved_reviews,
        }
    )

# ============================================================
# COVER PHOTO HELPER
# ============================================================

def get_cover_photo(property_obj):

    for photo in property_obj.photos:

        if photo.is_cover:

            return photo

    if property_obj.photos:

        return property_obj.photos[0]

    return None


# ============================================================
# OWNER: MY PROPERTIES
# ============================================================

@owner_required
def my_properties(request):

    user_id = request.session.get(
        "user_id"
    )

    properties = Property.objects(
        owner_id=user_id
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "owner_dashboard/my_properties.html",
        {
            "properties":
                properties,
        }
    )


# ============================================================
# OWNER: ADD PROPERTY
# ============================================================


@owner_required
def add_property(request):

    if request.method == "POST":

        form = PropertyForm(
            request.POST
        )

        if form.is_valid():

            user_id = request.session.get(
                "user_id"
            )

            property_id = str(
                uuid.uuid4()
            )

            property_obj = Property(
                property_id=property_id,

                owner_id=user_id,

                name=form.cleaned_data[
                    "name"
                ],

                caretaker_name=form.cleaned_data.get(
                    "caretaker_name",
                    ""
                ),

                caretaker_contact=form.cleaned_data.get(
                    "caretaker_contact",
                    ""
                ),

                landlord_name=form.cleaned_data.get(
                    "landlord_name",
                    ""
                ),

                landlord_contact=form.cleaned_data.get(
                    "landlord_contact",
                    ""
                ),

                description=form.cleaned_data.get(
                    "description",
                    ""
                ),

                location=Location(
                    area=form.cleaned_data[
                        "area"
                    ],

                    landmark=form.cleaned_data.get(
                        "landmark",
                        ""
                    ),

                    latitude=form.cleaned_data.get(
                        "latitude"
                    ),

                    longitude=form.cleaned_data.get(
                        "longitude"
                    ),
                ),

                distance_from_university=(
                    form.cleaned_data.get(
                        "distance_from_university"
                    )
                ),

                monthly_price=(
                    form.cleaned_data.get(
                        "monthly_price"
                    )
                ),

                semester_price=(
                    form.cleaned_data.get(
                        "semester_price"
                    )
                ),

                Cost_Sharing=(
                    form.cleaned_data.get(
                        "Cost_Sharing"
                    )
                ),

                amenities=(
                    form.cleaned_data.get(
                        "amenities",
                        []
                    )
                ),

                rooms=[],

                photos=[],

                approval_status="pending",

                status="active",

                created_at=datetime.now(),

                updated_at=datetime.now(),
            )

            property_obj.save()


            # Notify all active admins
            # about the new property

            admin_users = User.objects(
                role="admin",
                status="active"
            )

            for admin in admin_users:

                create_notification(
                    user_id=str(admin.id),

                    recipient_id=str(admin.id),

                    recipient_role="admin",

                    notification_type=(
                        "property_submitted"
                    ),

                    title="New Property Submitted",

                    message=(
                        f"Property "
                        f"#{property_obj.property_id} "
                        f"has been submitted by an "
                        f"owner and is awaiting "
                        f"approval."
                    ),

                    related_id=(
                        str(
                            property_obj.property_id
                        )
                    ),
                )


            messages.success(
                request,
                (
                    "Property added successfully. "
                    "It is now pending approval."
                )
            )

            return redirect(
                "owner_dashboard:dashboard"
            )

    else:

        form = PropertyForm()


    return render(
        request,
        "properties/add_property.html",
        {
            "form": form
        }
    )




# ============================================================
# OWNER: MANAGE ROOMS
# ============================================================

@owner_required
def manage_rooms(
    request,
    property_id
):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    current_user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != current_user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    form = RoomForm()

    return render(
        request,
        "owner_dashboard/manage_rooms.html",
        {
            "property":
                property_obj,

            "form":
                form,
        }
    )


# ============================================================
# OWNER: ADD ROOM
# ============================================================

@owner_required
def add_room(
    request,
    property_id
):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    if request.method != "POST":

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    form = RoomForm(
        request.POST
    )

    if not form.is_valid():

        for errors in form.errors.values():

            for error in errors:

                messages.error(
                    request,
                    error
                )

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    room_number = form.cleaned_data[
        "room_number"
    ]

    existing_room = next(
        (
            room
            for room in property_obj.rooms
            if room.room_number == room_number
        ),
        None
    )

    if existing_room:

        messages.error(
            request,
            f"Room {room_number} already exists."
        )

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    room = Room(
        room_number=room_number,

        room_type=form.cleaned_data[
            "room_type"
        ],

        price=form.cleaned_data[
            "price"
        ],

        status=form.cleaned_data[
            "status"
        ],
    )

    property_obj.rooms.append(
        room
    )

    property_obj.updated_at = datetime.now()

    property_obj.save()

    messages.success(
        request,
        f"Room {room_number} added successfully."
    )

    return redirect(
        "properties:manage_rooms",
        property_id=property_id
    )


# ============================================================
# OWNER: UPDATE ROOM STATUS
# ============================================================

@owner_required
def update_room_status(
    request,
    property_id,
    room_number
):

    if request.method != "POST":

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    current_user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != current_user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    room = next(
        (
            room
            for room in property_obj.rooms
            if room.room_number == room_number
        ),
        None
    )

    if room is None:

        messages.error(
            request,
            "Room not found."
        )

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    new_status = request.POST.get(
        "status"
    )

    allowed_statuses = [
        "vacant",
        "occupied",
        "reserved",
        "maintenance",
    ]

    if new_status not in allowed_statuses:

        messages.error(
            request,
            "Invalid room status."
        )

        return redirect(
            "properties:manage_rooms",
            property_id=property_id
        )

    old_status = room.status

    room.status = new_status

    property_obj.updated_at = datetime.now()

    property_obj.save()

    # --------------------------------------------------------
    # NOTIFY STUDENTS WHEN ROOM BECOMES VACANT
    # --------------------------------------------------------

    if (
        old_status != "vacant"
        and
        new_status == "vacant"
    ):

        notify_students_property_available(
            property_obj
        )

    messages.success(
        request,
        f"Room {room_number} is now {new_status}."
    )

    return redirect(
        "properties:manage_rooms",
        property_id=property_id
    )


# ============================================================
# AVAILABILITY NOTIFICATION
# ============================================================

def notify_when_available(
    request,
    property_id
):

    if request.method != "POST":

        return redirect(
            "properties:property_list"
        )

    student_id = request.session.get(
        "user_id"
    )

    role = request.session.get(
        "role"
    )

    if not student_id or role != "student":

        messages.error(
            request,
            "Please log in as a student."
        )

        return redirect(
            "accounts:login"
        )

    property_obj = Property.objects(
        property_id=property_id,
        approval_status="approved",
        status="active"
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:property_list"
        )

    if property_obj.vacant_room_count > 0:

        messages.info(
            request,
            "This property currently has available rooms."
        )

        return redirect(
            "properties:property_list"
        )

    existing_alert = AvailabilityAlert.objects(
        student_id=student_id,
        property_id=property_id,
        status="active"
    ).first()

    if existing_alert:

        messages.info(
            request,
            (
                "You are already subscribed to availability "
                "notifications for this property."
            )
        )

        return redirect(
            "properties:property_list"
        )

    alert = AvailabilityAlert(
        student_id=student_id,

        property_id=property_id,

        status="active",

        created_at=datetime.now(),
    )

    alert.save()

    messages.success(
        request,
        "You'll be notified when a room becomes available."
    )

    return redirect(
        "properties:property_list"
    )


# ============================================================
# NOTIFY STUDENTS
# ============================================================

def notify_students_property_available(
    property_obj
):

    alerts = AvailabilityAlert.objects(
        property_id=property_obj.property_id,
        status="active"
    )

    if not alerts:

        return

    now = datetime.now()

    for alert in alerts:

        try:

            create_notification(
                recipient_id=str(
                    alert.student_id
                ),

                recipient_role="student",

                notification_type="availability",

                title="Room Now Available",

                message=(
                    f"A room is now available at "
                    f"{property_obj.name}."
                ),

                related_id=str(
                    property_obj.property_id
                ),
            )

        except Exception:

            # Fallback for projects where the notification
            # helper is unavailable or uses a different model.

            try:

                Notification(
                    recipient_id=str(
                        alert.student_id
                    ),

                    title="Room Now Available",

                    message=(
                        f"A room is now available at "
                        f"{property_obj.name} "
                        f"({property_obj.property_id})."
                    ),

                    notification_type="availability",

                    is_read=False,

                    created_at=now,
                ).save()

            except Exception:

                pass

        alert.status = "notified"

        alert.notified_at = now

        alert.save()


# ============================================================
# FAVOURITES
# ============================================================

def add_favourite(
    request,
    property_id
):

    if request.session.get("role") != "student":

        messages.error(
            request,
            "Please log in as a student."
        )

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

    property_obj = Property.objects(
        property_id=property_id,
        approval_status="approved",
        status="active"
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:property_list"
        )

    existing_favourite = Favourite.objects(
        student_id=student_id,
        property_id=property_id
    ).first()

    if existing_favourite:

        messages.info(
            request,
            "This property is already in your favourites."
        )

    else:

        Favourite(
            student_id=student_id,

            property_id=property_id,

            created_at=datetime.now(),
        ).save()

        messages.success(
            request,
            "Property added to your favourites."
        )

    return redirect(
        "properties:property_detail",
        property_id=property_id
    )


def remove_favourite(
    request,
    property_id
):

    if request.session.get("role") != "student":

        messages.error(
            request,
            "Please log in as a student."
        )

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

    favourite = Favourite.objects(
        student_id=student_id,
        property_id=property_id
    ).first()

    if favourite:

        favourite.delete()

        messages.success(
            request,
            "Property removed from your favourites."
        )

    else:

        messages.info(
            request,
            "This property is not in your favourites."
        )

    return redirect(
        "properties:property_detail",
        property_id=property_id
    )


def favourite_list(request):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

    favourites = Favourite.objects(
        student_id=student_id
    )

    favourite_properties = []

    for favourite in favourites:

        property_obj = Property.objects(
            property_id=favourite.property_id
        ).first()

        if property_obj:

            favourite_properties.append(
                {
                    "favourite":
                        favourite,

                    "property":
                        property_obj,
                }
            )

    return render(
        request,
        "properties/favourites.html",
        {
            "favourites":
                favourite_properties,
        }
    )


# ============================================================
# PROPERTY PHOTOS
# ============================================================

@owner_required
def manage_photos(
    request,
    property_id
):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    if request.method == "POST":

        uploaded_files = request.FILES.getlist(
            "photos"
        )

        if not uploaded_files:

            messages.error(
                request,
                "Please select at least one photo to upload."
            )

            return redirect(
                "properties:manage_photos",
                property_id=property_id
            )

        current_count = len(
            property_obj.photos
        )

        if (
            current_count
            +
            len(uploaded_files)
            > 4
        ):

            messages.error(
                request,
                (
                    "You can have a maximum of 4 photos. "
                    f"You currently have {current_count}."
                )
            )

            return redirect(
                "properties:manage_photos",
                property_id=property_id
            )

        for uploaded_file in uploaded_files:

            extension = os.path.splitext(
                uploaded_file.name
            )[1].lower()

            filename = (
                f"properties/"
                f"{property_id}/"
                f"{uuid.uuid4()}"
                f"{extension}"
            )

            saved_path = default_storage.save(
                filename,
                uploaded_file
            )

            is_first_photo = (
                len(property_obj.photos) == 0
            )

            photo = Photo(
                url=default_storage.url(
                    saved_path
                ),

                caption="",

                is_cover=is_first_photo,
            )

            property_obj.photos.append(
                photo
            )

        property_obj.updated_at = datetime.now()

        property_obj.save()

        messages.success(
            request,
            "Photos uploaded successfully."
        )

        return redirect(
            "properties:manage_photos",
            property_id=property_id
        )

    form = PropertyPhotoForm()

    return render(
        request,
        "properties/manage_photos.html",
        {
            "property":
                property_obj,

            "form":
                form,

            "photo_count":
                len(property_obj.photos),

            "remaining_slots":
                4 - len(property_obj.photos),
        }
    )


# ============================================================
# SET COVER PHOTO
# ============================================================

@owner_required
def set_cover_photo(
    request,
    property_id,
    photo_index
):

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    if (
        photo_index < 0
        or
        photo_index >= len(
            property_obj.photos
        )
    ):

        messages.error(
            request,
            "Photo not found."
        )

        return redirect(
            "properties:manage_photos",
            property_id=property_id
        )

    for index, photo in enumerate(
        property_obj.photos
    ):

        photo.is_cover = (
            index == photo_index
        )

    property_obj.updated_at = datetime.now()

    property_obj.save()

    messages.success(
        request,
        "Cover photo updated successfully."
    )

    return redirect(
        "properties:manage_photos",
        property_id=property_id
    )


# ============================================================
# DELETE PHOTO
# ============================================================

@owner_required
def delete_photo(
    request,
    property_id,
    photo_index
):

    if request.method != "POST":

        return redirect(
            "properties:manage_photos",
            property_id=property_id
        )

    property_obj = Property.objects(
        property_id=property_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:my_properties"
        )

    user_id = str(
        request.session.get(
            "user_id"
        )
    )

    if property_obj.owner_id != user_id:

        messages.error(
            request,
            "You are not authorized to manage this property."
        )

        return redirect(
            "properties:my_properties"
        )

    if (
        photo_index < 0
        or
        photo_index >= len(
            property_obj.photos
        )
    ):

        messages.error(
            request,
            "Photo not found."
        )

        return redirect(
            "properties:manage_photos",
            property_id=property_id
        )

    photo = property_obj.photos[
        photo_index
    ]

    was_cover = photo.is_cover

    photo_url = photo.url

    del property_obj.photos[
        photo_index
    ]

    if (
        was_cover
        and
        property_obj.photos
    ):

        for index, remaining_photo in enumerate(
            property_obj.photos
        ):

            remaining_photo.is_cover = (
                index == 0
            )

    property_obj.updated_at = datetime.now()

    property_obj.save()

    # --------------------------------------------------------
    # DELETE ACTUAL FILE
    # --------------------------------------------------------

    if photo_url:

        media_url = settings.MEDIA_URL

        if photo_url.startswith(
            media_url
        ):

            file_path = photo_url.replace(
                media_url,
                "",
                1
            )

            file_path = os.path.join(
                settings.MEDIA_ROOT,
                file_path
            )

            if os.path.exists(
                file_path
            ):

                os.remove(
                    file_path
                )

    messages.success(
        request,
        "Photo deleted successfully."
    )

    return redirect(
        "properties:manage_photos",
        property_id=property_id
    )


# ============================================================
# PROPERTY REPORT
# ============================================================

def report_property(
    request,
    property_id
):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

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

    if request.method == "POST":

        form = PropertyReportForm(
            request.POST
        )

        if form.is_valid():

            Report(
                student_id=student_id,

                property_id=property_id,

                reason=form.cleaned_data[
                    "reason"
                ],

                description=form.cleaned_data[
                    "description"
                ],

                status="pending",

                created_at=datetime.now(),
            )
          

            Report.save()


            # Notify all active admins about the new report
            admin_users = User.objects(
                role="admin",
                status="active"
            )

            for admin in admin_users:

                create_notification(
                    user_id=str(admin.id),
                    recipient_id=str(admin.id),
                    recipient_role="admin",
                    notification_type="report_submitted",
                    title="New Property Report",
                    message=(
                        f"A student has submitted a report "
                        f"for property #{property_id}. "
                        f"Reason: {Report.reason}"
                    ),
                    related_id=str(property_id),
                )



            messages.success(
                request,
                (
                    "Your report has been submitted. "
                    "Thank you for helping keep Rongo Homes safe."
                )
            )

            return redirect(
                "properties:property_detail",
                property_id=property_id
            )

    else:

        form = PropertyReportForm()

    return render(
        request,
        "properties/report_property.html",
        {
            "property":
                property_obj,

            "form":
                form,
        }
    )


# ============================================================
# PROPERTY COMPARISON
# ============================================================

def add_to_compare(
    request,
    property_id
):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    property_obj = Property.objects(
        property_id=property_id,

        approval_status="approved",

        status="active"
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:student_home"
        )

    compare_list = request.session.get(
        "compare_properties",
        []
    )

    if property_id in compare_list:

        messages.info(
            request,
            "This property is already in your comparison."
        )

        return redirect(
            "properties:student_home"
        )

    if len(compare_list) >= 3:

        messages.warning(
            request,
            (
                "You can compare a maximum of "
                "3 properties at a time."
            )
        )

        return redirect(
            "properties:student_home"
        )

    compare_list.append(
        property_id
    )

    request.session[
        "compare_properties"
    ] = compare_list

    request.session.modified = True

    messages.success(
        request,
        "Property added to comparison."
    )

    return redirect(
        "properties:student_home"
    )


def compare_properties(request):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    property_ids = request.session.get(
        "compare_properties",
        []
    )

    properties = []

    for property_id in property_ids:

        property_obj = Property.objects(
            property_id=property_id,

            approval_status="approved",

            status="active"
        ).first()

        if property_obj:

            vacant_rooms = [
                room
                for room in property_obj.rooms
                if room.status == "vacant"
            ]

            properties.append(
                {
                    "property":
                        property_obj,

                    "vacant_rooms":
                        vacant_rooms,
                }
            )

    return render(
        request,
        "properties/compare_properties.html",
        {
            "properties":
                properties,
        }
    )


def remove_from_compare(
    request,
    property_id
):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    compare_list = request.session.get(
        "compare_properties",
        []
    )

    if property_id in compare_list:

        compare_list.remove(
            property_id
        )

    request.session[
        "compare_properties"
    ] = compare_list

    request.session.modified = True

    return redirect(
        "properties:compare_properties"
    )


def clear_comparison(request):

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    request.session[
        "compare_properties"
    ] = []

    request.session.modified = True

    messages.success(
        request,
        "Comparison list cleared."
    )

    return redirect(
        "properties:student_home"
    )

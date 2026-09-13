import os
import uuid
from accounts.models import User
from notifications.utils import create_notification
from properties.forms import(PropertyForm, PropertyPhotoForm,RoomForm,)
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib import messages
from properties.models import Location, Property, Photo,PropertyView,Favourite
from properties.forms import PropertyPhotoForm
from django.shortcuts import render, redirect
from accounts.decorators import owner_required
from payments.models import Payment
from datetime import datetime, timedelta
@owner_required
def dashboard(request):
    if request.session.get("role") != "owner":
        return redirect("accounts:login")
    owner_id = request.session.get("user_id")

    properties = Property.objects(
        owner_id=owner_id
    )

    total_properties = properties.count()

    approved_properties = Property.objects(
        owner_id=owner_id,
        approval_status="approved"
    ).count()

    pending_properties = Property.objects(
        owner_id=owner_id,
        approval_status="pending"
    ).count()

    rejected_properties = Property.objects(
        owner_id=owner_id,
        approval_status="rejected"
    ).count()

    suspended_properties = Property.objects(
        owner_id=owner_id,
        status="suspended"
    ).count()

    total_rooms = 0
    vacant_rooms = 0
    occupied_rooms = 0
    
        # ============================================================
    # PROPERTY ANALYTICS
    # ============================================================

    property_analytics = []

    total_views = 0

    for property_obj in properties:

        views = PropertyView.objects(
            property_id=property_obj.property_id
        )

        view_count = views.count()

        total_views += view_count

        property_analytics.append(
            {
                "property": property_obj,
                "views": view_count,
            }
        )
    for property_obj in properties:

        for room in property_obj.rooms:

            total_rooms += 1

            if room.status == "vacant":
                vacant_rooms += 1

            elif room.status == "occupied":
                occupied_rooms += 1

    return render(
        request,
        "owner_dashboard/dashboard.html",
        {
            "properties": properties,
            "total_properties": total_properties,
            "approved_properties": approved_properties,
            "pending_properties": pending_properties,
            "rejected_properties": rejected_properties,
            "suspended_properties": suspended_properties,
            "total_rooms": total_rooms,
            "vacant_rooms": vacant_rooms,
            "occupied_rooms": occupied_rooms,
            "total_views": total_views,
            "property_analytics": property_analytics,
        }
    )
    

def manage_rooms(request, property_id):
    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    owner_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=owner_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized to manage it."
        )
        return redirect("owner_dashboard:dashboard")

    return render(
        request,
        "owner_dashboard/manage_rooms.html",
        {
            "property": property_obj,
        }
    )


def update_room_status(
    request,
    property_id,
    room_number
):
    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    if request.method != "POST":
        return redirect(
            "owner_dashboard:manage_rooms",
            property_id=property_id
        )

    owner_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=owner_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized to manage it."
        )
        return redirect("owner_dashboard:dashboard")

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
            "owner_dashboard:manage_rooms",
            property_id=property_id
        )

    new_status = request.POST.get("status")

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
            "owner_dashboard:manage_rooms",
            property_id=property_id
        )

    old_status = room.status
    room.status = new_status

    property_obj.updated_at = datetime.now()
    property_obj.save()

    messages.success(
        request,
        f"Room {room_number} is now {new_status}."
    )

    return redirect(
        "owner_dashboard:manage_rooms",
        property_id=property_id
    )
    

@owner_required
def edit_room(request, property_id, room_number):

    owner_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=owner_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized to manage it."
        )
        return redirect("owner_dashboard:dashboard")

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
            "owner_dashboard:manage_rooms",
            property_id=property_id
        )

    if request.method == "POST":

        form = RoomForm(request.POST)

        if form.is_valid():

            new_room_number = form.cleaned_data["room_number"]

            # Prevent duplicate room numbers
            duplicate_room = next(
                (
                    existing_room
                    for existing_room in property_obj.rooms
                    if existing_room is not room
                    and existing_room.room_number == new_room_number
                ),
                None
            )

            if duplicate_room:
                form.add_error(
                    "room_number",
                    "A room with this room number already exists."
                )

            else:

                room.room_number = new_room_number
                room.room_type = form.cleaned_data["room_type"]
                room.price = form.cleaned_data["price"]
                room.status = form.cleaned_data["status"]

                property_obj.updated_at = datetime.now()
                property_obj.save()

                messages.success(
                    request,
                    f"Room {new_room_number} updated successfully."
                )

                return redirect(
                    "owner_dashboard:manage_rooms",
                    property_id=property_id
                )

    else:

        form = RoomForm(
            initial={
                "room_number": room.room_number,
                "room_type": room.room_type,
                "price": room.price,
                "status": room.status,
            }
        )

    return render(
        request,
        "owner_dashboard/edit_room.html",
        {
            "property": property_obj,
            "room": room,
            "form": form,
        }
    )


    
def my_properties(request):
    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    owner_id = request.session.get("user_id")

    properties = Property.objects(
        owner_id=owner_id
    )

    return render(
        request,
        "owner_dashboard/my_properties.html",
        {
            "properties": properties,
        }
    )
    
def manage_photos(request, property_id):

    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    user_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=user_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized to manage it."
        )

        return redirect(
            "owner_dashboard:my_properties"
        )

    if request.method == "POST":

        form = PropertyPhotoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            uploaded_files = request.FILES.getlist(
                "photos"
            )

            current_count = len(
                property_obj.photos
            )

            total_count = (
                current_count
                + len(uploaded_files)
            )

            if total_count > 4:

                messages.error(
                    request,
                    f"You can have a maximum of 4 photos. "
                    f"You currently have {current_count}."
                )

                return redirect(
                    "owner_dashboard:manage_photos",
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
                    is_cover=is_first_photo
                )

                property_obj.photos.append(
                    photo
                )

            property_obj.save()

            messages.success(
                request,
                "Photos uploaded successfully."
            )

            return redirect(
                "owner_dashboard:manage_photos",
                property_id=property_id
            )

    else:
        form = PropertyPhotoForm()

    return render(
        request,
        "owner_dashboard/manage_photos.html",
        {
            "property": property_obj,
            "form": form,
            "photo_count": len(property_obj.photos),
            "remaining_slots": 4 - len(property_obj.photos),
        }
    )
    
def set_cover_photo(
    request,
    property_id,
    photo_index
):

    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    user_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=user_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized."
        )

        return redirect(
            "owner_dashboard:my_properties"
        )

    if (
        photo_index < 0
        or photo_index >= len(property_obj.photos)
    ):
        messages.error(
            request,
            "Photo not found."
        )

        return redirect(
            "owner_dashboard:manage_photos",
            property_id=property_id
        )

    for index, photo in enumerate(
        property_obj.photos
    ):
        photo.is_cover = (
            index == photo_index
        )

    property_obj.save()

    messages.success(
        request,
        "Cover photo updated successfully."
    )

    return redirect(
        "owner_dashboard:manage_photos",
        property_id=property_id
    )
    
def delete_photo(
    request,
    property_id,
    photo_index
):

    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    user_id = request.session.get("user_id")

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=user_id
    ).first()

    if not property_obj:
        messages.error(
            request,
            "Property not found or you are not authorized."
        )

        return redirect(
            "owner_dashboard:my_properties"
        )

    if (
        photo_index < 0
        or photo_index >= len(property_obj.photos)
    ):
        messages.error(
            request,
            "Photo not found."
        )

        return redirect(
            "owner_dashboard:manage_photos",
            property_id=property_id
        )

    photo = property_obj.photos[photo_index]

    was_cover = photo.is_cover
    photo_url = photo.url

    del property_obj.photos[photo_index]

    if was_cover and property_obj.photos:

        property_obj.photos[0].is_cover = True

    property_obj.save()

    if photo_url.startswith(
        settings.MEDIA_URL
    ):

        file_path = photo_url.replace(
            settings.MEDIA_URL,
            "",
            1
        )

        file_path = os.path.join(
            settings.MEDIA_ROOT,
            file_path
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    messages.success(
        request,
        "Photo deleted successfully."
    )

    return redirect(
        "owner_dashboard:manage_photos",
        property_id=property_id
    )
    



@owner_required
def analytics(request):

    if request.session.get("role") != "owner":
        return redirect("accounts:login")

    owner_id = request.session.get("user_id")

    # ========================================================
    # OWNER PROPERTIES
    # ========================================================

    properties = list(
        Property.objects(
            owner_id=owner_id
        )
    )

    property_ids = [
        property_obj.property_id
        for property_obj in properties
    ]

    # ========================================================
    # SUMMARY TOTALS
    # ========================================================

    total_views = 0
    total_unique_students = 0
    total_favourites = 0
    total_unlocks = 0

    property_analytics = []

    # ========================================================
    # PROPERTY ANALYTICS
    # ========================================================

    for property_obj in properties:

        property_id = property_obj.property_id

        # ----------------------------------------------------
        # VIEWS
        # ----------------------------------------------------

        views = PropertyView.objects(
            property_id=property_id
        )

        view_count = views.count()

        total_views += view_count

        # ----------------------------------------------------
        # UNIQUE STUDENTS
        # ----------------------------------------------------

        student_ids = set()

        for view in views:

            if view.student_id:

                student_ids.add(
                    view.student_id
                )

        unique_students = len(student_ids)

        total_unique_students += unique_students

        # ----------------------------------------------------
        # FAVOURITES
        # ----------------------------------------------------

        favourite_count = Favourite.objects(
            property_id=property_id
        ).count()

        total_favourites += favourite_count

        # ----------------------------------------------------
        # SUCCESSFUL CONTACT UNLOCKS
        # ----------------------------------------------------

        unlock_count = Payment.objects(
            property_id=property_id,
            payment_type="contact_unlock",
            status="successful"
        ).count()

        total_unlocks += unlock_count

        # ----------------------------------------------------
        # ROOMS
        # ----------------------------------------------------

        total_rooms = len(
            property_obj.rooms
        )

        vacant_rooms = 0
        occupied_rooms = 0
        reserved_rooms = 0
        maintenance_rooms = 0

        for room in property_obj.rooms:

            if room.status == "vacant":

                vacant_rooms += 1

            elif room.status == "occupied":

                occupied_rooms += 1

            elif room.status == "reserved":

                reserved_rooms += 1

            elif room.status == "maintenance":

                maintenance_rooms += 1

        # ----------------------------------------------------
        # INTEREST RATE
        # ----------------------------------------------------

        if view_count > 0:

            interest_rate = round(
                (unlock_count / view_count) * 100,
                1
            )

        else:

            interest_rate = 0

        property_analytics.append(
            {
                "property": property_obj,

                "views": view_count,

                "unique_students":
                    unique_students,

                "favourites":
                    favourite_count,

                "unlock_count":
                    unlock_count,

                "total_rooms":
                    total_rooms,

                "vacant_rooms":
                    vacant_rooms,

                "occupied_rooms":
                    occupied_rooms,

                "reserved_rooms":
                    reserved_rooms,

                "maintenance_rooms":
                    maintenance_rooms,

                "interest_rate":
                    interest_rate,
            }
        )

    # ========================================================
    # SORT PROPERTY PERFORMANCE
    # ========================================================

    property_analytics.sort(
        key=lambda item: item["views"],
        reverse=True
    )

    # ========================================================
    # AVERAGE VIEWS
    # ========================================================

    property_count = len(properties)

    if property_count:

        average_views = round(
            total_views / property_count,
            1
        )

    else:

        average_views = 0

    # ========================================================
    # MOST VIEWED PROPERTY
    # ========================================================

    most_viewed_property = None

    if property_analytics:

        most_viewed_property = (
            property_analytics[0]
        )

    # ========================================================
    # DATE RANGE
    # ========================================================

    today = datetime.now().date()

    start_date = today - timedelta(days=29)

    # ========================================================
    # BUILD DAILY ANALYTICS
    # ========================================================

    daily_data = {}

    current_date = start_date

    while current_date <= today:

        date_key = current_date.isoformat()

        daily_data[date_key] = {
            "views": 0,
            "favourites": 0,
            "unlocks": 0,
        }

        current_date += timedelta(days=1)

    # ========================================================
    # DAILY PROPERTY VIEWS
    # ========================================================

    if property_ids:

        for property_id in property_ids:

            views = PropertyView.objects(
                property_id=property_id
            )

            for view in views:

                if not view.viewed_at:
                    continue

                view_date = (
                    view.viewed_at.date()
                )

                if (
                    start_date
                    <= view_date
                    <= today
                ):

                    date_key = view_date.isoformat()

                    daily_data[
                        date_key
                    ]["views"] += 1

    # ========================================================
    # DAILY FAVOURITES
    # ========================================================

    if property_ids:

        for property_id in property_ids:

            favourites = Favourite.objects(
                property_id=property_id
            )

            for favourite in favourites:

                if not favourite.created_at:
                    continue

                favourite_date = (
                    favourite.created_at.date()
                )

                if (
                    start_date
                    <= favourite_date
                    <= today
                ):

                    date_key = (
                        favourite_date.isoformat()
                    )

                    daily_data[
                        date_key
                    ]["favourites"] += 1

    # ========================================================
    # DAILY SUCCESSFUL UNLOCKS
    # ========================================================

    if property_ids:

        for property_id in property_ids:

            unlocks = Payment.objects(
                property_id=property_id,
                payment_type="contact_unlock",
                status="successful"
            )

            for payment in unlocks:

                if not payment.created_at:
                    continue

                payment_date = (
                    payment.created_at.date()
                )

                if (
                    start_date
                    <= payment_date
                    <= today
                ):

                    date_key = (
                        payment_date.isoformat()
                    )

                    daily_data[
                        date_key
                    ]["unlocks"] += 1

    # ========================================================
    # CHART DATA
    # ========================================================

    chart_labels = []
    chart_views = []
    chart_favourites = []
    chart_unlocks = []

    for date_key, values in daily_data.items():

        date_object = datetime.strptime(
            date_key,
            "%Y-%m-%d"
        ).date()

        chart_labels.append(
            date_object.strftime(
                "%d %b"
            )
        )

        chart_views.append(
            values["views"]
        )

        chart_favourites.append(
            values["favourites"]
        )

        chart_unlocks.append(
            values["unlocks"]
        )

    analytics_chart_data = {
        "labels": chart_labels,

        "views": chart_views,

        "favourites":
            chart_favourites,

        "unlocks":
            chart_unlocks,
    }

    # ========================================================
    # PROPERTY COMPARISON CHART
    # ========================================================

    property_chart_labels = []
    property_chart_views = []
    property_chart_favourites = []
    property_chart_unlocks = []

    for item in property_analytics:

        property_chart_labels.append(
            item["property"].name
        )

        property_chart_views.append(
            item["views"]
        )

        property_chart_favourites.append(
            item["favourites"]
        )

        property_chart_unlocks.append(
            item["unlock_count"]
        )

    property_chart_data = {
        "labels":
            property_chart_labels,

        "views":
            property_chart_views,

        "favourites":
            property_chart_favourites,

        "unlocks":
            property_chart_unlocks,
    }

    # ========================================================
    # RECENT ACTIVITY
    # ========================================================

    recent_views = []

    for property_obj in properties:

        views = PropertyView.objects(
            property_id=property_obj.property_id
        ).order_by(
            "-viewed_at"
        )[:10]

        for view in views:

            recent_views.append(
                {
                    "property":
                        property_obj,

                    "view":
                        view,
                }
            )

    recent_views.sort(
        key=lambda item:
            item["view"].viewed_at,
        reverse=True
    )

    recent_views = recent_views[:10]

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "owner_dashboard/analytics.html",
        {
            "properties":
                properties,

            "property_count":
                property_count,

            "total_views":
                total_views,

            "total_unique_students":
                total_unique_students,

            "total_favourites":
                total_favourites,

            "total_unlocks":
                total_unlocks,

            "average_views":
                average_views,

            "most_viewed_property":
                most_viewed_property,

            "property_analytics":
                property_analytics,

            "recent_views":
                recent_views,

            "analytics_chart_data":
                analytics_chart_data,

            "property_chart_data":
                property_chart_data,
        }
    )
    

@owner_required
def edit_property(request, property_id):

    owner_id = request.session.get(
        "user_id"
    )

    property_obj = Property.objects(
        property_id=property_id,
        owner_id=owner_id
    ).first()

    if not property_obj:

        messages.error(
            request,
            (
                "Property not found or you are "
                "not authorized to edit it."
            )
        )

        return redirect(
            "owner_dashboard:my_properties"
        )

    if request.method == "POST":

        form = PropertyForm(
            request.POST
        )

        if form.is_valid():

            property_obj.name = (
                form.cleaned_data["name"]
            )

            property_obj.caretaker_name = (
                form.cleaned_data.get(
                    "caretaker_name",
                    ""
                )
            )

            property_obj.caretaker_contact = (
                form.cleaned_data.get(
                    "caretaker_contact",
                    ""
                )
            )

            property_obj.landlord_name = (
                form.cleaned_data.get(
                    "landlord_name",
                    ""
                )
            )

            property_obj.landlord_contact = (
                form.cleaned_data.get(
                    "landlord_contact",
                    ""
                )
            )

            property_obj.description = (
                form.cleaned_data.get(
                    "description",
                    ""
                )
            )

            property_obj.location = Location(
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
            )

            property_obj.distance_from_university = (
                form.cleaned_data.get(
                    "distance_from_university"
                )
            )

            property_obj.monthly_price = (
                form.cleaned_data.get(
                    "monthly_price"
                )
            )

            property_obj.semester_price = (
                form.cleaned_data.get(
                    "semester_price"
                )
            )

            property_obj.Cost_Sharing = (
                form.cleaned_data.get(
                    "Cost_Sharing"
                )
            )

            property_obj.amenities = (
                form.cleaned_data.get(
                    "amenities",
                    []
                )
            )

            # Require admin approval again
            property_obj.approval_status = "pending"

            property_obj.updated_at = datetime.now()

            property_obj.save()


            # Notify all active admins
            admin_users = User.objects(
                role="admin",
                status="active"
            )

            for admin in admin_users:

                create_notification(
                    user_id=str(admin.id),

                    recipient_id=str(admin.id),

                    recipient_role="admin",

                    notification_type="property_submitted",

                    title="Property Update Submitted",

                    message=(
                        f"Property "
                        f"#{property_obj.property_id} "
                        f"has been updated by its owner "
                        f"and is awaiting approval."
                    ),

                    related_id=str(
                        property_obj.property_id
                    ),
                )


            messages.success(
                request,
                (
                    "Property details updated successfully. "
                    "The changes are now pending admin approval."
                )
            )

            return redirect(
                "owner_dashboard:my_properties"
            )

    else:

        initial_data = {
            "name": property_obj.name,

            "caretaker_name":
                property_obj.caretaker_name,

            "caretaker_contact":
                property_obj.caretaker_contact,

            "landlord_name":
                property_obj.landlord_name,

            "landlord_contact":
                property_obj.landlord_contact,

            "description":
                property_obj.description,

            "area":
                property_obj.location.area,

            "landmark":
                property_obj.location.landmark,

            "latitude":
                property_obj.location.latitude,

            "longitude":
                property_obj.location.longitude,

            "distance_from_university":
                property_obj.distance_from_university,

            "monthly_price":
                property_obj.monthly_price,

            "semester_price":
                property_obj.semester_price,

            "Cost_Sharing":
                property_obj.Cost_Sharing,

            "amenities":
                property_obj.amenities,
        }

        form = PropertyForm(
            initial=initial_data
        )

    return render(
        request,
        "owner_dashboard/edit_property.html",
        {
            "property": property_obj,
            "form": form,
        }
    )


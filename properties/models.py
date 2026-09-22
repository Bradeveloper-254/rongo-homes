import datetime

from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    FloatField,
    ListField,
    EmbeddedDocumentField,
    BooleanField,
    DateTimeField,
)


# ============================================================
# ROOM
# ============================================================

class Room(EmbeddedDocument):

    room_number = StringField(
        required=True
    )

    room_type = StringField(
        required=True
    )

    price = FloatField(
        required=True,
        min_value=0
    )

    status = StringField(
        choices=[
            "vacant",
            "occupied",
            "reserved",
            "maintenance",
        ],
        default="vacant"
    )


# ============================================================
# PROPERTY PHOTO
# ============================================================

class Photo(EmbeddedDocument):

    url = StringField(
        required=True
    )

    caption = StringField(
        default=""
    )

    is_cover = BooleanField(
        default=False
    )


# ============================================================
# PROPERTY LOCATION
# ============================================================

class Location(EmbeddedDocument):

    area = StringField(
        required=True
    )

    landmark = StringField(
        default=""
    )

    latitude = FloatField()

    longitude = FloatField()


# ============================================================
# PROPERTY
# ============================================================

class Property(Document):

    property_id = StringField(
        required=True,
        unique=True
    )

    owner_id = StringField(
        required=True
    )

    name = StringField(
        required=True
    )

    caretaker_name = StringField(
        default=""
    )

    caretaker_contact = StringField(
        default=""
    )

    landlord_name = StringField(
        default=""
    )

    landlord_contact = StringField(
        default=""
    )

    description = StringField(
        default="",
        max_length=1000
    )

    location = EmbeddedDocumentField(
        Location,
        required=True
    )

    distance_from_university = FloatField()

    monthly_price = FloatField(
        min_value=0
    )

    semester_price = FloatField(
        min_value=0
    )

    Cost_Sharing = FloatField(
        min_value=0
    )

    amenities = ListField(
        StringField()
    )

    photos = ListField(
        EmbeddedDocumentField(Photo)
    )

    rooms = ListField(
        EmbeddedDocumentField(Room)
    )

    approval_status = StringField(
        choices=[
            "pending",
            "approved",
            "rejected",
        ],
        default="pending"
    )

    status = StringField(
        choices=[
            "active",
            "suspended",
            "inactive",
        ],
        default="active"
    )

    created_at = DateTimeField()

    updated_at = DateTimeField()

    # --------------------------------------------------------
    # NUMBER OF VACANT ROOMS
    # --------------------------------------------------------

    @property
    def vacant_room_count(self):

        return sum(
            1
            for room in self.rooms
            if room.status == "vacant"
        )

    # --------------------------------------------------------
    # MONGODB COLLECTION
    # --------------------------------------------------------

    meta = {
        "collection": "properties"
    }

# ============================================================
# PROPERTY VIEW ANALYTICS
# ============================================================


class PropertyView(Document):

    property_id = StringField(
        required=True
    )

    student_id = StringField(
        default=""
    )

    session_key = StringField(
        default=""
    )

    viewed_at = DateTimeField(
        default=datetime.datetime.now
    )

    meta = {
        "collection": "property_views",

        "indexes": [
            "property_id",
            "student_id",
            "session_key",
            "-viewed_at",

            # Analytics optimization
            {
                "fields": [
                    "property_id",
                    "-viewed_at",
                ]
            },

            {
                "fields": [
                    "student_id",
                    "-viewed_at",
                ]
            },

            {
                "fields": [
                    "session_key",
                    "-viewed_at",
                ]
            },
        ],
    }


# ============================================================
# AVAILABILITY ALERT
# ============================================================

class AvailabilityAlert(Document):

    student_id = StringField(
        required=True
    )

    property_id = StringField(
        required=True
    )

    status = StringField(
        choices=[
            "active",
            "notified",
            "cancelled",
        ],
        default="active"
    )

    created_at = DateTimeField()

    notified_at = DateTimeField()

    meta = {
        "collection": "availability_alerts"
    }




class Favourite(Document):

    student_id = StringField(
        required=True
    )

    property_id = StringField(
        required=True
    )

    created_at = DateTimeField(
        default=datetime.datetime.now
    )

    meta = {
        "collection": "favourites",

        "indexes": [
            {
                "fields": [
                    "student_id",
                    "property_id",
                ],
                "unique": True,
            }
        ],
    }
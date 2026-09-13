from django.urls import path

from . import views


app_name = "properties"


urlpatterns = [

    # ========================================================
    # STUDENT HOME
    # ========================================================

    path(
        "student-home/",
        views.student_home,
        name="student_home",
    ),


    # ========================================================
    # PROPERTY LIST
    # ========================================================

    path(
        "",
        views.property_list,
        name="property_list",
    ),


    # ========================================================
    # OWNER - ADD PROPERTY
    # ========================================================

    path(
        "add-property/",
        views.add_property,
        name="add_property",
    ),


    # ========================================================
    # OWNER - MY PROPERTIES
    # ========================================================

    path(
        "my-properties/",
        views.my_properties,
        name="my_properties",
    ),


    # ========================================================
    # OWNER - ROOMS
    # ========================================================

    path(
        "my-properties/<str:property_id>/rooms/",
        views.manage_rooms,
        name="manage_rooms",
    ),

    path(
        "my-properties/<str:property_id>/rooms/add/",
        views.add_room,
        name="add_room",
    ),

    path(
        "my-properties/<str:property_id>/rooms/<str:room_number>/status/",
        views.update_room_status,
        name="update_room_status",
    ),


    # ========================================================
    # OWNER - PHOTOS
    # ========================================================

    path(
        "my-properties/<str:property_id>/photos/",
        views.manage_photos,
        name="manage_photos",
    ),

    path(
        "my-properties/<str:property_id>/photos/<int:photo_index>/cover/",
        views.set_cover_photo,
        name="set_cover_photo",
    ),

    path(
        "my-properties/<str:property_id>/photos/<int:photo_index>/delete/",
        views.delete_photo,
        name="delete_photo",
    ),


    # ========================================================
    # FAVOURITES
    # ========================================================

    path(
        "favourites/",
        views.favourite_list,
        name="favourite_list",
    ),

    path(
        "<str:property_id>/favourite/add/",
        views.add_favourite,
        name="add_favourite",
    ),

    path(
        "<str:property_id>/favourite/remove/",
        views.remove_favourite,
        name="remove_favourite",
    ),

    # AVAILABILITY NOTIFICATIONS
    

    path(
        "<str:property_id>/notify/",
        views.notify_when_available,
        name="notify_when_available",
    ),


    # ========================================================
    # REPORT PROPERTY
    # ========================================================

   path(
    "property/<str:property_id>/report/",
    views.report_property,
    name="report_property",
),


    # ========================================================
    # PROPERTY COMPARISON
    # ========================================================

    path(
        "compare/",
        views.compare_properties,
        name="compare_properties",
    ),

    path(
        "compare/add/<str:property_id>/",
        views.add_to_compare,
        name="add_to_compare",
    ),

    path(
        "compare/remove/<str:property_id>/",
        views.remove_from_compare,
        name="remove_from_compare",
    ),

    path(
        "compare/clear/",
        views.clear_comparison,
        name="clear_comparison",
    ),


    # ========================================================
    # PROPERTY DETAIL
    # ========================================================
    #
    # KEEP THIS LAST.
    # <str:property_id> is a catch-all route.
    #

    path(
        "<str:property_id>/",
        views.property_detail,
        name="property_detail",
    ),
]

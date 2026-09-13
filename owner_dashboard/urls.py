from django.urls import path
from . import views

app_name = "owner_dashboard"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),
 path(
        "properties/",
        views.my_properties,
        name="my_properties"
    ),
    path(
        "properties/<str:property_id>/rooms/",
        views.manage_rooms,
        name="manage_rooms"
    ),

    path(
        "properties/<str:property_id>/rooms/<str:room_number>/status/",
        views.update_room_status,
        name="update_room_status"
    ),
    path(
        "properties/<str:property_id>/photos/",
        views.manage_photos,
        name="manage_photos"
    ),

    path(
        "properties/<str:property_id>/photos/<int:photo_index>/cover/",
        views.set_cover_photo,
        name="set_cover_photo"
    ),

    path(
        "properties/<str:property_id>/photos/<int:photo_index>/delete/",
        views.delete_photo,
        name="delete_photo"
    ),
 path(
    "analytics/",
    views.analytics,
    name="analytics"
),   
 
path(
    "properties/<str:property_id>/edit/",
    views.edit_property,
    name="edit_property"
),
path( "properties/<str:property_id>/rooms/<str:room_number>/edit/", views.edit_room, name="edit_room" ),

]
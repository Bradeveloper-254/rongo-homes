from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [

    path(
        "",
        views.notification_list,
        name="list"
    ),

    path(
        "<str:notification_id>/read/",
        views.mark_as_read,
        name="mark_as_read"
    ),

    path(
        "mark-all-read/",
        views.mark_all_as_read,
        name="mark_all_read"
    ),
    path(
        "<str:notification_id>/click/",
        views.notification_click,
        name="notification_click"
    ),
]
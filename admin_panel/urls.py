
from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # Owners
    path( "owners/", views.owners, name="owners" ),
    path("owners/<str:user_id>/view/", views.owner_detail, name="owner_detail"),
    path(
        "owners/<str:user_id>/approve/",
        views.approve_owner,
        name="approve_owner"
    ),
    path(
        "owners/<str:user_id>/reject/",
        views.reject_owner,
        name="reject_owner"
    ),
    path(
        "owners/<str:user_id>/suspend/",
        views.suspend_owner,
        name="suspend_owner"
    ),
    path("owners/<str:user_id>/activate/", views.activate_owner, name="activate_owner"),

    # Students
    path(
        "students/",
        views.students,
        name="students"
    ),
    path(
        "students/<str:user_id>/suspend/",
        views.suspend_student,
        name="suspend_student"
    ),
    path(
        "students/<str:user_id>/activate/",
        views.activate_student,
        name="activate_student"
    ),

    # Properties
    path(
        "properties/",
        views.properties,
        name="properties"
    ),
    path(
        "properties/<str:property_id>/approve/",
        views.approve_property,
        name="approve_property"
    ),
    path(
        "properties/<str:property_id>/reject/",
        views.reject_property,
        name="reject_property"
    ),
    path(
        "properties/<str:property_id>/suspend/",
        views.suspend_property,
        name="suspend_property"
    ),
    path(
        "properties/<str:property_id>/activate/",
        views.activate_property,
        name="activate_property"
    ),
    path(
        "properties/<str:property_id>/view/",
        views.view_property,
        name="view_property"
    ),

    # Reports
    path(
        "reports/",
        views.reports,
        name="reports"
    ),
    path(
        "reports/<str:report_id>/resolve/",
        views.resolve_report,
        name="resolve_report"
    ),
    path(
        "reports/<str:report_id>/dismiss/",
        views.dismiss_report,
        name="dismiss_report"
    ),
    path(
        "reports/<str:report_id>/reject/",
        views.reject_report,
        name="reject_report"
    ),

    # Payments
    path(
        "payments/",
        views.payments,
        name="payments"
    ),
    path(
    "reviews/",
    views.reviews,
    name="reviews"
),

path(
    "reviews/<str:review_id>/approve/",
    views.approve_review,
    name="approve_review"
),

path(
    "reviews/<str:review_id>/reject/",
    views.reject_review,
    name="reject_review"
),
path(
    "announcements/send/",
    views.send_announcement,
    name="send_announcement"
),
# Notifications
path(
    "notifications/",
    views.notifications,
    name="notifications"
),

path(
    "notifications/<str:notification_id>/read/",
    views.mark_notification_read,
    name="mark_notification_read"
),

path(
    "notifications/mark-all-read/",
    views.mark_all_notifications_read,
    name="mark_all_notifications_read"
),



]

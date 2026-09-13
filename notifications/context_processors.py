from .models import Notification


def notification_count(request):

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    unread_notifications_count = 0

    if user_id and role in ["student", "owner"]:

        unread_notifications_count = Notification.objects(
            recipient_id=user_id,
            recipient_role=role,
            is_read=False
        ).count()

    return {
        "unread_notifications_count":
            unread_notifications_count
    }
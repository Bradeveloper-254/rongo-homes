from datetime import datetime

from .models import Notification


def create_notification(
    user_id,
    recipient_id,
    recipient_role,
    notification_type,
    title,
    message,
    related_id=None,
):
    return Notification(
        user_id=user_id,
        recipient_id=recipient_id,
        recipient_role=recipient_role,
        notification_type=notification_type,
        title=title,
        message=message,
        related_id=str(related_id) if related_id else None,
        is_read=False,
        created_at=datetime.now(),
    ).save()
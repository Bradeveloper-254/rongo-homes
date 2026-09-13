from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Notification


def notification_list(request):

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return redirect("accounts:login")

    notifications = Notification.objects(
        recipient_id=user_id,
        recipient_role=role
    ).order_by("-created_at")

    unread_count = Notification.objects(
        recipient_id=user_id,
        recipient_role=role,
        is_read=False
    ).count()

    return render(
        request,
        "notifications/notifications.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )


def mark_as_read(request, notification_id):

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return redirect("accounts:login")

    notification = Notification.objects(
        id=notification_id,
        recipient_id=user_id,
        recipient_role=role
    ).first()

    if notification:
        notification.is_read = True
        notification.save()

    return redirect(
        "notifications:list"
    )


def mark_all_as_read(request):

    user_id = request.session.get("user_id")
    role = request.session.get("role")

    if not user_id or not role:
        return redirect("accounts:login")

    Notification.objects(
        recipient_id=user_id,
        recipient_role=role,
        is_read=False
    ).update(
        set__is_read=True
    )

    return redirect(
        "notifications:list"
    )
    
def notification_click(request, notification_id):

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("accounts:login")

    notification = Notification.objects(
        id=notification_id,
        user_id=user_id
    ).first()

    if not notification:
        messages.error(
            request,
            "Notification not found."
        )
        return redirect("accounts:profile")

    # Mark as read
    notification.is_read = True
    notification.save()

    # Follow notification destination
    if notification.link:
        return redirect(notification.link)

    return redirect("accounts:profile")
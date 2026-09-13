from functools import wraps

from django.shortcuts import redirect
from django.contrib import messages

from .models import User


def login_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user_id = request.session.get("user_id")

        if not user_id:

            messages.error(
                request,
                "Please log in to continue."
            )

            return redirect(
                "accounts:login"
            )

        user = User.objects(
            id=user_id
        ).first()

        if not user:

            request.session.flush()

            messages.error(
                request,
                "Your account could not be found."
            )

            return redirect(
                "accounts:login"
            )

        if user.status != "active":

            request.session.flush()

            messages.error(
                request,
                "Your account is not active."
            )

            return redirect(
                "accounts:login"
            )

        request.current_user = user

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


def role_required(required_role):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user_id = request.session.get(
                "user_id"
            )

            if not user_id:

                messages.error(
                    request,
                    "Please log in to continue."
                )

                return redirect(
                    "accounts:login"
                )

            user = User.objects(
                id=user_id
            ).first()

            if not user:

                request.session.flush()

                return redirect(
                    "accounts:login"
                )

            if user.status != "active":

                messages.error(
                    request,
                    "Your account is not active."
                )

                return redirect(
                    "accounts:login"
                )

            if user.role != required_role:

                messages.error(
                    request,
                    "You do not have permission to access this page."
                )

                return redirect(
                    "accounts:profile"
                )

            request.current_user = user

            return view_func(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorator


student_required = role_required("student")

owner_required = role_required("owner")

admin_required = role_required("admin")

from django.urls import path
from . import views


app_name = "accounts"


urlpatterns = [

    # ==============================
    # ACCOUNT
    # ==============================

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    path(
        "terms/",
        views.terms,
        name="terms"
    ),


    # ==============================
    # PASSWORD
    # ==============================

    path(
        "forgot-password/",
        views.forgot_password,
        name="forgot_password"
    ),

    path(
        "reset-password/<str:token>/",
        views.reset_password,
        name="reset_password"
    ),


    # ==============================
    # ADMIN
    # ==============================

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-dashboard/approve/<str:owner_id>/",
        views.approve_owner,
        name="approve_owner"
    ),

    path(
        "admin-dashboard/reject/<str:owner_id>/",
        views.reject_owner,
        name="reject_owner"
    ),

]


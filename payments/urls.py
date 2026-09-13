
from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [

    # PAYMENT HISTORY
    path(
        "history/",
        views.payment_history,
        name="payment_history"
    ),

    # UNLOCKED CONTACTS
    path(
        "unlocked-contacts/",
        views.unlocked_contacts,
        name="unlocked_contacts"
    ),

    # PROPERTY CONTACT UNLOCK
    path(
        "unlock/<str:property_id>/",
        views.unlock_property,
        name="unlock_property"
    ),

    # M-PESA CALLBACK
    path(
        "mpesa/callback/",
        views.mpesa_callback,
        name="mpesa_callback"
    ),

    # PAYMENT STATUS
    path(
        "status/<str:transaction_id>/",
        views.payment_status,
        name="payment_status"
    ),
]


import base64
import uuid
import requests
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import (
    render,
    redirect
)
from django.contrib import messages
from django.http import (
    JsonResponse,
    HttpResponse
)

from .models import Payment
from properties.models import Property


# ============================================================
# HELPERS
# ============================================================

def get_mpesa_base_url():

    if settings.MPESA_ENVIRONMENT == "production":
        return "https://api.safaricom.co.ke"

    return "https://sandbox.safaricom.co.ke"


def normalize_phone_number(phone):

    phone = str(phone).strip()

    # 07XXXXXXXX
    if phone.startswith("07") and len(phone) == 10:
        return "254" + phone[1:]

    # 01XXXXXXXX
    if phone.startswith("01") and len(phone) == 10:
        return "254" + phone[1:]

    # +2547XXXXXXXX
    if phone.startswith("+254"):
        return phone[1:]

    # 2547XXXXXXXX
    if phone.startswith("254") and len(phone) == 12:
        return phone

    return None


def get_mpesa_access_token():

    if not settings.MPESA_CONSUMER_KEY:
        raise ValueError(
            "MPESA_CONSUMER_KEY is not configured."
        )

    if not settings.MPESA_CONSUMER_SECRET:
        raise ValueError(
            "MPESA_CONSUMER_SECRET is not configured."
        )

    url = (
        get_mpesa_base_url()
        + "/oauth/v1/generate"
    )

    response = requests.get(
        url,
        params={
            "grant_type": "client_credentials"
        },
        auth=(
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET
        ),
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    access_token = data.get(
        "access_token"
    )

    if not access_token:
        raise ValueError(
            "Safaricom did not return an access token."
        )

    return access_token


def generate_password(timestamp):

    raw_password = (
        str(settings.MPESA_SHORTCODE)
        + str(settings.MPESA_PASSKEY)
        + str(timestamp)
    )

    return base64.b64encode(
        raw_password.encode("utf-8")
    ).decode("utf-8")


# ============================================================
# UNLOCK PROPERTY
# ============================================================

def unlock_property(request, property_id):

    # --------------------------------------------------------
    # STUDENTS ONLY
    # --------------------------------------------------------

    if request.session.get("role") != "student":

        return redirect(
            "accounts:login"
        )

    student_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # PROPERTY
    # --------------------------------------------------------

    property_obj = Property.objects(
        property_id=property_id,
        approval_status="approved",
        status="active"
    ).first()

    if not property_obj:

        messages.error(
            request,
            "Property not found."
        )

        return redirect(
            "properties:student_home"
        )

    # --------------------------------------------------------
    # ALREADY PAID?
    # --------------------------------------------------------

    existing_payment = Payment.objects(
        student_id=student_id,
        property_id=property_id,
        status="successful"
    ).first()

    if existing_payment:

        messages.info(
            request,
            "You have already unlocked this property."
        )

        return redirect(
            "properties:property_detail",
            property_id=property_id
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
                
            }
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    phone_number = request.POST.get(
        "phone_number",
        ""
    )

    phone_number = normalize_phone_number(
        phone_number
    )

    if not phone_number:

        messages.error(
            request,
            "Please enter a valid Safaricom phone number."
        )

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
            }
        )

    # --------------------------------------------------------
    # CHECK MPESA CONFIGURATION
    # --------------------------------------------------------

    required_settings = {
        "MPESA_CONSUMER_KEY":
            settings.MPESA_CONSUMER_KEY,

        "MPESA_CONSUMER_SECRET":
            settings.MPESA_CONSUMER_SECRET,

        "MPESA_SHORTCODE":
            settings.MPESA_SHORTCODE,

        "MPESA_PASSKEY":
            settings.MPESA_PASSKEY,

        "MPESA_CALLBACK_URL":
            settings.MPESA_CALLBACK_URL,
    }

    missing = [
        key
        for key, value in required_settings.items()
        if not value
    ]

    if missing:

        messages.error(
            request,
            "M-PESA configuration is incomplete. "
            "Missing: "
            + ", ".join(missing)
        )

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
            }
        )

    # --------------------------------------------------------
    # GENERATE INTERNAL TRANSACTION
    # --------------------------------------------------------

    transaction_id = (
        "RHG-"
        + uuid.uuid4().hex[:10].upper()
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    # --------------------------------------------------------
    # CREATE PENDING PAYMENT
    # --------------------------------------------------------

    payment = Payment(
        transaction_id=transaction_id,
        student_id=student_id,
        property_id=property_id,
        amount=1,
        currency="KES",
        payment_method="mpesa",
        payment_type="contact_unlock",
        status="pending",
        phone_number=phone_number,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    payment.save()


# ============================================================
# GET ACCESS TOKEN
# ============================================================

    try:
        access_token = get_mpesa_access_token()

    except Exception as exc:

        payment.status = "failed"
        payment.result_description = str(exc)
        payment.updated_at = datetime.utcnow()
        payment.save()

        messages.error(
            request,
            "Unable to connect to M-PESA. "
            "Please try again."
        )

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
            }
        )


    # ============================================================
    # STK PUSH
    # ============================================================

    stk_url = (
        get_mpesa_base_url()
        + "/mpesa/stkpush/v1/processrequest"
    )

    password = generate_password(
        timestamp
    )

    payload = {

        "BusinessShortCode":
            settings.MPESA_SHORTCODE,

        "Password":
            password,

        "Timestamp":
            timestamp,

        "TransactionType":
            "CustomerPayBillOnline",

        "Amount":
            int(payment.amount),

        "PartyA":
            phone_number,

        "PartyB":
            settings.MPESA_SHORTCODE,

        "PhoneNumber":
            phone_number,

        "CallBackURL":
            settings.MPESA_CALLBACK_URL,

        "AccountReference":
            transaction_id,

        "TransactionDesc":
            settings.MPESA_TRANSACTION_DESC,
    }


    headers = {
        "Authorization":
            "Bearer " + access_token,

        "Content-Type":
            "application/json"
    }


    try:

        response = requests.post(
            stk_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        response_data = response.json()

    except (
        requests.exceptions.RequestException,
        ValueError
    ):

        payment.status = "failed"
        payment.result_description = (
            "M-PESA request failed or returned "
            "an invalid response."
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        messages.error(
            request,
            "Could not contact M-PESA. "
            "Please try again."
        )

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
            }
        )


    # ============================================================
    # HANDLE SAFARICOM RESPONSE
    # ============================================================

    response_code = str(
        response_data.get(
            "ResponseCode",
            ""
        )
    ).strip()


    if response_code != "0":

        payment.status = "failed"

        payment.result_code = response_code

        payment.result_description = (
            response_data.get(
                "ResponseDescription",
                "M-PESA request failed."
            )
        )

        payment.updated_at = datetime.utcnow()

        payment.save()

        messages.error(
            request,
            response_data.get(
                "ResponseDescription",
                "M-PESA payment request failed."
            )
        )

        return render(
            request,
            "payments/unlock.html",
            {
                "property": property_obj,
                "unlock_fee": 1
            }
        )


    # ============================================================
    # SAVE STK IDENTIFIERS
    # ============================================================

    payment.merchant_request_id = (
        response_data.get(
            "MerchantRequestID"
        )
    )

    payment.checkout_request_id = (
        response_data.get(
            "CheckoutRequestID"
        )
    )

    payment.result_description = (
        response_data.get(
            "ResponseDescription",
            "STK Push sent successfully."
        )
    )

    payment.updated_at = datetime.utcnow()

    payment.save()


    # ============================================================
    # PAYMENT WAITING PAGE
    # ============================================================

    return render(
        request,
        "payments/payment_pending.html",
        {
            "payment": payment,
            "property": property_obj
        }
    )




# ============================================================
# PAYMENT HISTORY
# ============================================================

def payment_history(request):
    if request.session.get("role") != "student":
        return redirect("accounts:login")

    student_id = request.session.get("user_id")

    payments = Payment.objects(
        student_id=student_id
    ).order_by("-created_at")

    return render(
        request,
        "payments/payment_history.html",
        {
            "payments": payments,
        }
    )


# ============================================================
# UNLOCKED CONTACTS
# ============================================================

def unlocked_contacts(request):
    if request.session.get("role") != "student":
        return redirect("accounts:login")

    student_id = request.session.get("user_id")

    unlocked_payments = Payment.objects(
        student_id=student_id,
        status="successful",
        payment_type="contact_unlock"
    ).order_by("-created_at")

    contacts = []

    for payment in unlocked_payments:

        property_obj = Property.objects(
            property_id=payment.property_id
        ).first()

        if property_obj:
            contacts.append(
                {
                    "property": property_obj,
                    "payment": payment,
                }
            )

    return render(
        request,
        "payments/unlocked_contacts.html",
        {
            "contacts": contacts,
        }
    )



# ============================================================
# MPESA CALLBACK
# ============================================================

@csrf_exempt
def mpesa_callback(request):
    """
    Receive and process M-PESA STK callback.

    Security rules:
    - Only POST is accepted.
    - Unknown checkout requests are ignored.
    - Only pending payments can change state.
    - Successful callbacks must contain a receipt.
    - Callback amount must match the server-created payment amount.
    - Duplicate callbacks are harmless.
    - A receipt already attached to another successful payment is rejected.
    - Sensitive payment details are not printed to logs.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc": "POST required."
            },
            status=405
        )

    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc": "Invalid JSON."
            },
            status=400
        )

    callback = (
        payload.get("Body", {})
        .get("stkCallback", {})
    )

    if not callback:
        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc": "Invalid callback payload."
            },
            status=400
        )

    checkout_request_id = callback.get(
        "CheckoutRequestID"
    )

    result_code = callback.get(
        "ResultCode"
    )

    result_description = callback.get(
        "ResultDesc",
        ""
    )

    if not checkout_request_id:
        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc": "Missing CheckoutRequestID."
            },
            status=400
        )

    payment = Payment.objects(
        checkout_request_id=checkout_request_id
    ).first()

    if not payment:
        # Do not reveal whether a payment exists.
        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    # --------------------------------------------------------
    # IDEMPOTENCY
    # --------------------------------------------------------

    # Once a payment is successful, repeated callbacks
    # must not change or duplicate it.
    if payment.status == "successful":
        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Already processed."
            }
        )

    # --------------------------------------------------------
    # SAVE CALLBACK RESULT
    # --------------------------------------------------------

    payment.result_code = str(
        result_code
    )

    payment.result_description = (
        str(result_description)[:500]
    )

    # --------------------------------------------------------
    # FAILED / CANCELLED PAYMENT
    # --------------------------------------------------------

    if result_code != 0:
        payment.status = "failed"
        payment.updated_at = datetime.utcnow()
        payment.save()

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    # --------------------------------------------------------
    # SUCCESS CALLBACK VALIDATION
    # --------------------------------------------------------

    callback_metadata = (
        callback.get(
            "CallbackMetadata",
            {}
        )
    )

    metadata_items = (
        callback_metadata.get(
            "Item",
            []
        )
    )

    metadata = {}

    for item in metadata_items:
        name = item.get("Name")

        if name:
            metadata[name] = item.get("Value")

    mpesa_receipt = metadata.get(
        "MpesaReceiptNumber"
    )

    callback_amount = metadata.get(
        "Amount"
    )

    callback_phone = metadata.get(
        "PhoneNumber"
    )

    # A successful payment must have an M-PESA receipt.
    if not mpesa_receipt:
        payment.status = "failed"
        payment.result_description = (
            "Successful callback missing M-PESA receipt."
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    # --------------------------------------------------------
    # AMOUNT VALIDATION
    # --------------------------------------------------------

    try:
        callback_amount = float(
            callback_amount
        )
    except (
        TypeError,
        ValueError
    ):
        callback_amount = None

    if callback_amount is None:
        payment.status = "failed"
        payment.result_description = (
            "Callback missing valid payment amount."
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    if callback_amount != float(payment.amount):
        payment.status = "failed"
        payment.result_description = (
            "Callback amount does not match "
            "the payment amount."
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    # --------------------------------------------------------
    # DUPLICATE RECEIPT PROTECTION
    # --------------------------------------------------------

    existing_receipt = Payment.objects(
        mpesa_reference=str(mpesa_receipt),
        status="successful"
    ).first()

    if (
        existing_receipt
        and str(existing_receipt.id)
        != str(payment.id)
    ):
        payment.status = "failed"
        payment.result_description = (
            "M-PESA receipt already used."
        )
        payment.updated_at = datetime.utcnow()
        payment.save()

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )

    # --------------------------------------------------------
    # OPTIONAL PHONE VALIDATION
    # --------------------------------------------------------

    if callback_phone and payment.phone_number:

        callback_phone = str(
            callback_phone
        ).replace("+", "").replace(" ", "")

        stored_phone = str(
            payment.phone_number
        ).replace("+", "").replace(" ", "")

        if callback_phone != stored_phone:
            payment.status = "failed"
            payment.result_description = (
                "Callback phone number does not "
                "match the payment."
            )
            payment.updated_at = datetime.utcnow()
            payment.save()

            return JsonResponse(
                {
                    "ResultCode": 0,
                    "ResultDesc": "Accepted"
                }
            )

    # --------------------------------------------------------
    # FINAL SUCCESS
    # --------------------------------------------------------

    payment.mpesa_reference = str(
        mpesa_receipt
    )

    payment.status = "successful"
    payment.updated_at = datetime.utcnow()

    payment.save()

    return JsonResponse(
        {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }
    )

# ============================================================
# PAYMENT STATUS
# ============================================================

def payment_status(
    request,
    transaction_id
):

    if request.session.get("role") != "student":

        return JsonResponse(
            {
                "error": "Unauthorized"
            },
            status=403
        )

    student_id = request.session.get(
        "user_id"
    )

    payment = Payment.objects(
        transaction_id=transaction_id,
        student_id=student_id
    ).first()

    if not payment:

        return JsonResponse(
            {
                "error": "Payment not found"
            },
            status=404
        )

    return JsonResponse({

        "status":
            payment.status,

        "mpesa_reference":
            payment.mpesa_reference or "",

        "result_description":
            payment.result_description or "",

        "property_id":
            payment.property_id,

        "transaction_id":
            payment.transaction_id

    })


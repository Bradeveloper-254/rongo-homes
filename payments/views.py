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

    # --------------------------------------------------------
    # GET ACCESS TOKEN
    # --------------------------------------------------------

    try:

        access_token = (
            get_mpesa_access_token()
        )

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

    # --------------------------------------------------------
    # STK PUSH
    # --------------------------------------------------------

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

        response_data = response.json()

    except Exception as exc:

        payment.status = "failed"
        payment.result_description = str(exc)
        payment.updated_at = datetime.utcnow()
        payment.save()

        messages.error(
            request,
            "Could not contact M-PESA. Please try again."
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
    # HANDLE SAFARICOM RESPONSE
    # --------------------------------------------------------

    response_code = response_data.get(
        "ResponseCode"
    )

    if response_code != "0":

        payment.status = "failed"

        payment.result_code = str(
            response_data.get(
                "ResponseCode",
                ""
            )
        )

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

    # --------------------------------------------------------
    # SAVE STK IDENTIFIERS
    # --------------------------------------------------------

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
    
    print(
    "\nSTK PUSH CREATED"
    )

    print(
        "Transaction ID:",
        payment.transaction_id
    )

    print(
        "MerchantRequestID:",
        payment.merchant_request_id
    )

    print(
        "CheckoutRequestID:",
        payment.checkout_request_id
    )

    print(
        "Callback URL:",
        settings.MPESA_CALLBACK_URL
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # PAYMENT WAITING PAGE
    # --------------------------------------------------------

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

    print("\n" + "=" * 70)
    print("M-PESA CALLBACK RECEIVED")
    print("=" * 70)

    # Safaricom sends the callback using POST
    if request.method != "POST":
        print("Callback received using GET")
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Callback endpoint is active."
        })

    # --------------------------------------------------------
    # READ JSON BODY
    # --------------------------------------------------------

    try:
        data = json.loads(request.body)

        print("CALLBACK DATA:")
        print(json.dumps(data, indent=4))

    except json.JSONDecodeError as exc:

        print("INVALID JSON:", exc)

        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Invalid JSON."
        }, status=400)

    # --------------------------------------------------------
    # EXTRACT STK CALLBACK
    # --------------------------------------------------------

    try:

        callback = (
            data
            .get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = (
            callback.get("CheckoutRequestID")
        )

        result_code = callback.get(
            "ResultCode"
        )

        result_description = callback.get(
            "ResultDesc",
            ""
        )

        print("CheckoutRequestID:", checkout_request_id)
        print("ResultCode:", result_code)
        print("ResultDesc:", result_description)

        # ----------------------------------------------------
        # FIND PAYMENT
        # ----------------------------------------------------

        if not checkout_request_id:

            print("No CheckoutRequestID received.")

            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            })

        payment = Payment.objects(
            checkout_request_id=checkout_request_id
        ).first()

        if not payment:

            print(
                "PAYMENT NOT FOUND FOR CHECKOUT REQUEST:",
                checkout_request_id
            )

            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            })

        print(
            "PAYMENT FOUND:",
            payment.transaction_id
        )

        # ----------------------------------------------------
        # SAVE RESULT INFORMATION
        # ----------------------------------------------------

        payment.result_code = str(
            result_code
        )

        payment.result_description = (
            result_description
        )

        payment.updated_at = datetime.utcnow()

        # ----------------------------------------------------
        # SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        if result_code == 0:

            print("PAYMENT SUCCESSFUL")

            callback_metadata = (
                callback.get(
                    "CallbackMetadata",
                    {}
                )
            )

            items = callback_metadata.get(
                "Item",
                []
            )

            metadata = {}

            for item in items:

                name = item.get("Name")
                value = item.get("Value")

                if name:
                    metadata[name] = value

            # -----------------------------------------------
            # MPESA RECEIPT
            # -----------------------------------------------

            mpesa_receipt = metadata.get(
                "MpesaReceiptNumber"
            )

            if mpesa_receipt:

                payment.mpesa_reference = str(
                    mpesa_receipt
                )

                print(
                    "M-PESA RECEIPT:",
                    mpesa_receipt
                )

            # -----------------------------------------------
            # FINAL PAYMENT STATUS
            # -----------------------------------------------

            payment.status = "successful"

            print(
                "PAYMENT STATUS CHANGED TO SUCCESSFUL"
            )

        # ----------------------------------------------------
        # FAILED / CANCELLED PAYMENT
        # ----------------------------------------------------

        else:

            payment.status = "failed"

            print(
                "PAYMENT FAILED:",
                result_description
            )

        # ----------------------------------------------------
        # SAVE PAYMENT
        # ----------------------------------------------------

        payment.updated_at = datetime.utcnow()

        payment.save()

        print(
            "PAYMENT SAVED:",
            payment.transaction_id,
            payment.status
        )

        print("=" * 70)
        print("CALLBACK PROCESSING COMPLETE")
        print("=" * 70)

        # ----------------------------------------------------
        # ACKNOWLEDGE SAFARICOM
        # ----------------------------------------------------

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })

    except Exception as exc:

        print(
            "M-PESA CALLBACK ERROR:",
            exc
        )

        # Always acknowledge the callback so Safaricom
        # does not keep retrying the request.

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })



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
                "error":
                    "Unauthorized"
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
                "error":
                    "Payment not found"
            },
            status=404
        )

    return JsonResponse(
        {
            "status":
                payment.status,

            "mpesa_reference":
                payment.mpesa_reference or "",

            "result_description":
                payment.result_description or "",

            "property_id":
                payment.property_id
        }
    )
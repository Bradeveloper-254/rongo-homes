
from django.shortcuts import render, redirect

from reports.models import Report
from properties.models import Property


# ============================================================
# MY REPORTS
# ============================================================

def my_reports(request):

    if request.session.get("role") != "student":
        return redirect("accounts:login")

    student_id = request.session.get("user_id")

    reports = Report.objects(
        student_id=student_id
    ).order_by("-created_at")

    reported_properties = []

    for report in reports:

        property_obj = Property.objects(
            property_id=report.property_id
        ).first()

        reported_properties.append(
            {
                "report": report,
                "property": property_obj,
            }
        )

    return render(
        request,
        "reports/my_reports.html",
        {
            "reported_properties": reported_properties,
        }
    )


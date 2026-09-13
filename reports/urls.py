
from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [

    path(
        "my-reports/",
        views.my_reports,
        name="my_reports"
    ),

]


"""
URL configuration for rongo_homes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rongo_homes import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path("test-mongodb/", test_mongodb),
    path("", RedirectView.as_view(url='/properties/', permanent=False), name='home'),
    path("accounts/", include("accounts.urls")),
    path(
        "admin-panel/",
        include("admin_panel.urls")
    ),
    path(
        "properties/",
        include(("properties.urls", "properties"), namespace="properties"),
    ),
    path(
        "payments/",
        include("payments.urls")
    ),
    path(
        "reviews/",
        include("reviews.urls")
    ),
   path(
    "owner-dashboard/",
    include(
        ("owner_dashboard.urls", "owner_dashboard"),
        namespace="owner_dashboard",
    ),
),
   path(
    "notifications/",
    include("notifications.urls")
),
   path("reports/", include("reports.urls")),

]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
)
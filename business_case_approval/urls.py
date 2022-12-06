from django.contrib import admin
from django.urls import include, path

from business_case_approval.application import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("application/<int:application_id>/", views.page_view, name="pages-index"),
    path("application/<int:application_id>/download", views.page_view, name="download-pdf"),
    path("application/<int:application_id>/<str:page_name>", views.page_view, name="pages"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]

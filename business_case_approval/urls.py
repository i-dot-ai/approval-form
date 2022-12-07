from django.contrib import admin
from django.urls import include, path

from business_case_approval.application import utils, views

urlpatterns = [
    path("", utils.index_view, name="index"),
    path("application/<int:application_id>/", utils.page_view, name="pages-index"),
    path("application/<int:application_id>/download/", views.download_pdf, name="download-pdf"),
    path("application/<int:application_id>/print/", views.print_view, name="print"),
    path("application/<int:application_id>/<str:page_name>/", utils.page_view, name="pages"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]

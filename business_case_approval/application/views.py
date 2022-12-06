import io

import pdfkit
from django.forms.models import model_to_dict
from django.http import FileResponse
from django.shortcuts import render
from django.utils.text import slugify

from . import models, utils

utils.SimplePage(title="Intro")
utils.FormPage(title="Name", field_names=("name",))
utils.FormPage(title="Exemption", field_names=("hrbp", "grade", "title"), extra_data={"grades": models.Grades.options})
utils.FormPage(title="Establishment", field_names=("establishment",))
utils.FormPage(title="Impact", field_names=("impact_statement",))
utils.FormPage(
    title="justification",
    field_names=("ddat_role", "ddat_family", "funding_source", "recruitment_type", "recruitment_mechanism"),
    extra_data={
        "ddat_families": models.DDATFamilies.options,
        "funding_sources": models.FundingSource.options,
        "recruitment_types": models.RecruitmentTypes.options,
        "recruitment_mechanisms": models.RecruitmentMechanisms.options,
    },
)
utils.FormPage(
    title="Location",
    field_names=("location_strategy", "locations", "london_reason"),
    extra_data={"london_reasons": models.LondonReasons.options, "locations": models.Locations.options},
)
utils.FormPage(title="SCS roles", field_names=("scs_adverts", "scs_assignments_lengths"))


def register(title):
    def _inner(func):
        page = utils.ViewPage(title, func)
        return page

    return _inner


@register("End")
def end_view(request, url_data):
    application_id = url_data["application_id"]
    application = models.Application.objects.get(pk=application_id)
    data = model_to_dict(application)
    input_url = f"http://localhost:8010/application/{application_id}/print"
    output_filename = "/tmp/applicaton_{application_id}.pdf"
    pdf_data = pdfkit.from_url(input_url, output_filename)
    application.pdf = pdf_data
    application.save()
    return render(request, "end.pug", {**data})


def download_pdf(request, application_id):
    application = models.Application.objects.get(pk=application_id)
    filename = slugify(f"application_{application_id}_{application.name}.pdf")
    filelike = io.BytesIO(application.pdf)
    response = FileResponse(filelike, as_attachment=True, filename=filename)
    return response

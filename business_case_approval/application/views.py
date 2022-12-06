import io

import pdfkit
from django import forms
from django.forms.models import model_to_dict
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.text import slugify

from . import models

page_map = {}


def index_view(request):
    if request.method == "POST":
        user = request.user
        application = models.Application(user=user)
        application.save()
        return redirect(page_view, application_id=application.id)
    return render(request, "index.pug")


def make_url(application_id, page_name):
    if not page_name:
        return None
    return reverse("pages", args=(application_id, page_name))


def page_view(request, application_id, page_name="intro"):
    if page_name not in page_map:
        raise Http404()

    page_name_order = tuple(page_map.keys())

    index = page_name_order.index(page_name)
    prev_page = index and page_name_order[index - 1] or None
    next_page = (index < len(page_name_order) - 1) and page_name_order[index + 1] or None
    prev_url = make_url(application_id, prev_page)
    this_url = make_url(application_id, page_name)
    next_url = make_url(application_id, next_page)

    pages = tuple(
        {
            "slug": _p.slug,
            "url": make_url(application_id, _p.slug),
            "title": _p.title,
            "completed": page_name_order.index(_p.slug) < index,
            "current": _p.slug == page_name,
        }
        for _p in page_map.values()
    )

    url_data = {
        "pages": pages,
        "application_id": application_id,
        "page_name": page_name,
        "index": index,
        "prev_page": prev_page,
        "next_page": next_page,
        "prev_url": prev_url,
        "this_url": this_url,
        "next_url": next_url,
    }
    return page_map[page_name].view(request, url_data)


class FormPage:
    def __init__(self, title, field_names, extra_data=None):
        self.title = title
        self.slug = slugify(title)
        self.field_names = field_names
        self.template_name = f"{self.slug}.pug"
        self.extra_data = extra_data or {}

        class _Form(forms.ModelForm):
            class Meta:
                model = models.Application
                fields = field_names

        self.form_class = _Form
        page_map[self.slug] = self

    def view(self, request, url_data):
        application_id = url_data["application_id"]
        application = models.Application.objects.get(pk=application_id)
        if request.method == "POST":
            form = self.form_class(request.POST, instance=application)
            if form.is_valid():
                form.save()
                return redirect(url_data["next_url"])
            else:
                data = request.POST
                errors = form.errors
        else:
            data = model_to_dict(application)
            errors = {}
        return render(request, self.template_name, {"errors": errors, "data": data, **url_data, **self.extra_data})


class SimplePage:
    def __init__(self, title, extra_data=None):
        self.title = title
        self.slug = slugify(title)
        self.extra_data = extra_data or {}
        page_map[self.slug] = self

    def view(self, request, url_data):
        return render(request, f"{self.slug}.pug", {**url_data})


class ViewPage:
    def __init__(self, title, view, extra_data=None):
        self.title = title
        self.slug = slugify(title)
        self.extra_data = extra_data or {}
        page_map[self.slug] = self
        self.view = view


SimplePage(title="Intro")
FormPage(title="Name", field_names=("name",))
FormPage(title="Exemption", field_names=("hrbp", "grade", "title"), extra_data={"grades": models.Grades.options})
FormPage(title="Establishment", field_names=("establishment",))
FormPage(title="Impact", field_names=("impact_statement",))
FormPage(
    title="justification",
    field_names=("ddat_role", "ddat_family", "funding_source", "recruitment_type", "recruitment_mechanism"),
    extra_data={
        "ddat_families": models.DDATFamilies.options,
        "funding_sources": models.FundingSource.options,
        "recruitment_types": models.RecruitmentTypes.options,
        "recruitment_mechanisms": models.RecruitmentMechanisms.options,
    },
)
FormPage(
    title="Location",
    field_names=("location_strategy", "locations", "london_reason"),
    extra_data={"london_reasons": models.LondonReasons.options, "locations": models.Locations.options},
)
FormPage(title="SCS roles", field_names=("scs_adverts", "scs_assignments_lengths"))


def register(title):
    def _inner(func):
        page = ViewPage(title, func)
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

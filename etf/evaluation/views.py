import io

import pdfkit
from django import forms
from django.forms.models import model_to_dict
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.text import slugify

from . import models

page_order = (
    "intro",
    "name",
    "description",
    "end",
)

view_map = {}


def register(name):
    def _inner(func):
        view_map[name] = func
        return func

    return _inner


def index_view(request):
    if request.method == "POST":
        user = request.user
        evaluation = models.Evaluation(user=user)
        evaluation.save()
        return redirect(page_view, evaluation_id=evaluation.id)
    return render(request, "index.pug")


def make_url(evaluation_id, page_name):
    if not page_name:
        return None
    return reverse("pages", args=(evaluation_id, page_name))


def page_view(request, evaluation_id, page_name="intro"):
    if page_name not in page_order:
        raise Http404()

    index = page_order.index(page_name)
    prev_page = index and page_order[index - 1] or None
    next_page = (index < len(page_order) - 1) and page_order[index + 1] or None
    prev_url = make_url(evaluation_id, prev_page)
    this_url = make_url(evaluation_id, page_name)
    next_url = make_url(evaluation_id, next_page)

    url_data = {
        "evaluation_id": evaluation_id,
        "page_name": page_name,
        "index": index,
        "prev_page": prev_page,
        "next_page": next_page,
        "prev_url": prev_url,
        "this_url": this_url,
        "next_url": next_url,
    }
    return view_map[page_name](request, url_data)


def _create_form_page_response(request, url_data, form_class, template_name, extra_data=None):
    if not extra_data:
        extra_data = {}
    evaluation_id = url_data["evaluation_id"]
    evaluation = models.Evaluation.objects.get(pk=evaluation_id)
    if request.method == "POST":
        form = form_class(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            return redirect(url_data["next_url"])
        else:
            data = request.POST
            errors = form.errors
    else:
        data = model_to_dict(evaluation)
        errors = {}
    return render(request, template_name, {"errors": errors, "data": data, **url_data, **extra_data})


def create_form_view(name, field_names, extra_data=None):
    if not extra_data:
        extra_data = {}

    class _Form(forms.ModelForm):
        class Meta:
            model = models.Evaluation
            fields = field_names

    @register(name)
    def _view(request, url_data):
        return _create_form_page_response(
            request, url_data, form_class=_Form, template_name=f"{name}.pug", extra_data=extra_data
        )


def create_simple_view(name, extra_data=None):
    @register(name)
    def _view(request, url_data):
        return render(request, f"{name}.pug", {**url_data})


create_simple_view("intro")
create_form_view("name", ("name",))
create_form_view("exemption", ("hrbp", "grade", "title"), extra_data={"grades": models.Grades.options})
create_simple_view("end")
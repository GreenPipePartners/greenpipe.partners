"""Daily, print-friendly schedules using the existing report Gist publishing flow."""

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .gists import GistError, load_report_gist
from .models import Report


def _days(customer):
    return Report.objects.filter(
        customer=customer, report_type=Report.ReportType.SCHEDULE
    ).order_by("start_date", "gist_id")


def _response(request, context):
    response = render(request, "portal/schedule.html", context)
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "no-referrer"
    response["Cache-Control"] = "private, no-store"
    return response


def index(request):
    return _response(request, {"schedule_title": "Daily schedules", "pages": []})


def detail(request, customer, gist_id):
    selected = get_object_or_404(_days(customer), gist_id=gist_id)
    return _render_days(request, customer, selected)


def all_days(request, customer, access_key):
    selected = get_object_or_404(_days(customer), gist_id=access_key)
    return _render_days(request, customer, selected, show_all=True)


def _render_days(request, customer, selected, show_all=False):
    days = list(_days(customer))
    position = next(index for index, day in enumerate(days) if day.pk == selected.pk)
    pages = []
    for day in days if show_all else [selected]:
        key = f"schedule-gist:{day.gist_id}"
        document = cache.get(key)
        if document is None:
            try:
                document = load_report_gist(day.gist_id)
            except GistError as exc:
                raise Http404(str(exc)) from exc
            cache.set(key, document, timeout=60)
        pages.append({"day": day, "html": document["document_html"]})

    return _response(
        request,
        {
            "schedule_title": selected.customer_name or customer,
            "days": days,
            "pages": pages,
            "selected": None if show_all else selected,
            "show_all": show_all,
            "previous_day": days[position - 1] if position else None,
            "next_day": days[position + 1] if position + 1 < len(days) else None,
            "all_url": reverse(
                "portal:schedule_all",
                kwargs={"customer": customer, "access_key": days[0].gist_id},
            ),
        },
    )

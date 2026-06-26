from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import content_disposition_header

from .gists import GistError, load_report_csv, load_report_gist
from .models import Report


def home(request):
    return render(request, "portal/home.html")


def logo(request):
    logo_path = settings.BASE_DIR / "logo_hollow.png"
    if not logo_path.exists():
        raise Http404("Logo asset not found.")
    return FileResponse(logo_path.open("rb"), content_type="image/png")


def health(request):
    return JsonResponse({"status": "ok"})


def docs(request):
    return redirect("/docs/flux/latest/", permanent=False)


def about(request):
    return render(request, "portal/about.html")


def flux_docs_latest(request):
    return redirect("/docs/flux/0.1.0/", permanent=False)


def flux_docs_file(request, version, docs_path=""):
    root = _flux_docs_root(version)
    requested_path = docs_path or "index.html"
    file_path = _published_file(root, requested_path)
    if file_path.is_dir():
        file_path = _published_file(root, requested_path, "index.html")
    return FileResponse(file_path.open("rb"))


def release_typo_redirect(request, artifact_path):
    return redirect(f"/release/{artifact_path}", permanent=True)


def release_file(request, artifact_path):
    root = settings.GREENPIPE_PUBLISH_ROOT / "release"
    file_path = _published_file(root, artifact_path)
    if file_path.is_dir():
        raise Http404("Published file not found.")
    return FileResponse(file_path.open("rb"))


def report_detail(request, customer, gist_id):
    report = Report.objects.filter(customer=customer, gist_id=gist_id).first()
    if not report:
        raise Http404("Report not found.")

    try:
        gist_report = load_report_gist(report.gist_id)
    except GistError as exc:
        raise Http404(str(exc)) from exc
    _add_csv_download_urls(report, gist_report)

    return render(
        request,
        "portal/report_detail.html",
        {
            "report": report,
            "customer": report.customer,
            "gist_report": gist_report,
            "report_heading": _report_heading(report, gist_report),
            "customer_reports_url": _customer_reports_url(report),
        },
    )


def customer_reports(request, customer, access_key):
    if not Report.objects.filter(customer=customer, gist_id=access_key).exists():
        raise Http404("Report list not found.")

    reports = Report.objects.filter(customer=customer)
    return render(
        request,
        "portal/report_list.html",
        {
            "customer": customer,
            "weekly_reports": [
                _report_list_item(report)
                for report in reports.filter(report_type=Report.ReportType.WEEKLY).order_by(
                    "-end_date", "-start_date", "-created_at"
                )
            ],
            "engineering_reports": [
                _report_list_item(report)
                for report in reports.filter(report_type=Report.ReportType.ENGINEERING).order_by("-created_at")
            ],
        },
    )


def report_csv_download(request, customer, gist_id, filename):
    report = Report.objects.filter(customer=customer, gist_id=gist_id).first()
    if not report:
        raise Http404("Report not found.")

    try:
        csv_content = load_report_csv(report.gist_id, filename)
    except GistError as exc:
        raise Http404(str(exc)) from exc

    response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = content_disposition_header(True, filename)
    return response


def _report_heading(report, gist_report):
    if report.title:
        return report.title
    if report.report_type == Report.ReportType.ENGINEERING:
        return gist_report.get("description") or "Engineering Report"
    if report.start_date and report.end_date:
        return ""
    return "Weekly Report"


def _add_csv_download_urls(report, gist_report):
    for csv_file in gist_report.get("csvs", []):
        csv_file["download_url"] = reverse(
            "portal:report_csv_download",
            kwargs={
                "customer": report.customer,
                "gist_id": report.gist_id,
                "filename": csv_file["filename"],
            },
        )


def _customer_reports_url(report):
    return reverse(
        "portal:customer_reports",
        kwargs={"customer": report.customer, "access_key": report.gist_id},
    )


def _report_list_item(report):
    return {
        "title": _report_list_title(report),
        "url": report.get_absolute_url(),
        "meta": _report_list_meta(report),
    }


def _report_list_title(report):
    if report.title:
        return report.title
    if report.report_type == Report.ReportType.ENGINEERING:
        return "Engineering Report"
    return "Weekly Report"


def _report_list_meta(report):
    if report.start_date and report.end_date:
        return f"{_format_report_date(report.start_date)} to {_format_report_date(report.end_date)}"
    if report.customer_name:
        return f"Prepared for {report.customer_name}"
    return ""


def _format_report_date(value):
    return f"{value:%B} {value.day}, {value:%Y}"


def _flux_docs_root(version):
    published_root = settings.GREENPIPE_PUBLISH_ROOT / "docs" / "flux" / version
    if published_root.exists():
        return published_root

    local_root = settings.BASE_DIR / ".runtime" / "site"
    if version == "0.1.0" and local_root.exists():
        return local_root

    return published_root


def _published_file(root, *parts):
    root = root.resolve()
    file_path = root.joinpath(*parts).resolve()
    if file_path != root and root not in file_path.parents:
        raise Http404("Published file not found.")
    if not file_path.exists():
        raise Http404("Published file not found.")
    return file_path

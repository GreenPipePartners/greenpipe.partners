from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render

from .gists import GistError, load_report_gist
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

    return render(
        request,
        "portal/report_detail.html",
        {
            "report": report,
            "customer": report.customer,
            "gist_report": gist_report,
        },
    )


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

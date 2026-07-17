from django.urls import path, re_path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("fluxy/", views.fluxy, name="fluxy"),
    path("logo_hollow.png", views.logo, name="logo"),
    path("health/", views.health, name="health"),
    path("docs/", views.docs, name="docs"),
    path("about/", views.about, name="about"),
    path("raft/", views.raft, name="raft"),
    path("agentlab/", views.agentlab, name="agentlab"),
    path("agentlabs/", views.agentlabs, name="agentlabs"),
    path("docs/flux/latest/", views.flux_docs_latest, name="flux_docs_latest"),
    path("docs/flux/<str:version>/", views.flux_docs_file, name="flux_docs_index"),
    path("docs/flux/<str:version>/<path:docs_path>", views.flux_docs_file, name="flux_docs_file"),
    path("release/", views.release_index, name="release_index"),
    re_path(
        r"^release/(?P<topic>[^/]+)/(?P<release_date>\d{4}-\d{2}-\d{2})/csv/(?P<filename>.+)$",
        views.release_csv_download,
        name="release_csv_download",
    ),
    re_path(
        r"^release/(?P<topic>[^/]+)/(?P<release_date>\d{4}-\d{2}-\d{2})$",
        views.release_detail,
        name="release_detail",
    ),
    path("release/<path:artifact_path>", views.release_file, name="release_file"),
    path("realease/<path:artifact_path>", views.release_typo_redirect, name="release_typo_redirect"),
    path(
        "reports/<str:customer>/<slug:gist_id>/csv/<path:filename>",
        views.report_csv_download,
        name="report_csv_download",
    ),
    path("reports/<str:customer>/all/<slug:access_key>", views.customer_reports, name="customer_reports"),
    path("reports/<str:customer>/<slug:gist_id>", views.report_detail, name="report_detail"),
]

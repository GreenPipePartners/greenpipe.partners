from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("logo_hollow.png", views.logo, name="logo"),
    path("health/", views.health, name="health"),
    path("docs/", views.docs, name="docs"),
    path("about/", views.about, name="about"),
    path("docs/flux/latest/", views.flux_docs_latest, name="flux_docs_latest"),
    path("docs/flux/<str:version>/", views.flux_docs_file, name="flux_docs_index"),
    path("docs/flux/<str:version>/<path:docs_path>", views.flux_docs_file, name="flux_docs_file"),
    path("release/<path:artifact_path>", views.release_file, name="release_file"),
    path("realease/<path:artifact_path>", views.release_typo_redirect, name="release_typo_redirect"),
    path("reports/<slug:customer>/<slug:gist_id>", views.report_detail, name="report_detail"),
]

from django.urls import path

from . import device_api, views

app_name = "panellock"

urlpatterns = [
    path("", views.index, name="index"),
    path("proposal-request/", views.builder_proposal, name="builder_proposal"),
    path("protect/", views.protect, name="protect"),
    path("proposal/<uuid:estimate_id>/<str:token>/", views.proposal, name="proposal"),
    path("proposal/<uuid:estimate_id>/<str:token>/follow-up/", views.follow_up, name="follow_up"),
    path("portal/", views.portal, name="portal"),
    path("portal/<slug:organization_slug>/", views.organization_portal, name="organization_portal"),
    path(
        "portal/<slug:organization_slug>/panels/<uuid:panel_id>/allowances/",
        views.panel_allowances,
        name="panel_allowances",
    ),
    path(
        "portal/<slug:organization_slug>/panels/<uuid:panel_id>/connect/",
        views.panel_connection,
        name="panel_connection",
    ),
    path(
        "portal/<slug:organization_slug>/projects/<uuid:project_id>/gateway-upload/",
        views.gateway_upload,
        name="gateway_upload",
    ),
    path("portal/<slug:organization_slug>/uploads/", views.upload_session, name="upload_session"),
    path("portal/<slug:organization_slug>/enrollment/", views.create_enrollment, name="create_enrollment"),
    path("portal/<slug:organization_slug>/updates/new/", views.managed_update, name="managed_update"),
    path("portal/<slug:organization_slug>/plans/<uuid:plan_id>/", views.review_plan, name="review_plan"),
    path("api/v1/enroll/", device_api.enroll, name="device_enroll"),
    path("api/v1/heartbeat/", device_api.heartbeat, name="device_heartbeat"),
    path("api/v1/jobs/next/", device_api.next_job, name="device_next_job"),
    path("api/v1/jobs/<uuid:job_id>/events/", device_api.job_event, name="device_job_event"),
]

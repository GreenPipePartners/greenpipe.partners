from django import forms

from .models import BackupAsset, Device, FollowUpRequest, Panel, UpdateRelease


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUpRequest
        fields = ["preferred_contact", "best_time", "details"]
        widgets = {"details": forms.Textarea}


class EnrollmentForm(forms.Form):
    panel = forms.ModelChoiceField(
        queryset=Panel.objects.none(),
        required=False,
        help_text="Select a panel to start a service connection, or leave blank when enrolling an unassigned reusable AgentLab.",
    )
    intended_name = forms.CharField(max_length=160, label="AgentLab name")
    as_spare = forms.BooleanField(
        required=False,
        label="Enroll without starting a panel session",
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["panel"].queryset = organization.panels.order_by("name")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("as_spare") and not cleaned.get("panel"):
            self.add_error("panel", "Select a target panel or enroll this AgentLab without starting a panel session.")
        if cleaned.get("as_spare") and cleaned.get("panel"):
            self.add_error("panel", "An AgentLab enrolled without a session cannot also select a target panel.")
        return cleaned


class ManagedUpdateForm(forms.Form):
    panel = forms.ModelChoiceField(queryset=Panel.objects.none())
    release = forms.ModelChoiceField(queryset=UpdateRelease.objects.none())
    backup = forms.ModelChoiceField(queryset=BackupAsset.objects.none())
    maintenance_window = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    request_text = forms.CharField(widget=forms.Textarea, help_text="Describe the update or replacement outcome you want.")
    replacement = forms.BooleanField(required=False, help_text="Prepare an enrolled spare as the replacement device.")
    replacement_device = forms.ModelChoiceField(queryset=Device.objects.none(), required=False, help_text="Required only for replacement; must be an unassigned enrolled spare.")
    downtime_acknowledged = forms.BooleanField(label="I authorize this maintenance window and acknowledge possible HMI downtime.")

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["panel"].queryset = organization.panels.order_by("name")
        self.fields["release"].queryset = UpdateRelease.objects.filter(
            published_at__isnull=False,
        ).exclude(artifact_url="").exclude(artifact_sha256="").order_by("-published_at")
        self.fields["backup"].queryset = organization.backups.filter(scan_status=BackupAsset.ScanStatus.CLEAN).order_by("-created_at")
        self.fields["replacement_device"].queryset = organization.devices.filter(
            status=Device.Status.SPARE,
            assignments__isnull=True,
        ).order_by("name")

    def clean(self):
        cleaned = super().clean()
        panel = cleaned.get("panel")
        backup = cleaned.get("backup")
        replacement = cleaned.get("replacement")
        replacement_device = cleaned.get("replacement_device")
        if panel and backup and backup.panel_id != panel.id:
            self.add_error("backup", "Select a clean backup belonging to this panel.")
        if replacement and not replacement_device:
            self.add_error("replacement_device", "Select the enrolled spare that will replace this panel PC.")
        if not replacement and replacement_device:
            self.add_error("replacement_device", "Select replacement only when preparing a spare.")
        return cleaned

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .gists import parse_gist_id


class Report(models.Model):
    class ReportType(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        ENGINEERING = "engineering", "Engineering"

    customer = models.CharField(max_length=80)
    customer_name = models.CharField(max_length=120, blank=True)
    report_type = models.CharField(max_length=24, choices=ReportType.choices, default=ReportType.WEEKLY)
    title = models.CharField(max_length=180, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    gist_url = models.URLField()
    gist_id = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["customer", "gist_id"], name="unique_report_customer_gist")]
        ordering = ["customer", "gist_id"]

    def clean(self):
        try:
            self.gist_id = parse_gist_id(self.gist_url)
        except ValueError as exc:
            raise ValidationError({"gist_url": str(exc)}) from exc

    def save(self, *args, **kwargs):
        self.gist_id = parse_gist_id(self.gist_url)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("portal:report_detail", kwargs={"customer": self.customer, "gist_id": self.gist_id})

    def __str__(self):
        if self.title:
            return f"{self.customer} / {self.title}"
        if self.start_date or self.end_date:
            return f"{self.customer} / {self.start_date} - {self.end_date}"
        return f"{self.customer} / {self.get_report_type_display()} Report"

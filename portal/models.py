from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .gists import parse_gist_id


class Report(models.Model):
    customer = models.CharField(max_length=80)
    customer_name = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
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
        return f"{self.customer} / {self.start_date} - {self.end_date}"

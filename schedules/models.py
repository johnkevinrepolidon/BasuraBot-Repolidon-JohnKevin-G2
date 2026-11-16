from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class WasteCategory(models.TextChoices):
    BIODEGRADABLE = "BIODEGRADABLE", "Biodegradable"
    RECYCLABLE = "RECYCLABLE", "Recyclable"
    RESIDUAL = "RESIDUAL", "Residual"


class RouteSchedule(models.Model):
    """Weekly garbage collection schedule of a barangay, per route and waste category."""

    class Day(models.TextChoices):
        MON = "MON", "Monday"
        TUE = "TUE", "Tuesday"
        WED = "WED", "Wednesday"
        THU = "THU", "Thursday"
        FRI = "FRI", "Friday"
        SAT = "SAT", "Saturday"
        SUN = "SUN", "Sunday"

    barangay = models.ForeignKey("accounts.Barangay", on_delete=models.PROTECT, related_name="schedules")
    waste_category = models.CharField(max_length=15, choices=WasteCategory.choices)
    route_name = models.CharField(max_length=100)
    collection_day = models.CharField(max_length=3, choices=Day.choices)
    collection_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "route_schedule"
        constraints = [
            # BR-09: no two schedules with the same route, day and time in a barangay.
            models.UniqueConstraint(
                fields=["barangay", "route_name", "collection_day", "collection_time"],
                name="uniq_route_schedule",
            )
        ]

    def __str__(self):
        return f"{self.route_name} - {self.get_collection_day_display()} {self.collection_time:%H:%M}"


class Announcement(models.Model):
    """Announcement posted by barangay staff for the residents of their barangay."""

    barangay = models.ForeignKey("accounts.Barangay", on_delete=models.PROTECT, related_name="announcements")
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="announcements"
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    posted_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "announcement"
        ordering = ["-posted_at"]
        constraints = [
            # BR-11: expiry must be later than the posted date-time (NULL = no expiry).
            models.CheckConstraint(
                check=Q(expires_at__isnull=True) | Q(expires_at__gt=F("posted_at")),
                name="announcement_expires_after_posted",
            )
        ]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()

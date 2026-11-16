from django import forms
from django.utils import timezone

from .models import Announcement, RouteSchedule

DT_LOCAL = "%Y-%m-%dT%H:%M"


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = RouteSchedule
        fields = ["waste_category", "route_name", "collection_day", "collection_time", "is_active"]
        labels = {"is_active": "Active"}
        widgets = {"collection_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"})}

    def __init__(self, *args, barangay, **kwargs):
        self.barangay = barangay  # always the logged-in staff's own barangay (BR-08)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        route, day, at = (cleaned.get(k) for k in ("route_name", "collection_day", "collection_time"))
        if route and day and at:
            duplicates = RouteSchedule.objects.filter(
                barangay=self.barangay, route_name__iexact=route, collection_day=day, collection_time=at
            ).exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "This barangay already has a schedule with the same route, day and time."
                )
        return cleaned

    def save(self, commit=True):
        schedule = super().save(commit=False)
        schedule.barangay = self.barangay
        if commit:
            schedule.save()
        return schedule


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "expires_at"]
        labels = {"expires_at": "Expires at (optional)"}
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
            "expires_at": forms.DateTimeInput(format=DT_LOCAL, attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, barangay, posted_by, **kwargs):
        self.barangay = barangay
        self.posted_by = posted_by
        super().__init__(*args, **kwargs)
        self.fields["expires_at"].input_formats = [DT_LOCAL, "%Y-%m-%d %H:%M"]

    def clean_expires_at(self):
        expires_at = self.cleaned_data.get("expires_at")
        if expires_at:
            posted_at = self.instance.posted_at if self.instance.pk else timezone.now()
            if expires_at <= posted_at:
                raise forms.ValidationError("The expiry date and time must be later than the posting time.")
        return expires_at

    def save(self, commit=True):
        announcement = super().save(commit=False)
        announcement.barangay = self.barangay
        if not announcement.pk:
            announcement.posted_by = self.posted_by
        if commit:
            announcement.save()
        return announcement

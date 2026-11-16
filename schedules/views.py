from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from accounts.decorators import resident_required, staff_required

from .forms import AnnouncementForm, ScheduleForm
from .models import Announcement, RouteSchedule
from .services import DAY_INDEX, current_announcements, upcoming_for_barangay


# ---------- Resident (read-only, own barangay only: BR-10) ----------

@resident_required
def resident_schedules(request):
    return render(request, "schedules/resident_schedules.html", {
        "items": upcoming_for_barangay(request.user.barangay),
    })


@resident_required
def resident_announcements(request):
    return render(request, "schedules/resident_announcements.html", {
        "announcements": current_announcements(request.user.barangay),
    })


# ---------- Staff: schedules (own barangay only: BR-08) ----------

def _own_schedule(request, pk):
    return get_object_or_404(RouteSchedule, pk=pk, barangay=request.user.barangay)


@staff_required
def staff_schedules(request):
    schedules = sorted(
        RouteSchedule.objects.filter(barangay=request.user.barangay),
        key=lambda s: (DAY_INDEX[s.collection_day], s.collection_time),
    )
    return render(request, "schedules/staff_schedule_list.html", {"schedules": schedules})


@staff_required
def schedule_create(request):
    form = ScheduleForm(request.POST or None, barangay=request.user.barangay)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Schedule added.")
            return redirect("schedules:staff_schedules")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form, "title": "Add collection schedule", "submit_label": "Save schedule",
        "cancel_url": reverse_lazy("schedules:staff_schedules"),
    })


@staff_required
def schedule_edit(request, pk):
    schedule = _own_schedule(request, pk)
    form = ScheduleForm(request.POST or None, instance=schedule, barangay=request.user.barangay)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Schedule updated.")
            return redirect("schedules:staff_schedules")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form, "title": "Edit collection schedule", "submit_label": "Save changes",
        "cancel_url": reverse_lazy("schedules:staff_schedules"),
    })


@staff_required
def schedule_deactivate(request, pk):
    """Delete = deactivate (soft delete), so history is kept (SDD design notes)."""
    schedule = _own_schedule(request, pk)
    if request.method == "POST":
        schedule.is_active = False
        schedule.save(update_fields=["is_active"])
        messages.success(request, "Schedule deactivated. Residents no longer see it.")
        return redirect("schedules:staff_schedules")
    return render(request, "confirm.html", {
        "title": "Deactivate schedule",
        "message": f"Deactivate \"{schedule}\"? Residents will no longer see it. You can reactivate it by editing it.",
        "confirm_label": "Deactivate",
        "cancel_url": reverse_lazy("schedules:staff_schedules"),
    })


# ---------- Staff: announcements (own barangay only: BR-08) ----------

def _own_announcement(request, pk):
    return get_object_or_404(Announcement, pk=pk, barangay=request.user.barangay)


@staff_required
def staff_announcements(request):
    return render(request, "schedules/staff_announcement_list.html", {
        "announcements": Announcement.objects.filter(barangay=request.user.barangay).select_related("posted_by"),
    })


@staff_required
def announcement_create(request):
    form = AnnouncementForm(request.POST or None, barangay=request.user.barangay, posted_by=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement posted.")
            return redirect("schedules:staff_announcements")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form, "title": "Post announcement", "submit_label": "Post announcement",
        "cancel_url": reverse_lazy("schedules:staff_announcements"),
    })


@staff_required
def announcement_edit(request, pk):
    announcement = _own_announcement(request, pk)
    form = AnnouncementForm(
        request.POST or None, instance=announcement, barangay=request.user.barangay, posted_by=request.user
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated.")
            return redirect("schedules:staff_announcements")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form, "title": "Edit announcement", "submit_label": "Save changes",
        "cancel_url": reverse_lazy("schedules:staff_announcements"),
    })


@staff_required
def announcement_delete(request, pk):
    announcement = _own_announcement(request, pk)
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Announcement deleted.")
        return redirect("schedules:staff_announcements")
    return render(request, "confirm.html", {
        "title": "Delete announcement",
        "message": f"Permanently delete \"{announcement.title}\"?",
        "confirm_label": "Delete",
        "cancel_url": reverse_lazy("schedules:staff_announcements"),
    })

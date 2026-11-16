from django.contrib import admin

from .models import Announcement, RouteSchedule


@admin.register(RouteSchedule)
class RouteScheduleAdmin(admin.ModelAdmin):
    list_display = ("route_name", "barangay", "waste_category", "collection_day", "collection_time", "is_active")
    list_filter = ("barangay", "waste_category", "collection_day", "is_active")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "barangay", "posted_by", "posted_at", "expires_at")
    list_filter = ("barangay",)

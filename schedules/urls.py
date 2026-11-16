from django.urls import path

from . import views

app_name = "schedules"

urlpatterns = [
    # Residents
    path("schedules/", views.resident_schedules, name="resident_schedules"),
    path("announcements/", views.resident_announcements, name="resident_announcements"),
    # Staff portal: schedules
    path("portal/schedules/", views.staff_schedules, name="staff_schedules"),
    path("portal/schedules/new/", views.schedule_create, name="schedule_create"),
    path("portal/schedules/<int:pk>/edit/", views.schedule_edit, name="schedule_edit"),
    path("portal/schedules/<int:pk>/deactivate/", views.schedule_deactivate, name="schedule_deactivate"),
    # Staff portal: announcements
    path("portal/announcements/", views.staff_announcements, name="staff_announcements"),
    path("portal/announcements/new/", views.announcement_create, name="announcement_create"),
    path("portal/announcements/<int:pk>/edit/", views.announcement_edit, name="announcement_edit"),
    path("portal/announcements/<int:pk>/delete/", views.announcement_delete, name="announcement_delete"),
]

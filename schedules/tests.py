from datetime import datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Barangay, User

from .models import Announcement, RouteSchedule
from .services import next_collection


class BaseCase(TestCase):
    def setUp(self):
        self.b1 = Barangay.objects.create(barangay_name="Mambaling", city_municipality="Cebu City")
        self.b2 = Barangay.objects.create(barangay_name="Labangon", city_municipality="Cebu City")
        mk = lambda email, mobile, role, b: User.objects.create_user(
            email=email, password="Secret123", full_name=email, mobile_number=mobile, role=role, barangay=b)
        self.res1 = mk("res1@example.com", "09170000001", User.Role.RESIDENT, self.b1)
        self.res2 = mk("res2@example.com", "09170000002", User.Role.RESIDENT, self.b2)
        self.staff1 = mk("staff1@example.com", "09170000003", User.Role.STAFF, self.b1)
        self.staff2 = mk("staff2@example.com", "09170000004", User.Role.STAFF, self.b2)

    def login(self, email):
        self.client.login(username=email, password="Secret123")

    schedule_data = {
        "waste_category": "RECYCLABLE", "route_name": "Main Road",
        "collection_day": "WED", "collection_time": "07:30", "is_active": "on",
    }


class ScheduleCrudTests(BaseCase):
    def test_staff_creates_schedule_for_own_barangay(self):
        self.login("staff1@example.com")
        response = self.client.post(reverse("schedules:schedule_create"), self.schedule_data)
        self.assertRedirects(response, reverse("schedules:staff_schedules"))
        self.assertEqual(RouteSchedule.objects.get().barangay, self.b1)

    def test_duplicate_schedule_rejected(self):
        self.login("staff1@example.com")
        self.client.post(reverse("schedules:schedule_create"), self.schedule_data)
        response = self.client.post(reverse("schedules:schedule_create"), self.schedule_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RouteSchedule.objects.count(), 1)

    def test_resident_cannot_use_staff_portal(self):
        self.login("res1@example.com")
        self.assertEqual(self.client.get(reverse("schedules:staff_schedules")).status_code, 403)
        self.assertEqual(self.client.post(reverse("schedules:schedule_create"), self.schedule_data).status_code, 403)
        self.assertEqual(RouteSchedule.objects.count(), 0)

    def test_staff_cannot_edit_other_barangay_schedule(self):
        schedule = RouteSchedule.objects.create(
            barangay=self.b2, waste_category="RESIDUAL", route_name="Other",
            collection_day="FRI", collection_time=time(6, 0))
        self.login("staff1@example.com")
        self.assertEqual(self.client.get(reverse("schedules:schedule_edit", args=[schedule.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("schedules:schedule_deactivate", args=[schedule.pk])).status_code, 404)

    def test_update_schedule(self):
        schedule = RouteSchedule.objects.create(
            barangay=self.b1, waste_category="RESIDUAL", route_name="Old",
            collection_day="FRI", collection_time=time(6, 0))
        self.login("staff1@example.com")
        data = dict(self.schedule_data, route_name="New Route")
        self.client.post(reverse("schedules:schedule_edit", args=[schedule.pk]), data)
        schedule.refresh_from_db()
        self.assertEqual(schedule.route_name, "New Route")

    def test_deactivate_hides_from_resident(self):
        schedule = RouteSchedule.objects.create(
            barangay=self.b1, waste_category="RESIDUAL", route_name="Visible Route",
            collection_day="FRI", collection_time=time(6, 0))
        self.login("res1@example.com")
        self.assertContains(self.client.get(reverse("schedules:resident_schedules")), "Visible Route")
        self.client.logout()
        self.login("staff1@example.com")
        self.client.post(reverse("schedules:schedule_deactivate", args=[schedule.pk]))
        schedule.refresh_from_db()
        self.assertFalse(schedule.is_active)
        self.client.logout()
        self.login("res1@example.com")
        self.assertNotContains(self.client.get(reverse("schedules:resident_schedules")), "Visible Route")

    def test_resident_sees_only_own_barangay(self):
        RouteSchedule.objects.create(
            barangay=self.b2, waste_category="RESIDUAL", route_name="Labangon Only",
            collection_day="FRI", collection_time=time(6, 0))
        self.login("res1@example.com")
        self.assertNotContains(self.client.get(reverse("schedules:resident_schedules")), "Labangon Only")


class AnnouncementTests(BaseCase):
    def test_staff_posts_announcement_linked_to_user(self):
        self.login("staff1@example.com")
        self.client.post(reverse("schedules:announcement_create"), {"title": "Hello", "message": "World", "expires_at": ""})
        a = Announcement.objects.get()
        self.assertEqual(a.posted_by, self.staff1)
        self.assertEqual(a.barangay, self.b1)

    def test_expiry_must_be_later_than_posting(self):
        self.login("staff1@example.com")
        response = self.client.post(reverse("schedules:announcement_create"), {
            "title": "Old", "message": "x", "expires_at": "2000-01-01T08:00"})
        self.assertIn("expires_at", response.context["form"].errors)
        self.assertEqual(Announcement.objects.count(), 0)

    def test_expired_not_shown_to_residents(self):
        Announcement.objects.create(
            barangay=self.b1, posted_by=self.staff1, title="Expired one", message="x",
            posted_at=timezone.now() - timedelta(days=2), expires_at=timezone.now() - timedelta(days=1))
        Announcement.objects.create(barangay=self.b1, posted_by=self.staff1, title="Current one", message="x")
        self.login("res1@example.com")
        response = self.client.get(reverse("schedules:resident_announcements"))
        self.assertContains(response, "Current one")
        self.assertNotContains(response, "Expired one")

    def test_staff_cannot_delete_other_barangay_announcement(self):
        a = Announcement.objects.create(barangay=self.b2, posted_by=self.staff2, title="T", message="x")
        self.login("staff1@example.com")
        self.assertEqual(self.client.post(reverse("schedules:announcement_delete", args=[a.pk])).status_code, 404)
        self.assertEqual(Announcement.objects.count(), 1)

    def test_staff_deletes_own_barangay_announcement(self):
        a = Announcement.objects.create(barangay=self.b1, posted_by=self.staff1, title="T", message="x")
        self.login("staff1@example.com")
        self.client.post(reverse("schedules:announcement_delete", args=[a.pk]))
        self.assertEqual(Announcement.objects.count(), 0)


class NextCollectionTests(BaseCase):
    def test_next_collection_same_day_and_next_week(self):
        schedule = RouteSchedule(barangay=self.b1, collection_day="MON", collection_time=time(6, 0))
        monday = datetime(2026, 11, 16)  # a Monday
        before = timezone.make_aware(monday.replace(hour=5))
        after = timezone.make_aware(monday.replace(hour=10))
        self.assertEqual(next_collection(schedule, before).date(), monday.date())
        self.assertEqual(next_collection(schedule, after).date(), (monday + timedelta(days=7)).date())

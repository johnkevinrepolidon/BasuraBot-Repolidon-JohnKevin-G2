from datetime import time

from django.core.management.base import BaseCommand

from accounts.models import Barangay, User
from schedules.models import Announcement, RouteSchedule

BARANGAYS = ["Mambaling", "Basak San Nicolas", "Labangon", "Punta Princesa", "Pasil", "Guadalupe"]


class Command(BaseCommand):
    help = "Create demo barangays, test accounts and sample schedules/announcements."

    def handle(self, *args, **options):
        for name in BARANGAYS:
            Barangay.objects.get_or_create(barangay_name=name, city_municipality="Cebu City")
        mambaling = Barangay.objects.get(barangay_name="Mambaling")
        labangon = Barangay.objects.get(barangay_name="Labangon")

        accounts = [
            ("staff@basurabot.test", "Staff12345", "Maria Santos (Staff)", "09171110001", User.Role.STAFF, mambaling),
            ("staff2@basurabot.test", "Staff12345", "Jose Reyes (Staff)", "09171110002", User.Role.STAFF, labangon),
            ("resident@basurabot.test", "Resident123", "Juan Dela Cruz", "09172220001", User.Role.RESIDENT, mambaling),
            ("resident2@basurabot.test", "Resident123", "Ana Cruz", "09172220002", User.Role.RESIDENT, labangon),
        ]
        for email, password, name, mobile, role, barangay in accounts:
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email, password=password, full_name=name,
                    mobile_number=mobile, role=role, barangay=barangay,
                )

        staff = User.objects.get(email="staff@basurabot.test")
        samples = [
            ("BIODEGRADABLE", "Mambaling Main Road", "MON", time(6, 0)),
            ("RECYCLABLE", "Mambaling Main Road", "WED", time(7, 30)),
            ("RESIDUAL", "Mambaling Interior Streets", "FRI", time(6, 30)),
        ]
        for category, route, day, at in samples:
            RouteSchedule.objects.get_or_create(
                barangay=mambaling, route_name=route, collection_day=day, collection_time=at,
                defaults={"waste_category": category},
            )
        Announcement.objects.get_or_create(
            barangay=mambaling, title="Segregate before you set out your waste",
            defaults={"posted_by": staff, "message": "Please set out your garbage only on your scheduled collection day."},
        )
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Staff:    staff@basurabot.test / Staff12345")
        self.stdout.write("Resident: resident@basurabot.test / Resident123")

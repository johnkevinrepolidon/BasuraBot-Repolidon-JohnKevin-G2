from django.test import TestCase
from django.urls import reverse

from .models import Barangay, User


def make_user(barangay, email, role=User.Role.RESIDENT, mobile="09170000001", password="Secret123"):
    return User.objects.create_user(
        email=email, password=password, full_name="Test User",
        mobile_number=mobile, role=role, barangay=barangay,
    )


class RegistrationTests(TestCase):
    def setUp(self):
        self.barangay = Barangay.objects.create(barangay_name="Mambaling", city_municipality="Cebu City")
        self.data = {
            "full_name": "Juan Dela Cruz", "email": "juan@example.com", "mobile_number": "09171234567",
            "barangay": self.barangay.pk, "password1": "Secret123", "password2": "Secret123",
        }

    def test_success_creates_hashed_resident(self):
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(email="juan@example.com")
        self.assertEqual(user.role, User.Role.RESIDENT)
        self.assertNotEqual(user.password, "Secret123")
        self.assertTrue(user.check_password("Secret123"))

    def test_duplicate_email_rejected(self):
        make_user(self.barangay, "juan@example.com")
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_mobile_rejected_even_in_plus63_form(self):
        make_user(self.barangay, "other@example.com", mobile="09171234567")
        self.data["mobile_number"] = "+639171234567"
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertIn("mobile_number", response.context["form"].errors)

    def test_password_mismatch_rejected(self):
        self.data["password2"] = "Different123"
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertIn("password2", response.context["form"].errors)

    def test_weak_password_rejected(self):
        self.data.update(password1="onlyletters", password2="onlyletters")
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertIn("password1", response.context["form"].errors)

    def test_invalid_mobile_rejected(self):
        self.data["mobile_number"] = "12345"
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertIn("mobile_number", response.context["form"].errors)

    def test_cannot_self_register_as_staff(self):
        self.data["role"] = "STAFF"
        self.client.post(reverse("accounts:register"), self.data)
        self.assertEqual(User.objects.get(email="juan@example.com").role, User.Role.RESIDENT)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.barangay = Barangay.objects.create(barangay_name="Mambaling", city_municipality="Cebu City")
        self.resident = make_user(self.barangay, "res@example.com")
        self.staff = make_user(self.barangay, "staff@example.com", role=User.Role.STAFF, mobile="09170000002")

    def test_invalid_credentials_show_error(self):
        response = self.client.post(reverse("accounts:login"), {"username": "res@example.com", "password": "wrong"})
        self.assertContains(response, "Invalid email or password")

    def test_login_then_dashboard_by_role(self):
        self.client.post(reverse("accounts:login"), {"username": "res@example.com", "password": "Secret123"})
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:resident_dashboard"))

    def test_staff_goes_to_staff_dashboard(self):
        self.client.login(username="staff@example.com", password="Secret123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:staff_dashboard"))

    def test_logout_ends_session(self):
        self.client.login(username="res@example.com", password="Secret123")
        self.client.post(reverse("accounts:logout"))
        response = self.client.get(reverse("accounts:resident_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_inactive_account_cannot_log_in(self):
        self.resident.is_active = False
        self.resident.save()
        response = self.client.post(reverse("accounts:login"), {"username": "res@example.com", "password": "Secret123"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class RoleAccessTests(TestCase):
    def setUp(self):
        self.barangay = Barangay.objects.create(barangay_name="Mambaling", city_municipality="Cebu City")
        make_user(self.barangay, "res@example.com")
        make_user(self.barangay, "staff@example.com", role=User.Role.STAFF, mobile="09170000002")

    def test_anonymous_is_sent_to_login(self):
        url = reverse("accounts:resident_dashboard")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_resident_cannot_open_staff_dashboard(self):
        self.client.login(username="res@example.com", password="Secret123")
        self.assertEqual(self.client.get(reverse("accounts:staff_dashboard")).status_code, 403)

    def test_staff_cannot_open_resident_dashboard(self):
        self.client.login(username="staff@example.com", password="Secret123")
        self.assertEqual(self.client.get(reverse("accounts:resident_dashboard")).status_code, 403)

    def test_resident_cannot_create_staff(self):
        self.client.login(username="res@example.com", password="Secret123")
        self.assertEqual(self.client.get(reverse("accounts:staff_create")).status_code, 403)

    def test_staff_can_create_staff(self):
        self.client.login(username="staff@example.com", password="Secret123")
        self.client.post(reverse("accounts:staff_create"), {
            "full_name": "New Staff", "email": "new@example.com", "mobile_number": "09175550000",
            "barangay": self.barangay.pk, "password1": "Secret123", "password2": "Secret123",
        })
        self.assertEqual(User.objects.get(email="new@example.com").role, User.Role.STAFF)


class ProfileTests(TestCase):
    def setUp(self):
        self.barangay = Barangay.objects.create(barangay_name="Mambaling", city_municipality="Cebu City")
        self.user = make_user(self.barangay, "res@example.com")
        self.other = make_user(self.barangay, "other@example.com", mobile="09170000003")

    def test_profile_requires_login(self):
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 302)

    def test_profile_shows_only_own_data(self):
        self.client.login(username="res@example.com", password="Secret123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "res@example.com")
        self.assertNotContains(response, "other@example.com")

    def test_update_own_profile(self):
        self.client.login(username="res@example.com", password="Secret123")
        self.client.post(reverse("accounts:profile_edit"), {
            "full_name": "Updated Name", "email": "res@example.com",
            "mobile_number": "09179999999", "notification_pref": "SMS",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.notification_pref, "SMS")

    def test_cannot_take_another_users_email(self):
        self.client.login(username="res@example.com", password="Secret123")
        response = self.client.post(reverse("accounts:profile_edit"), {
            "full_name": "X", "email": "other@example.com",
            "mobile_number": "09170000001", "notification_pref": "BOTH",
        })
        self.assertIn("email", response.context["form"].errors)

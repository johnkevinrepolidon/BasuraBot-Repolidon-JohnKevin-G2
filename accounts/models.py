from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

PH_MOBILE_REGEX = r"^(09\d{9}|\+639\d{9})$"


class Barangay(models.Model):
    """Master list of barangays covered by the system."""

    barangay_name = models.CharField(max_length=100)
    city_municipality = models.CharField(max_length=100, default="Cebu City")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "barangay"
        ordering = ["barangay_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["barangay_name", "city_municipality"], name="uniq_barangay_name_city"
            )
        ]

    def __str__(self):
        return f"{self.barangay_name}, {self.city_municipality}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        # Case-insensitive login by email.
        return self.get(email__iexact=email)

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("role", User.Role.RESIDENT)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.STAFF)
        if "barangay" not in extra and "barangay_id" not in extra:
            extra["barangay"], _ = Barangay.objects.get_or_create(
                barangay_name="Mambaling", city_municipality="Cebu City"
            )
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Residents and barangay staff share this table; `role` controls access.

    Note: Django's built-in `is_staff` only controls access to /admin/.
    BasuraBot's own staff permission is `role == STAFF`.
    """

    class Role(models.TextChoices):
        RESIDENT = "RESIDENT", "Resident"
        STAFF = "STAFF", "Barangay Staff"

    class NotificationPref(models.TextChoices):
        SMS = "SMS", "SMS only"
        WEB = "WEB", "Web notification only"
        BOTH = "BOTH", "SMS and web"

    username = None
    first_name = None
    last_name = None

    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT, related_name="users")
    full_name = models.CharField(max_length=100)
    email = models.EmailField(
        max_length=120, unique=True, error_messages={"unique": "This email address is already registered."}
    )
    mobile_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(PH_MOBILE_REGEX, "Use the format 09XXXXXXXXX or +639XXXXXXXXX.")
        ],
        error_messages={"unique": "This mobile number is already registered."},
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RESIDENT)
    notification_pref = models.CharField(
        max_length=4, choices=NotificationPref.choices, default=NotificationPref.BOTH
    )
    points_balance = models.IntegerField(default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "mobile_number"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        constraints = [
            models.CheckConstraint(check=Q(points_balance__gte=0), name="users_points_balance_gte_0")
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name

    @property
    def is_resident(self):
        return self.role == self.Role.RESIDENT

    @property
    def is_barangay_staff(self):
        return self.role == self.Role.STAFF

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Barangay, User


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ("barangay_name", "city_municipality", "is_active")
    list_filter = ("is_active",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "barangay", "is_active")
    list_filter = ("role", "barangay", "is_active")
    search_fields = ("email", "full_name", "mobile_number")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "mobile_number", "barangay", "notification_pref", "points_balance")}),
        ("Access", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "mobile_number", "barangay", "role", "password1", "password2")}),
    )

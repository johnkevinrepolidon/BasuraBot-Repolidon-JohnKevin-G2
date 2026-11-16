from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from schedules.services import current_announcements, upcoming_for_barangay

from .decorators import resident_required, staff_required
from .forms import LoginForm, ProfileForm, RegistrationForm, StaffCreateForm
from .models import User


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form,
        "title": "Create a resident account",
        "submit_label": "Register",
        "alt_text": "Already have an account?",
        "alt_label": "Log in",
        "alt_url": reverse_lazy("accounts:login"),
    })


class BasuraLoginView(LoginView):
    template_name = "form_page.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    extra_context = {
        "title": "Log in",
        "submit_label": "Log in",
        "alt_text": "New resident?",
        "alt_label": "Create an account",
        "alt_url": reverse_lazy("accounts:register"),
    }

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Login failed. Check your email and password.")
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    logout(request)  # ends the session
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    if request.user.role == User.Role.STAFF:
        return redirect("accounts:staff_dashboard")
    return redirect("accounts:resident_dashboard")


@resident_required
def resident_dashboard(request):
    barangay = request.user.barangay
    return render(request, "accounts/resident_dashboard.html", {
        "upcoming": upcoming_for_barangay(barangay)[:5],
        "announcements": current_announcements(barangay)[:3],
    })


@staff_required
def staff_dashboard(request):
    from schedules.models import RouteSchedule

    barangay = request.user.barangay
    return render(request, "accounts/staff_dashboard.html", {
        "schedule_count": RouteSchedule.objects.filter(barangay=barangay, is_active=True).count(),
        "announcement_count": current_announcements(barangay).count(),
        "resident_count": User.objects.filter(
            barangay=barangay, role=User.Role.RESIDENT, is_active=True
        ).count(),
    })


@login_required
def profile(request):
    # No user id in the URL: a user can only ever see their own profile.
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form,
        "title": "Edit profile",
        "submit_label": "Save changes",
        "cancel_url": reverse_lazy("accounts:profile"),
    })


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "form_page.html"
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password was changed."
    extra_context = {
        "title": "Change password",
        "submit_label": "Change password",
        "cancel_url": reverse_lazy("accounts:profile"),
    }


@staff_required
def staff_create(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff account created for {user.full_name}.")
            return redirect("accounts:staff_dashboard")
        messages.error(request, "Please correct the errors below.")
    return render(request, "form_page.html", {
        "form": form,
        "title": "Create a staff account",
        "submit_label": "Create staff account",
        "cancel_url": reverse_lazy("accounts:staff_dashboard"),
    })

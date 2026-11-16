from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Announcement, RouteSchedule

DAY_INDEX = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def next_collection(schedule, now=None):
    """The next date-time (local time) this weekly schedule happens."""
    now = timezone.localtime(now or timezone.now())
    days_ahead = (DAY_INDEX[schedule.collection_day] - now.weekday()) % 7
    candidate = timezone.make_aware(
        datetime.combine(now.date() + timedelta(days=days_ahead), schedule.collection_time)
    )
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


def upcoming_for_barangay(barangay):
    """Active schedules of a barangay, soonest pickup first (BR-10)."""
    now = timezone.now()
    items = [
        {"schedule": s, "next": next_collection(s, now)}
        for s in RouteSchedule.objects.filter(barangay=barangay, is_active=True)
    ]
    return sorted(items, key=lambda item: item["next"])


def current_announcements(barangay):
    """Announcements of a barangay that have not expired (BR-10, BR-11)."""
    return (
        Announcement.objects.filter(barangay=barangay)
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
        .select_related("posted_by")
    )

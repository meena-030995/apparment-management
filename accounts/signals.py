from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from core.activity_logs import log_activity
from core.notifications import send_login_notification


def _login_description(request):
    path = getattr(request, "path", "") or ""
    if path.startswith("/admin/"):
        return "signed in to the admin panel."
    if "/api/" in path:
        return "signed in through the API."
    return "signed in to the web dashboard."


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    send_login_notification(user, request)
    log_activity(
        user,
        "login",
        f"{user.username} {_login_description(request)}",
        {"ip_address": request.META.get("REMOTE_ADDR", "Unknown")},
    )

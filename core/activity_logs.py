from accounts.models import ActivityLog


def log_activity(user, action, description, metadata=None):
    if user is None or not getattr(user, "is_authenticated", False):
        return

    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        metadata=metadata or {},
    )

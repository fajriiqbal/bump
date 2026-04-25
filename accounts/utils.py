from .models import AuditLog


def log_action(actor, action, object_type="", object_id="", metadata=None):
    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        metadata=metadata or {},
    )

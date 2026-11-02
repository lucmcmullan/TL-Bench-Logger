from scripts.db import db
from scripts.models import AuditLog

def write_audit(initials, event_type, message):
    db.session.add(AuditLog(user_initials=initials, event_type=event_type, message=message))

    db.session.commit()
from scripts.db import db
from scripts.models import AuditLog
from utils.socketio_instance import socketio

def write_audit(initials, event_type, message):
    if not initials:
        initials = "SYSTEM"

    log = AuditLog(user_initials=initials, event_type=event_type, message=message) 
    db.session.add(log)
    db.session.commit()

    socketio.emit(
        "audit_log", { 
        "user_initials": initials, 
        "event_type": event_type, 
        "message": message, 
        "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") }
        )
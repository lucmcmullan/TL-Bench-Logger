from app import app
from database.db import db
from werkzeug.security import generate_password_hash
from database.models import *

from constants import FACTORY_LAYOUT

with app.app_context():
    BenchLock.query.delete()
    SessionUser.query.delete()
    InspectionSession.query.delete()
    Inspection.query.delete()
    Bench.query.delete()
    
    for row in FACTORY_LAYOUT:
        for bench in row:
            if bench is None:
                continue

            db.session.add(Bench(id=bench["id"], name=bench["label"]))

    db.session.add(User(initials="LM", name="Luc McMullan", password_hash=generate_password_hash("password"), is_admin=True))
    db.session.commit()
    
    print("test benches loaded")
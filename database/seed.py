from app import app
from database.db import db
from werkzeug.security import generate_password_hash
from database.models import *
from database.backup import backup

from constants import FACTORY_LAYOUT

with app.app_context():
    backup("Manual")

    db.create_all()

    BenchLock.query.delete()
    SessionUser.query.delete() 
    
    for row in FACTORY_LAYOUT:
        for bench in row:
            if bench is None:
                continue

            existing_bench = db.session.get(Bench, bench["id"])

            if not existing_bench:
                db.session.add(Bench(id=bench["id"], name=bench["label"]))

    if not User.query.filter_by(initials="LM").first():
        db.session.add(User(initials="LM", name="Luc McMullan", password_hash=generate_password_hash("password"), is_admin=True))
    
    db.session.commit()
    
    print("test benches loaded")
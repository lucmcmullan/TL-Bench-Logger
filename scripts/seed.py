from app import app
from scripts.db import db
from werkzeug.security import generate_password_hash
from scripts.models import *
from utils.backup import backup

import os
with app.app_context():
    backup("Manual")

    db.create_all()

    BenchLock.query.delete()
    SessionUser.query.delete() 

    if not User.query.filter_by(initials="LM", name="Luc McMullan").first():
        db.session.add(User(initials="LM", name="Luc McMullan", password_hash=generate_password_hash(os.getenv(LM_DEFAULT_PASSWORD)), is_admin=True))
    
    db.session.commit()
    
    print("Database re-seeded")
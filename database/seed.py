from app import app
from database.db import db
from werkzeug.security import generate_password_hash
from database.models import *

from constants import FACTORY_LAYOUT

from pathlib import Path
from datetime import datetime

import shutil

with app.app_context():
    db_file = Path("data/app.db")
    backup_dir = Path("data/backups")

    backup_dir.mkdir(parents=True, exist_ok=True)

    if db_file.exists():
        timestamp = datetime.now().strftime("%d%m%y%H%M")
        backup_file = (backup_dir / f"app_{timestamp}.db")
        shutil.copy2(db_file, backup_file)
        print(f"DB backup created: {backup_file}")

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
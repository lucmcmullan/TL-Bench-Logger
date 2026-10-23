from app import app
from database.db import db
from database.models import Bench

from factory import FACTORY_LAYOUT

with app.app_context():
    db.drop_all()
    db.create_all()
    
    for row in FACTORY_LAYOUT:
        for bench in row:
            if bench is None:
                continue

            db.session.add(Bench(id=bench["id"], name=bench["label"]))

    db.session.commit()
    
    print("test benches loaded")
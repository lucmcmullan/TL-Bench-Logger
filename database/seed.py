from app import app
from database.db import db
from database.models import Bench

with app.app_context(): # change to actual benches, not just a placeholder
    db.drop_all()
    db.create_all()
    
    for i in range(1, 51):
        bench = Bench(name=f"B{i:02d}")
        
        db.session.add(bench)
        
    db.session.commit()
    
    print("test benches loaded")
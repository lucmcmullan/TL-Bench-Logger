from flask import Flask

from config import Config

from database.db import db

from routes.auth import auth_bp
from routes.session import session_bp
from routes.benches import bench_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all
    
app.register_blueprint(auth_bp)
app.register_blueprint(session_bp)
app.register_blueprint(bench_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
# re-seed database after changing model:
# delete app.db
# run python -m database.seed 
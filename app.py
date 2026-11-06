from flask import Flask
from utils.socketio_instance import socketio

from config import Config
from scripts.db import db

from routes.auth import auth_bp
from routes.session import session_bp
from routes.benches import bench_bp
from routes.admin import admin_bp
from routes.dev import dev_bp

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(session_bp)
app.register_blueprint(dev_bp)
app.register_blueprint(bench_bp)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

# re-seed database after changing model:
# delete app.db
# run python -m scripts.seed

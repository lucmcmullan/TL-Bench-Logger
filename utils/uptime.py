from pathlib import Path
from datetime import datetime
import json

UPTIME_FILE = Path("data/uptime.json")

DT_THRESHOLD = 300 # seconds

def init_uptime():
    now = datetime.now()

    if not UPTIME_FILE.exists():
        data = {
            "started_at": now.isoformat(),
            "last_shutdown": None
        }

        UPTIME_FILE.write_text(json.dumps(data, indent=4))

        return now

    data = json.loads(UPTIME_FILE.read_text())

    if not data.get("started_at"):
        started_at = datetime.now()
        data["started_at"] = started_at.isoformat()
        UPTIME_FILE.write_text(json.dumps(data, indent=4))
    else:
        started_at = datetime.fromisoformat(data["started_at"])

    last_shutdown = data.get("last_shutdown")

    if last_shutdown:
        downtime = (now - datetime.fromisoformat(last_shutdown)).total_seconds()

        if downtime >= DT_THRESHOLD:
            started_at = now

    data["started_at"] = (started_at.isoformat())

    UPTIME_FILE.write_text(json.dumps(data, indent=4))

    return started_at
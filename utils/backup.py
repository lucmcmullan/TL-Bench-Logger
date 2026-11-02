from pathlib import Path
from datetime import datetime
import shutil, json

def backup(btype: str = "Automatic"):
    db_file = Path("data/app.db")
    backup_dir = Path("data/backups")

    backup_dir.mkdir(parents=True, exist_ok=True)

    if not db_file.exists():
        return

    backup_name = datetime.now().strftime("app_%Y%m%d.db")

    backup_file = backup_dir / backup_name

    if backup_file.exists():
        return

    shutil.copy2(db_file, backup_file)

    meta = {
        "filename": backup_file.name,
        "backup_type": btype,
        "backed_up_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(backup_dir / "_last_backup.json", "w") as f:
        json.dump(meta, f, indent=4)

    print(f"DB backup created: {backup_file}")

def perform_daily_backup():
    now = datetime.now()

    if now.hour >= 17:
        backup()

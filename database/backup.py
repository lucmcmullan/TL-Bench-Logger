from pathlib import Path
from datetime import datetime
import shutil 

def backup():
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

    print(f"DB backup created: {backup_file}")

def perform_daily_backup():
    now = datetime.now()

    if now.hour >= 17:
        backup()

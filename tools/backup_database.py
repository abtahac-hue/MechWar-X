"""Create a full SQL backup of MechWarX before upgrading.

From VS Code's MechWar-X directory:
    py tools/backup_database.py

Requires MySQL Server 8's mysqldump and a working .env.
The backup is saved OUTSIDE the Git repository, next to the project folder.
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402


def main():
    load_dotenv(ROOT / ".env")
    mysql_dump = shutil.which("mysqldump")
    if not mysql_dump:
        candidate = Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe")
        if candidate.exists():
            mysql_dump = str(candidate)
    if not mysql_dump:
        raise SystemExit("Could not locate mysqldump.exe; MySQL Server tools are required.")

    db_name = os.getenv("DB_NAME", "MechWarX")
    if db_name.lower() != "mechwarx":
        raise SystemExit("This script is restricted to the MechWarX database.")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    if not username or password is None:
        raise SystemExit("DB_USER or DB_PASSWORD is missing in .env")

    destination = ROOT.parent / (
        "MechWarX_preupgrade_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".sql"
    )
    args = [
        mysql_dump,
        "--host=" + os.getenv("DB_HOST", "127.0.0.1"),
        "--port=" + os.getenv("DB_PORT", "3306"),
        "--user=" + username,
        "--single-transaction",
        "--routines",
        "--triggers",
        "--events",
        "--set-gtid-purged=OFF",
        db_name,
    ]
    env = dict(os.environ)
    # MySQL reads this only from the local subprocess environment; no
    # password is written to console, command arguments, or the backup file.
    env["MYSQL_PWD"] = password
    try:
        with destination.open("wb") as output:
            proc = subprocess.run(args, stdout=output, stderr=subprocess.PIPE,
                                  env=env, timeout=180)
        if proc.returncode:
            destination.unlink(missing_ok=True)
            raise SystemExit(
                "Backup failed: " + proc.stderr.decode("utf-8", errors="replace")[:1200]
            )
        if destination.stat().st_size < 1000:
            destination.unlink(missing_ok=True)
            raise SystemExit("Backup unexpectedly small; no usable backup was created.")
        # Verify the expected database structures are present in the dump.
        data = destination.read_bytes()
        if b"CREATE TABLE" not in data or b"MaintenanceIncident" not in data:
            raise SystemExit("Backup file lacks expected table definitions. Do NOT upgrade.")
        print("Backup completed. Location:", destination)
        print("Backup size:", destination.stat().st_size, "bytes")
        print("Review and securely retain this file before upgrading.")
    finally:
        env.pop("MYSQL_PWD", None)


if __name__ == "__main__":
    main()

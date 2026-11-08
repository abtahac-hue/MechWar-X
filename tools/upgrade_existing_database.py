"""One-time MechWar-X migration runner (no MySQL Workbench required).

Run only AFTER making and verifying a current database backup:
    py tools/upgrade_existing_database.py --backup-confirmed

This updates the existing schema and triggers. MySQL DDL commits automatically:
if a step fails, STOP and inspect the error instead of rerunning blindly.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from db_connection import get_connection  # noqa: E402


def split_mysql_script(source):
    """Handle the DELIMITER statements and procedure bodies in this project."""
    delimiter = ";"
    collected = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("DELIMITER "):
            if collected:
                raise ValueError("Unexpected delimiter in unfinished statement")
            delimiter = stripped.split(None, 1)[1]
            continue
        collected.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(collected)
            statement = statement[:statement.rfind(delimiter)].strip()
            if statement:
                yield statement
            collected = []
    if collected:
        raise ValueError("Incomplete SQL statement in upgrade script")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-confirmed", action="store_true",
                        help="Confirm a recent verified database backup exists")
    args = parser.parse_args()
    if not args.backup_confirmed:
        parser.error("Make and VERIFY a database backup first, then rerun with --backup-confirmed")
    sql_file = ROOT / "sql" / "06_upgrade_existing_database.sql"
    statements = list(split_mysql_script(sql_file.read_text(encoding="utf-8")))
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT DATABASE()")
            name = cursor.fetchone()[0]
            if name.lower() != "mechwarx":
                raise RuntimeError(f"Wrong database: {name!r}")
            cursor.execute("SHOW COLUMNS FROM MaintenanceIncident LIKE 'IssueType'")
            if cursor.fetchone():
                raise RuntimeError(
                    "IssueType already exists. Migration may already be applied or partial; "
                    "inspect the database before making changes."
                )
            cursor.execute("SHOW CREATE TABLE MaintenanceIncident")
            ddl = cursor.fetchone()[1]
            if "chk_incident_repair_status" not in ddl:
                raise RuntimeError(
                    "Expected check constraint not found. Review SHOW CREATE TABLE first."
                )
            print(f"Database: {name}; {len(statements)} upgrade statements.")
            print("WARNING: This modifies tables and triggers and cannot be fully rolled back.")
            confirmation = input("Type UPGRADE MECHWARX to continue: ").strip()
            if confirmation != "UPGRADE MECHWARX":
                print("Cancelled; no database changes made.")
                return
            for index, statement in enumerate(statements, start=1):
                header = statement.lstrip().splitlines()[0][:90]
                print(f"[{index}/{len(statements)}] {header}")
                cursor.execute(statement)
                # No result sets are expected, but drain if the driver returns one.
                while cursor.nextset():
                    pass
            connection.commit()
            print("Upgrade completed. Confirm with SHOW COLUMNS and SHOW TRIGGERS.")
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    main()

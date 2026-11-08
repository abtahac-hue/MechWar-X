"""Read-only MechWar-X database readiness report.

Usage: py tools/verify_database.py
No INSERT, UPDATE, DELETE, or stored procedure calls are executed.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from db_connection import get_connection  # noqa: E402

EXPECTED_TABLES = {
    "MechType", "BattleGarage", "PitCrewTechnician", "Mech",
    "MechInventory", "Client", "DeploymentManifest", "MaintenanceIncident",
}
EXPECTED_TRIGGERS = {
    "trg_critical_maintenance_lock",
    "trg_maintenance_repair_update",
    "trg_deployment_cancellation_sync",
}
EXPECTED_PROCEDURES = {
    "BookDeployment", "CancelDeployment", "StartDeployment", "CompleteDeployment",
}
REQUIRED_INCIDENT_COLUMNS = {
    "IncidentID", "MechID", "StaffID", "ReportedByClientID", "IssueType",
    "IncidentDate", "IncidentDescription", "EngineeringNotes",
    "Severity", "RepairStatus", "RepairCompletedDate",
}


def show(name, passed, detail):
    print(f"[{'PASS' if passed else 'CHECK'}] {name}: {detail}")
    return passed


def main():
    connection = get_connection()
    passes = []
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SHOW TABLES")
            tables = {row[0] for row in cursor.fetchall()}
            passes.append(show("Eight tables", EXPECTED_TABLES <= tables,
                               f"{len(EXPECTED_TABLES & tables)}/8 found"))

            cursor.execute("SHOW COLUMNS FROM MaintenanceIncident")
            columns = {row[0] for row in cursor.fetchall()}
            missing_columns = sorted(REQUIRED_INCIDENT_COLUMNS - columns)
            passes.append(show("Incident schema", not missing_columns,
                               "All required fields present" if not missing_columns
                               else "Missing: " + ", ".join(missing_columns)))

            cursor.execute("SHOW TRIGGERS")
            triggers = {row[0] for row in cursor.fetchall()}
            passes.append(show("Maintenance and cancellation triggers",
                               EXPECTED_TRIGGERS <= triggers,
                               f"{len(EXPECTED_TRIGGERS & triggers)}/3 found"))

            cursor.execute(
                "SELECT ROUTINE_NAME FROM information_schema.ROUTINES "
                "WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_TYPE='PROCEDURE'"
            )
            procedures = {row[0] for row in cursor.fetchall()}
            passes.append(show("Stored procedures",
                               EXPECTED_PROCEDURES <= procedures,
                               f"{len(EXPECTED_PROCEDURES & procedures)}/4 found"))

            for label, table in (
                ("Mechs", "Mech"),
                ("Deployments", "DeploymentManifest"),
                ("Maintenance incidents", "MaintenanceIncident"),
            ):
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"  {label}: {cursor.fetchone()[0]}")
        finally:
            cursor.close()
    finally:
        connection.close()

    print()
    print("Static readiness checks:", f"{sum(passes)}/{len(passes)} passed")
    print("Note: triggers/procedures must still be behavior-tested on a backed-up test DB.")


if __name__ == "__main__":
    main()

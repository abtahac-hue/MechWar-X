"""Database operations for the MechWar-X desktop GUI.
Uses the existing .env and db_connection.py; never runs setup SQL on import.
"""
from decimal import Decimal
from db_connection import get_connection


def register_mech(values):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO Mech
                (ChassisSerialNumber, Manufacturer, Model, AssemblyYear, ArmorColor,
                 DailyDeploymentRate, MechTypeID, GarageID)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (
                values['Chassis Serial Number'], values['Manufacturer'], values['Model'],
                int(values['Assembly Year']), values['Armor Color'],
                Decimal(values['Daily Deployment Rate']), int(values['Mech Type ID']),
                int(values['Garage ID'])
            ))
            mech_id = cursor.lastrowid
            cursor.execute("INSERT INTO MechInventory (MechID) VALUES (%s)", (mech_id,))
            connection.commit()
            return mech_id
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def search_deployments(client_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT SerialID, ClientID, MechID,
                ScheduledStart, ManifestStatus
                FROM DeploymentManifest WHERE ClientID=%s ORDER BY ScheduledStart DESC""", (client_id,))
            rows = cursor.fetchall()
            return [
                (manifest_id, client, mech,
                 scheduled_start.strftime("%Y-%m-%d %H:%M")
                 if hasattr(scheduled_start, "strftime")
                 else str(scheduled_start),
                 status)
                for manifest_id, client, mech, scheduled_start, status in rows
            ]
        finally:
            cursor.close()
    finally:
        connection.close()


def book_deployment(values):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("CALL BookDeployment(%s,%s,%s,%s,%s,%s)", (
                int(values['Client ID']), int(values['Mech ID']),
                int(values['Departure Garage ID']), int(values['Return Garage ID']),
                values['Scheduled Start'], values['Scheduled Return']
            ))
            # Consume any procedure results before closing the cursor.
            while cursor.nextset():
                pass
            connection.commit()
            return True
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_incidents():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            try:
                cursor.execute("""SELECT IncidentID AS id, MechID AS mech,
                    Severity AS severity, RepairStatus AS status,
                    IssueType AS issue_type
                    FROM MaintenanceIncident ORDER BY IncidentID DESC""")
            except Exception as exc:
                # Keep incident viewing working on the original schema until
                # the optional one-time migration has been applied.
                if getattr(exc, "errno", None) != 1054:
                    raise
                cursor.execute("""SELECT IncidentID AS id, MechID AS mech,
                    Severity AS severity, RepairStatus AS status,
                    Severity AS issue_type
                    FROM MaintenanceIncident ORDER BY IncidentID DESC""")
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()


def mark_incident_repaired(incident_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("""UPDATE MaintenanceIncident
                SET RepairStatus='Repaired',
                    RepairCompletedDate=GREATEST(NOW(), IncidentDate)
                WHERE IncidentID=%s AND RepairStatus <> 'Repaired'""", (incident_id,))
            changed = cursor.rowcount
            connection.commit()
            return changed
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_incident(values):
    """Create an auditable incident. Maintenance triggers lock critical failures."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO MaintenanceIncident
                (MechID, StaffID, ReportedByClientID, IncidentDescription,
                 Severity, IssueType, RepairStatus, EngineeringNotes)
                VALUES (%s, %s, %s, %s, %s, %s, 'Reported', %s)""",
                (int(values["Mech ID"]), int(values["Technician ID"]),
                 int(values["Reporting Client ID"]),
                 values["Damage Description"], values["Severity"],
                 values["Issue Type"], values["Engineering Notes"])
            )
            incident_id = cursor.lastrowid
            connection.commit()
            return incident_id
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cancel_deployment(manifest_id):
    """Cancel a booked manifest using the stored procedure and status trigger."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("CALL CancelDeployment(%s)", (int(manifest_id),))
            while cursor.nextset():
                pass
            connection.commit()
            return True
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_incident_status(incident_id, new_status, notes):
    """Update incident lifecycle status and engineering notes in one transaction."""
    if new_status not in ("Reported", "In-Progress", "Awaiting Parts", "Repaired"):
        raise ValueError("Invalid repair status")
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE MaintenanceIncident SET
                    RepairStatus=%s,
                    RepairCompletedDate=CASE WHEN %s='Repaired'
                        THEN GREATEST(NOW(), IncidentDate) ELSE NULL END,
                    EngineeringNotes=CASE WHEN %s <> '' THEN %s
                        ELSE EngineeringNotes END
                   WHERE IncidentID=%s AND RepairStatus <> 'Repaired'""",
                (new_status, new_status, notes, notes, int(incident_id))
            )
            changed = cursor.rowcount
            connection.commit()
            return changed
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

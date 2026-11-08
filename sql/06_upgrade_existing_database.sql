-- MechWar-X | ONE-TIME UPGRADE OF EXISTING DATABASE
-- This script changes an existing populated schema. BACK UP DATABASE FIRST.
-- Do NOT use on a fresh installation; use 01-05 instead.
-- NOT IDEMPOTENT: execute only once, and only after examining SHOW CREATE TABLE.
USE MechWarX;

-- Add optional columns so historical incidents remain valid.
-- The GUI requires values for client and engineering notes for all NEW incidents.
ALTER TABLE MaintenanceIncident
 ADD COLUMN ReportedByClientID INT UNSIGNED NULL,
 ADD COLUMN IssueType VARCHAR(20) NOT NULL DEFAULT 'Routine',
 ADD COLUMN EngineeringNotes TEXT NULL;

-- Preserve the meaning of legacy 'Critical' severity incident records.
UPDATE MaintenanceIncident SET IssueType='Critical' WHERE Severity='Critical';

ALTER TABLE MaintenanceIncident
 ADD CONSTRAINT fk_incident_client FOREIGN KEY (ReportedByClientID)
 REFERENCES Client(ClientID) ON DELETE RESTRICT ON UPDATE CASCADE;

-- The existing check allows only Open / In Progress / Repaired.
-- Keep historical values valid while supporting the professor's required statuses.
ALTER TABLE MaintenanceIncident DROP CHECK chk_incident_repair_status;
ALTER TABLE MaintenanceIncident
 ADD CONSTRAINT chk_incident_repair_status CHECK (
   RepairStatus IN ('Reported','In-Progress','Awaiting Parts',
                    'Repaired','Open','In Progress'));

ALTER TABLE MaintenanceIncident
 ADD CONSTRAINT chk_incident_issue_type CHECK (IssueType IN ('Routine','Critical'));

-- Replace existing maintenance triggers to use IssueType.
DROP TRIGGER IF EXISTS trg_critical_maintenance_lock;
DROP TRIGGER IF EXISTS trg_maintenance_repair_update;
DROP TRIGGER IF EXISTS trg_deployment_cancellation_sync;

DELIMITER $$
CREATE TRIGGER trg_critical_maintenance_lock
AFTER INSERT ON MaintenanceIncident FOR EACH ROW
BEGIN
 IF NEW.IssueType='Critical' AND NEW.RepairStatus<>'Repaired' THEN
  UPDATE MechInventory SET OperationalStatus='Unavailable',
   LastStatusUpdate=CURRENT_TIMESTAMP WHERE MechID=NEW.MechID;
 END IF;
END$$

CREATE TRIGGER trg_maintenance_repair_update
AFTER UPDATE ON MaintenanceIncident FOR EACH ROW
BEGIN
 DECLARE v_UnresolvedCritical INT DEFAULT 0;
 IF NEW.IssueType='Critical' AND NEW.RepairStatus<>'Repaired' THEN
  UPDATE MechInventory SET OperationalStatus='Unavailable',
   LastStatusUpdate=CURRENT_TIMESTAMP WHERE MechID=NEW.MechID;
 ELSE
  SELECT COUNT(*) INTO v_UnresolvedCritical FROM MaintenanceIncident
  WHERE MechID=NEW.MechID AND IssueType='Critical' AND RepairStatus<>'Repaired';
  IF v_UnresolvedCritical=0 THEN
   UPDATE MechInventory SET OperationalStatus='Available',
    LastStatusUpdate=CURRENT_TIMESTAMP WHERE MechID=NEW.MechID;
  END IF;
 END IF;
END$$

-- Synchronizes inventory automatically even when status is changed
-- using a different SQL client rather than the app's CancelDeployment procedure.
CREATE TRIGGER trg_deployment_cancellation_sync
AFTER UPDATE ON DeploymentManifest FOR EACH ROW
BEGIN
 DECLARE v_UnresolvedCritical INT DEFAULT 0;
 DECLARE v_Active INT DEFAULT 0;
 IF NEW.ManifestStatus='Cancelled' AND OLD.ManifestStatus<>'Cancelled' THEN
  SELECT COUNT(*) INTO v_UnresolvedCritical FROM MaintenanceIncident
   WHERE MechID=NEW.MechID AND IssueType='Critical'
    AND RepairStatus<>'Repaired';
  SELECT COUNT(*) INTO v_Active FROM DeploymentManifest
   WHERE MechID=NEW.MechID AND ManifestStatus='Active in Arena';
  IF v_UnresolvedCritical=0 AND v_Active=0 THEN
   UPDATE MechInventory SET OperationalStatus='Available',
    LastStatusUpdate=CURRENT_TIMESTAMP WHERE MechID=NEW.MechID;
  END IF;
 END IF;
END$$
DELIMITER ;

-- Optional post-upgrade read-only checks:
-- SHOW COLUMNS FROM MaintenanceIncident;
-- SHOW TRIGGERS;

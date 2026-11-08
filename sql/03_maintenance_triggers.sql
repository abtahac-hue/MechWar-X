-- MechWar-X | Maintenance triggers
-- Based on the team's original 11_* and 12_* scripts; no test data or calls.
USE MechWarX;
DELIMITER $$
CREATE TRIGGER trg_critical_maintenance_lock
AFTER INSERT ON MaintenanceIncident
FOR EACH ROW
BEGIN
 IF NEW.IssueType = 'Critical' AND NEW.RepairStatus <> 'Repaired' THEN
  UPDATE MechInventory
  SET OperationalStatus = 'Unavailable', LastStatusUpdate = CURRENT_TIMESTAMP
  WHERE MechID = NEW.MechID;
 END IF;
END$$

CREATE TRIGGER trg_maintenance_repair_update
AFTER UPDATE ON MaintenanceIncident
FOR EACH ROW
BEGIN
 DECLARE v_OpenCriticalCount INT DEFAULT 0;
 IF NEW.IssueType = 'Critical' AND NEW.RepairStatus <> 'Repaired' THEN
  UPDATE MechInventory SET OperationalStatus = 'Unavailable',
   LastStatusUpdate = CURRENT_TIMESTAMP WHERE MechID = NEW.MechID;
 ELSE
  SELECT COUNT(*) INTO v_OpenCriticalCount
  FROM MaintenanceIncident
  WHERE MechID = NEW.MechID
   AND IssueType = 'Critical' AND RepairStatus <> 'Repaired';
  IF v_OpenCriticalCount = 0 THEN
   UPDATE MechInventory SET OperationalStatus = 'Available',
    LastStatusUpdate = CURRENT_TIMESTAMP WHERE MechID = NEW.MechID;
  END IF;
 END IF;
END$$
DELIMITER ;

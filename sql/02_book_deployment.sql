-- MechWar-X | BookDeployment
-- Based on the team's original 09_BookDeployment.sql; setup-only (no test calls).
USE MechWarX;
DELIMITER $$
CREATE PROCEDURE BookDeployment(
 IN p_ClientID INT UNSIGNED, IN p_MechID INT UNSIGNED,
 IN p_DepartureGarageID INT UNSIGNED, IN p_ReturnGarageID INT UNSIGNED,
 IN p_ScheduledStart DATETIME, IN p_ScheduledReturn DATETIME
)
BEGIN
 DECLARE v_LicenseExpiration DATE;
 DECLARE v_DailyRate DECIMAL(10,2);
 DECLARE v_Status VARCHAR(20);
 DECLARE v_ConflictCount INT DEFAULT 0;
 DECLARE v_CriticalCount INT DEFAULT 0;
 DECLARE v_EstimatedCost DECIMAL(12,2);
 DECLARE v_LockMechID INT UNSIGNED;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION
 BEGIN
  ROLLBACK;
  RESIGNAL;
 END;
 START TRANSACTION;
 IF p_ScheduledStart IS NULL OR p_ScheduledReturn IS NULL
    OR p_ScheduledReturn <= p_ScheduledStart THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid deployment schedule';
 END IF;
 SELECT LicenseExpirationDate INTO v_LicenseExpiration
 FROM Client WHERE ClientID = p_ClientID;
 IF v_LicenseExpiration IS NULL OR v_LicenseExpiration < DATE(p_ScheduledReturn) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Client license invalid or expired';
 END IF;
 SET v_LockMechID = NULL;
 SELECT MechID, DailyDeploymentRate INTO v_LockMechID, v_DailyRate
 FROM Mech WHERE MechID = p_MechID FOR UPDATE;
 IF v_LockMechID IS NULL THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mech not found';
 END IF;
 SET v_Status = NULL;
 SELECT OperationalStatus INTO v_Status
 FROM MechInventory WHERE MechID = p_MechID;
 IF v_Status IS NULL OR v_Status <> 'Available' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mech is unavailable';
 END IF;
 SELECT COUNT(*) INTO v_CriticalCount
 FROM MaintenanceIncident WHERE MechID = p_MechID
 AND Severity = 'Critical' AND RepairStatus <> 'Repaired';
 IF v_CriticalCount > 0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mech has unresolved critical maintenance';
 END IF;
 SELECT COUNT(*) INTO v_ConflictCount
 FROM DeploymentManifest WHERE MechID = p_MechID
 AND ManifestStatus IN ('Match Booked', 'Active in Arena')
 AND ScheduledStart < p_ScheduledReturn AND ScheduledReturn > p_ScheduledStart;
 IF v_ConflictCount > 0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mech already booked for this period';
 END IF;
 SET v_EstimatedCost = ROUND(
  v_DailyRate * TIMESTAMPDIFF(MINUTE,p_ScheduledStart,p_ScheduledReturn)/1440,2
 );
 INSERT INTO DeploymentManifest(
  ClientID,MechID,DepartureGarageID,ReturnGarageID,ScheduledStart,
  ScheduledReturn,AgreedDailyRate,EstimatedCost,ManifestStatus
 ) VALUES (
  p_ClientID,p_MechID,p_DepartureGarageID,p_ReturnGarageID,p_ScheduledStart,
  p_ScheduledReturn,v_DailyRate,v_EstimatedCost,'Match Booked'
 );
 COMMIT;
END$$
DELIMITER ;

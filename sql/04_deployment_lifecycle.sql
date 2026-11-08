-- MechWar-X | Deployment lifecycle procedures
-- Derived from team originals: 14_cancel_deployment.sql,
-- 15_StartDeployment_FINAL.sql and 16_complete_deployment.sql.
-- Does not run test CALL statements.
USE MechWarX;
DELIMITER $$

CREATE PROCEDURE CancelDeployment(IN p_SerialID INT UNSIGNED)
BEGIN
 DECLARE v_MechID INT UNSIGNED DEFAULT NULL;
 DECLARE v_Status VARCHAR(30) DEFAULT NULL;
 DECLARE v_CriticalCount INT DEFAULT 0;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT MechID INTO v_MechID
 FROM DeploymentManifest WHERE SerialID=p_SerialID;
 IF v_MechID IS NULL THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deployment not found';
 END IF;
 SELECT MechID INTO v_MechID FROM Mech WHERE MechID=v_MechID FOR UPDATE;
 SELECT ManifestStatus INTO v_Status FROM DeploymentManifest
 WHERE SerialID=p_SerialID FOR UPDATE;
 IF v_Status <> 'Match Booked' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only booked deployments can be cancelled';
 END IF;
 UPDATE DeploymentManifest SET ManifestStatus='Cancelled' WHERE SerialID=p_SerialID;
 SELECT COUNT(*) INTO v_CriticalCount
 FROM MaintenanceIncident
 WHERE MechID=v_MechID AND Severity='Critical' AND RepairStatus<>'Repaired';
 IF v_CriticalCount>0 THEN
  UPDATE MechInventory SET OperationalStatus='Unavailable',
   LastStatusUpdate=CURRENT_TIMESTAMP WHERE MechID=v_MechID;
 END IF;
 COMMIT;
END$$

CREATE PROCEDURE StartDeployment(IN p_SerialID INT UNSIGNED)
BEGIN
 DECLARE v_MechID INT UNSIGNED DEFAULT NULL;
 DECLARE v_LockedMechID INT UNSIGNED DEFAULT NULL;
 DECLARE v_Status VARCHAR(30) DEFAULT NULL;
 DECLARE v_InventoryStatus VARCHAR(20) DEFAULT NULL;
 DECLARE v_ScheduledStart DATETIME;
 DECLARE v_ScheduledReturn DATETIME;
 DECLARE v_CriticalCount INT DEFAULT 0;
 DECLARE v_ActiveCount INT DEFAULT 0;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT MechID INTO v_MechID FROM DeploymentManifest WHERE SerialID=p_SerialID;
 IF v_MechID IS NULL THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deployment not found';
 END IF;
 SELECT MechID INTO v_LockedMechID FROM Mech WHERE MechID=v_MechID FOR UPDATE;
 SELECT ManifestStatus,ScheduledStart,ScheduledReturn
 INTO v_Status,v_ScheduledStart,v_ScheduledReturn
 FROM DeploymentManifest WHERE SerialID=p_SerialID FOR UPDATE;
 IF v_Status<>'Match Booked' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only booked deployments can be started';
 END IF;
 IF CURRENT_TIMESTAMP<v_ScheduledStart THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deployment cannot start before scheduled time';
 END IF;
 IF CURRENT_TIMESTAMP>=v_ScheduledReturn THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Scheduled deployment window has expired';
 END IF;
 SELECT OperationalStatus INTO v_InventoryStatus FROM MechInventory WHERE MechID=v_MechID;
 IF v_InventoryStatus IS NULL OR v_InventoryStatus<>'Available' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Mech is operationally unavailable';
 END IF;
 SELECT COUNT(*) INTO v_CriticalCount FROM MaintenanceIncident
 WHERE MechID=v_MechID AND Severity='Critical' AND RepairStatus<>'Repaired';
 IF v_CriticalCount>0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Critical maintenance must be resolved';
 END IF;
 SELECT COUNT(*) INTO v_ActiveCount FROM DeploymentManifest
 WHERE MechID=v_MechID AND ManifestStatus='Active in Arena';
 IF v_ActiveCount>0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Mech is already active in the arena';
 END IF;
 UPDATE DeploymentManifest SET ActualStart=CURRENT_TIMESTAMP,
  ManifestStatus='Active in Arena' WHERE SerialID=p_SerialID;
 COMMIT;
END$$

CREATE PROCEDURE CompleteDeployment(IN p_SerialID INT UNSIGNED)
BEGIN
 DECLARE v_MechID INT UNSIGNED DEFAULT NULL;
 DECLARE v_LockedMechID INT UNSIGNED DEFAULT NULL;
 DECLARE v_Status VARCHAR(30);
 DECLARE v_ActualStart DATETIME;
 DECLARE v_ActualReturn DATETIME;
 DECLARE v_ReturnGarageID INT UNSIGNED;
 DECLARE v_DailyRate DECIMAL(10,2);
 DECLARE v_DurationMinutes INT;
 DECLARE v_ActualCost DECIMAL(12,2);
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT MechID INTO v_MechID FROM DeploymentManifest WHERE SerialID=p_SerialID;
 IF v_MechID IS NULL THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deployment not found';
 END IF;
 SELECT MechID INTO v_LockedMechID FROM Mech WHERE MechID=v_MechID FOR UPDATE;
 SELECT ManifestStatus,ActualStart,ReturnGarageID,AgreedDailyRate
 INTO v_Status,v_ActualStart,v_ReturnGarageID,v_DailyRate
 FROM DeploymentManifest WHERE SerialID=p_SerialID FOR UPDATE;
 IF v_Status<>'Active in Arena' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only active deployments can be completed';
 END IF;
 SET v_ActualReturn=CURRENT_TIMESTAMP;
 IF v_ActualStart IS NULL OR v_ActualReturn<=v_ActualStart THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid actual deployment duration';
 END IF;
 SET v_DurationMinutes=TIMESTAMPDIFF(MINUTE,v_ActualStart,v_ActualReturn);
 IF v_DurationMinutes<=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Deployment must last at least one full minute';
 END IF;
 SET v_ActualCost=ROUND(v_DailyRate*v_DurationMinutes/1440,2);
 UPDATE DeploymentManifest SET ActualReturn=v_ActualReturn,
  ActualCost=v_ActualCost,ManifestStatus='Completed'
 WHERE SerialID=p_SerialID;
 UPDATE Mech SET CombatHours=CombatHours+ROUND(v_DurationMinutes/60,2),
  GarageID=v_ReturnGarageID WHERE MechID=v_MechID;
 COMMIT;
END$$
DELIMITER ;

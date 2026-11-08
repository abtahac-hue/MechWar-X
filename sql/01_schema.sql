-- MechWar-X | Schema (MySQL 8)
-- RUN ONLY ON A FRESH DEVELOPMENT DATABASE.
-- Creates empty tables; does not alter an existing database.
CREATE DATABASE IF NOT EXISTS MechWarX;
USE MechWarX;

CREATE TABLE MechType (
 MechTypeID INT UNSIGNED AUTO_INCREMENT,
 TypeName VARCHAR(50) NOT NULL,
 PRIMARY KEY (MechTypeID),
 UNIQUE (TypeName)
);

CREATE TABLE BattleGarage (
 GarageID INT UNSIGNED AUTO_INCREMENT,
 GarageName VARCHAR(100) NOT NULL,
 GridAddress VARCHAR(255) NOT NULL,
 DispatchPhone VARCHAR(20) NOT NULL,
 PRIMARY KEY (GarageID)
);

CREATE TABLE PitCrewTechnician (
 StaffID INT UNSIGNED AUTO_INCREMENT,
 GarageID INT UNSIGNED NOT NULL,
 FullName VARCHAR(100) NOT NULL,
 PhoneNumber VARCHAR(20) NOT NULL,
 CorporateEmail VARCHAR(150) NOT NULL,
 PRIMARY KEY (StaffID),
 UNIQUE (CorporateEmail),
 CONSTRAINT fk_technician_garage FOREIGN KEY (GarageID)
 REFERENCES BattleGarage(GarageID) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE Mech (
 MechID INT UNSIGNED AUTO_INCREMENT,
 ChassisSerialNumber VARCHAR(50) NOT NULL,
 Manufacturer VARCHAR(100) NOT NULL,
 Model VARCHAR(100) NOT NULL,
 AssemblyYear SMALLINT UNSIGNED NOT NULL,
 ArmorColor VARCHAR(50) NOT NULL,
 DailyDeploymentRate DECIMAL(10,2) NOT NULL,
 CombatHours DECIMAL(10,2) NOT NULL DEFAULT 0.00,
 MechTypeID INT UNSIGNED NOT NULL,
 GarageID INT UNSIGNED NOT NULL,
 PRIMARY KEY (MechID),
 UNIQUE (ChassisSerialNumber),
 CONSTRAINT chk_mech_year CHECK (AssemblyYear > 0),
 CONSTRAINT chk_mech_rate CHECK (DailyDeploymentRate > 0),
 CONSTRAINT chk_mech_hours CHECK (CombatHours >= 0),
 CONSTRAINT fk_mech_type FOREIGN KEY (MechTypeID)
 REFERENCES MechType(MechTypeID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_mech_garage FOREIGN KEY (GarageID)
 REFERENCES BattleGarage(GarageID) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE MechInventory (
 MechID INT UNSIGNED NOT NULL,
 OperationalStatus VARCHAR(20) NOT NULL DEFAULT 'Available',
 LastStatusUpdate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (MechID),
 CONSTRAINT chk_inventory_status CHECK (OperationalStatus IN ('Available', 'Unavailable')),
 CONSTRAINT fk_inventory_mech FOREIGN KEY (MechID)
 REFERENCES Mech(MechID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Client (
 ClientID INT UNSIGNED AUTO_INCREMENT,
 FirstName VARCHAR(50) NOT NULL,
 LastName VARCHAR(50) NOT NULL,
 CorporateAddress VARCHAR(255) NOT NULL,
 PhoneNumber VARCHAR(20) NOT NULL,
 Email VARCHAR(150) NOT NULL,
 PilotLicenseToken VARCHAR(100) NOT NULL,
 LicenseExpirationDate DATE NOT NULL,
 PRIMARY KEY (ClientID),
 UNIQUE (Email),
 UNIQUE (PilotLicenseToken)
);

CREATE TABLE DeploymentManifest (
 SerialID INT UNSIGNED AUTO_INCREMENT,
 ClientID INT UNSIGNED NOT NULL,
 MechID INT UNSIGNED NOT NULL,
 DepartureGarageID INT UNSIGNED NOT NULL,
 ReturnGarageID INT UNSIGNED NOT NULL,
 ScheduledStart DATETIME NOT NULL,
 ScheduledReturn DATETIME NOT NULL,
 ActualStart DATETIME NULL,
 ActualReturn DATETIME NULL,
 AgreedDailyRate DECIMAL(10,2) NOT NULL,
 EstimatedCost DECIMAL(12,2) NOT NULL,
 ActualCost DECIMAL(12,2) NULL,
 ManifestStatus VARCHAR(30) NOT NULL DEFAULT 'Match Booked',
 PRIMARY KEY (SerialID),
 CONSTRAINT fk_manifest_client FOREIGN KEY (ClientID)
 REFERENCES Client(ClientID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_manifest_mech FOREIGN KEY (MechID)
 REFERENCES Mech(MechID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_manifest_departure_garage FOREIGN KEY (DepartureGarageID)
 REFERENCES BattleGarage(GarageID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_manifest_return_garage FOREIGN KEY (ReturnGarageID)
 REFERENCES BattleGarage(GarageID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT chk_manifest_schedule CHECK (ScheduledReturn > ScheduledStart),
 CONSTRAINT chk_manifest_actual_times CHECK (
  ActualReturn IS NULL OR (ActualStart IS NOT NULL AND ActualReturn > ActualStart)
 ),
 CONSTRAINT chk_manifest_rate CHECK (AgreedDailyRate > 0),
 CONSTRAINT chk_manifest_estimated_cost CHECK (EstimatedCost >= 0),
 CONSTRAINT chk_manifest_actual_cost CHECK (ActualCost IS NULL OR ActualCost >= 0),
 CONSTRAINT chk_manifest_status CHECK (ManifestStatus IN (
  'Match Booked', 'Active in Arena', 'Completed', 'Cancelled', 'Destroyed/Cancelled'
 ))
);

CREATE TABLE MaintenanceIncident (
 IncidentID INT UNSIGNED AUTO_INCREMENT,
 MechID INT UNSIGNED NOT NULL,
 StaffID INT UNSIGNED NOT NULL,
 ReportedByClientID INT UNSIGNED NULL,
 IncidentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 IssueType VARCHAR(20) NOT NULL DEFAULT 'Routine',
 IncidentDescription TEXT NOT NULL,
 Severity VARCHAR(20) NOT NULL,
 RepairStatus VARCHAR(20) NOT NULL DEFAULT 'Reported',
 EngineeringNotes TEXT NULL,
 RepairCompletedDate DATETIME NULL,
 PRIMARY KEY (IncidentID),
 CONSTRAINT fk_incident_mech FOREIGN KEY (MechID)
 REFERENCES Mech(MechID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_incident_technician FOREIGN KEY (StaffID)
 REFERENCES PitCrewTechnician(StaffID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT fk_incident_client FOREIGN KEY (ReportedByClientID)
 REFERENCES Client(ClientID) ON DELETE RESTRICT ON UPDATE CASCADE,
 CONSTRAINT chk_incident_issue_type CHECK (IssueType IN ('Routine','Critical')),
 CONSTRAINT chk_incident_severity CHECK (Severity IN ('Low','Medium','High','Critical')),
 CONSTRAINT chk_incident_repair_status CHECK (RepairStatus IN (
  'Reported','In-Progress','Awaiting Parts','Repaired','Open','In Progress'
 )),
 CONSTRAINT chk_incident_repair_date CHECK (
  (RepairStatus = 'Repaired' AND RepairCompletedDate IS NOT NULL
   AND RepairCompletedDate >= IncidentDate)
  OR (RepairStatus <> 'Repaired' AND RepairCompletedDate IS NULL)
 )
);

-- MechWar-X | OPTIONAL DEMO SEED
-- Use ONLY on a fresh, empty development database after 01_schema.sql.
-- Fictional sample records; no personal credentials or real customer information.
USE MechWarX;

INSERT INTO MechType (TypeName) VALUES
 ('Light Scout'),('Assault Brawler'),('Heavy Artillery'),('Juggernaut');

INSERT INTO BattleGarage (GarageName,GridAddress,DispatchPhone) VALUES
 ('Neo-Prime Central Garage','Sector A-101','305-555-0101'),
 ('Eastern Combat Hangar','Sector E-205','305-555-0102'),
 ('Western Defense Garage','Sector W-310','305-555-0103'),
 ('Northern Repair Station','Sector N-415','305-555-0104');

INSERT INTO PitCrewTechnician
 (GarageID,FullName,PhoneNumber,CorporateEmail) VALUES
 (1,'Alex Morgan','305-555-0201','alex.morgan@neoprime.example'),
 (1,'Jordan Lee','305-555-0202','jordan.lee@neoprime.example'),
 (2,'Taylor Brooks','305-555-0203','taylor.brooks@neoprime.example'),
 (3,'Casey Rivera','305-555-0204','casey.rivera@neoprime.example'),
 (4,'Morgan Ellis','305-555-0205','morgan.ellis@neoprime.example');

INSERT INTO Mech
 (ChassisSerialNumber,Manufacturer,Model,AssemblyYear,ArmorColor,
  DailyDeploymentRate,MechTypeID,GarageID) VALUES
 ('NP-LS-1001','Titan Dynamics','Phantom X1',2025,'Black',1500.00,1,1),
 ('NP-AB-1002','IronCore Industries','Destroyer V2',2024,'Red',2800.00,2,2),
 ('NP-HA-1003','Nova Robotics','Thunderstrike',2026,'Silver',3500.00,3,3);

INSERT INTO MechInventory(MechID)
 SELECT m.MechID FROM Mech m
 LEFT JOIN MechInventory i ON i.MechID=m.MechID
 WHERE i.MechID IS NULL;

INSERT INTO Client
 (FirstName,LastName,CorporateAddress,PhoneNumber,Email,
  PilotLicenseToken,LicenseExpirationDate) VALUES
 ('Ethan','Carter','101 Neo-Prime Plaza','305-555-0301',
  'ethan@neoprime.example','PILOT-NP-1001','2028-12-31'),
 ('Sophia','Mitchell','205 Eastern Arena','305-555-0302',
  'sophia@neoprime.example','PILOT-NP-1002','2029-06-30'),
 ('Liam','Anderson','310 Western District','305-555-0303',
  'liam@neoprime.example','PILOT-NP-1003','2028-09-15');

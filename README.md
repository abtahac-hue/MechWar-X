# ◈ MechWar-X | Neo-Prime Command

**A neon-styled desktop command center for managing a futuristic mech fleet.**

MechWar-X is a database-driven desktop application created for an FIU database systems group project. It combines a **Python / CustomTkinter** interface with a **MySQL 8** relational database to manage machine registration, deployment schedules, and maintenance records.

### At a glance

| Area | What it does |
| --- | --- |
| **Command Center** | Displays live counts of registered mechs, deployment manifests, and maintenance incidents |
| **Mech Registration** | Validates mech specifications and inserts records into `Mech` and `MechInventory` in one transaction |
| **Deployment Search** | Retrieves real deployment manifests for a specified client |
| **Deployment Booking** | Calls the database's `BookDeployment` stored procedure to create a booking |
| **Maintenance Console** | Lists incidents and updates unresolved repairs |
| **Visual design** | Dark neon interface with blue, purple, and pink aurora animation |

## Interface

The application includes five sidebar screens: **Dashboard**, **Mech Registration**, **Deployment Search**, **Book Deployment**, and **Maintenance Console**.

*Screenshots of the dashboard and workflows will be added after final review.*

## Tech stack

- **Language:** Python 3
- **Desktop GUI:** CustomTkinter + Tkinter
- **Database:** MySQL 8
- **Database driver:** mysql-connector-python
- **Configuration:** python-dotenv
- **Architecture:** UI (`main.py`) → database operations (`mechwarx_operations.py`) → connection utility (`db_connection.py`) → MySQL

## Repository files

```text
MechWar-X/
├── main.py                 # Desktop GUI and screen navigation
├── mechwarx_operations.py  # Registration, search, booking, and repairs
├── db_connection.py        # MySQL connection and dashboard counts
├── requirements.txt        # Python dependencies
├── .env.example            # Placeholder database settings
└── .gitignore              # Excludes credentials and local files
```

## Run locally

**Prerequisites:** Python 3, a running MySQL 8 server, and a database named `MechWarX` with the expected tables and stored procedures.

1. Clone the repository:

   ```bash
   git clone https://github.com/abtahac-hue/MechWar-X.git
   cd MechWar-X
   ```

2. Install the required packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, then fill in **your own local MySQL credentials**:

   ```dotenv
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   DB_NAME=MechWarX
   ```

4. Import the project's MySQL schema and stored procedures (including `BookDeployment`). **The schema/scripts are not yet included in this repository**, so a clean installation requires them separately.

5. Start the desktop app:

   ```bash
   python main.py
   ```

> **Note:** The dashboard needs MySQL to be running. Registration, booking, and repair actions write to the database. Work against a development database and back it up before testing changes.

## Database design

The application works with the following related tables:

`MechType` · `BattleGarage` · `Mech` · `MechInventory` · `Client` · `DeploymentManifest` · `MaintenanceIncident` · `PitCrewTechnician`

Key database features include foreign-key relationships, transactional registration, stored-procedure-driven deployment booking, and maintenance state updates.

## Testing status

The application has been launched locally with MySQL connected. The dashboard, deployment search, maintenance incident listing, registration, and a successful deployment booking have been exercised manually.

**Still to verify:** rejection of an overlapping second booking, updating a currently unresolved incident, automated tests, and a clean-machine installation.

## Security

- `.env` is excluded from Git and must never be committed.
- Raw MySQL `.ibd` files, local database backups, and Python caches are excluded.
- The included `.env.example` contains placeholders only.
- Use the principle of least privilege when creating a local MySQL account.

## Academic project

Built as an **FIU database systems group project** and developed as a portfolio demonstration of relational database design, desktop application integration, validation, and data-driven user interfaces.

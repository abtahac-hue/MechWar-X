# MechWar-X | Neo-Prime Command

A futuristic desktop fleet-management application built with **Python**, **CustomTkinter**, and **MySQL** for a database systems course project.

## Features

- **Command Center:** live counts for mechs, deployment manifests, and maintenance incidents.
- **Mech Registration:** input validation and database-backed registration.
- **Deployment Search:** look up deployment manifests by client.
- **Book Deployment:** schedule deployments using MySQL stored procedures and business rules.
- **Maintenance Console:** review maintenance incidents and record repairs.
- **Interface:** dark neon dashboard with animated aurora accents.

## Technology

Python · CustomTkinter · Tkinter · MySQL Connector/Python · MySQL · python-dotenv

## Getting started

1. Install **Python 3** and **MySQL 8**.
2. Obtain the application source files (`main.py`, `mechwarx_operations.py`, and `db_connection.py`) and the database schema.
3. Install dependencies:

   ```bash
   pip install customtkinter mysql-connector-python python-dotenv
   ```

4. Create a local `.env` file (never commit it):

   ```dotenv
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   DB_NAME=MechWarX
   ```

5. Create the database tables and required stored procedures from the project's SQL scripts.
6. Run:

   ```bash
   python main.py
   ```

> The app requires a running MySQL instance. Some operations update actual database records; test against a backed-up development database.

## Project status

The desktop GUI has been launched and its database-connected dashboard, search, registration, and booking flows have been exercised locally. Full automated testing and installation from a clean machine are still pending.

## Security

This repository excludes `.env`, raw MySQL table files, local backups, and Python caches. Use `.env.example` to document configuration, never real credentials.

## Screenshots

Dashboard and workflow screenshots will be added here.


import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "MechWarX"),
        connection_timeout=5
    )


def get_dashboard_stats():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM Mech")
            total_mechs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM DeploymentManifest")
            total_deployments = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM MaintenanceIncident")
            total_incidents = cursor.fetchone()[0]

            return {
                "mechs": total_mechs,
                "deployments": total_deployments,
                "incidents": total_incidents
            }
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        stats = get_dashboard_stats()
        print("DATABASE CONNECTION SUCCESSFUL!")
        print(stats)
    except mysql.connector.Error as error:
        print(f"Database connection failed: {error}")

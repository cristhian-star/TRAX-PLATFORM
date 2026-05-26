from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "trax.db"

COLUMNS = {
    "professional_user_id": "INTEGER",
    "accepted_at": "DATETIME",
    "started_at": "DATETIME",
    "completed_at": "DATETIME",
    "confirmed_at": "DATETIME",
    "cancelled_at": "DATETIME",
}

LEGACY_STATES = {
    "PENDIENTE": "CREADA",
    "ACEPTADO": "ACEPTADA",
    "EN_PROCESO": "EN_PROGRESO",
    "FINALIZADO": "COMPLETADA",
    "CANCELADO": "CANCELADA",
}


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB no encontrada: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(contract_requests)")
        table_info = cursor.fetchall()
        if not table_info:
            raise SystemExit("La tabla contract_requests no existe en la DB activa")

        existing = {row[1] for row in table_info}
        added = []
        for column_name, definition in COLUMNS.items():
            if column_name in existing:
                continue
            cursor.execute(
                f"ALTER TABLE contract_requests ADD COLUMN {column_name} {definition}"
            )
            added.append(column_name)

        for old_state, new_state in LEGACY_STATES.items():
            cursor.execute(
                "UPDATE contract_requests SET estado = ? WHERE estado = ?",
                (new_state, old_state),
            )

        cursor.execute(
            """
            UPDATE contract_requests
            SET professional_user_id = (
                SELECT professionals.user_id
                FROM professionals
                WHERE professionals.id = contract_requests.professional_id
            )
            WHERE professional_user_id IS NULL
            """
        )
        connection.commit()

    if added:
        print("Columnas agregadas: " + ", ".join(added))
    else:
        print("No hay columnas faltantes.")
    print("Estados legacy y ownership profesional normalizados cuando fue posible.")


if __name__ == "__main__":
    main()

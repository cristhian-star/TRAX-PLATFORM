from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "trax.db"

COLUMNS = {
    "estado": "TEXT NOT NULL DEFAULT 'ACTIVO'",
    "motivo_estado": "TEXT",
}


def table_exists(cursor, table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB no encontrada: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()

        if not table_exists(cursor, "users"):
            raise SystemExit("La tabla users no existe en la DB activa")

        current_columns = existing_columns(cursor, "users")
        added_columns = []

        for column_name, column_definition in COLUMNS.items():
            if column_name in current_columns:
                continue

            cursor.execute(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
            )
            added_columns.append(column_name)

        connection.commit()

    if added_columns:
        print("Columnas agregadas: " + ", ".join(added_columns))
    else:
        print("No hay columnas faltantes. Migracion ya aplicada.")


if __name__ == "__main__":
    main()

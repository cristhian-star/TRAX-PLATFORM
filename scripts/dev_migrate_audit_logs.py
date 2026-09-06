from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "trax.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER NOT NULL,
    target_user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT,
    FOREIGN KEY(actor_user_id) REFERENCES users(id),
    FOREIGN KEY(target_user_id) REFERENCES users(id)
)
"""


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB no encontrada: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(CREATE_TABLE_SQL)
        connection.commit()

    print("Tabla audit_logs disponible. Migracion aplicada de forma idempotente.")


if __name__ == "__main__":
    main()

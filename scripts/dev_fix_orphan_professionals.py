from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "trax.db"


def _normalized(value):
    return (value or "").strip().casefold()


def _columns(connection, table_name):
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _available_user(connection, user_id, professional_id):
    existing = connection.execute(
        "SELECT id FROM professionals WHERE user_id = ? AND id <> ?",
        (user_id, professional_id),
    ).fetchone()
    return existing is None


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB no encontrada: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        professional_columns = _columns(connection, "professionals")
        user_columns = _columns(connection, "users")

        if "user_id" not in professional_columns:
            raise SystemExit(
                "La columna professionals.user_id no existe. Ejecuta primero la migracion de ownership."
            )

        if not {"id", "nombre", "email"}.issubset(user_columns):
            raise SystemExit("La tabla users no contiene las columnas requeridas.")

        select_fields = "id, nombre, servicio, zona"
        can_match_email = "email" in professional_columns
        if can_match_email:
            select_fields += ", email"

        orphans = connection.execute(
            f"SELECT {select_fields} FROM professionals WHERE user_id IS NULL ORDER BY id"
        ).fetchall()

        if not orphans:
            print("No hay profesionales sin owner.")
            return

        print(f"Profesionales sin owner: {len(orphans)}")
        if not can_match_email:
            print(
                "La tabla professionals no tiene email; nombre por si solo no prueba ownership. "
                "Se informaran candidatos, sin asociarlos automaticamente."
            )

        linked = 0
        pending = 0

        for professional in orphans:
            linked_by_email = False
            if can_match_email and _normalized(professional["email"]):
                email_candidates = connection.execute(
                    "SELECT id, nombre, email FROM users WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))",
                    (professional["email"],),
                ).fetchall()
                safe_candidates = [
                    user for user in email_candidates
                    if _available_user(connection, user["id"], professional["id"])
                ]
                if len(safe_candidates) == 1:
                    user = safe_candidates[0]
                    cursor = connection.execute(
                        "UPDATE professionals SET user_id = ? WHERE id = ? AND user_id IS NULL",
                        (user["id"], professional["id"]),
                    )
                    if cursor.rowcount:
                        linked += 1
                        linked_by_email = True
                        print(
                            f"ASOCIADO professional #{professional['id']} -> user #{user['id']} "
                            f"por email unico ({user['email']})."
                        )

            if linked_by_email:
                continue

            name_candidates = connection.execute(
                "SELECT id, nombre, email FROM users "
                "WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?)) AND rol = 'PROFESIONAL'",
                (professional["nombre"],),
            ).fetchall()
            name_candidates = [
                user for user in name_candidates
                if _available_user(connection, user["id"], professional["id"])
            ]

            pending += 1
            profile_label = (
                f"professional #{professional['id']} '{professional['nombre']}' "
                f"({professional['servicio']}, {professional['zona']})"
            )
            if len(name_candidates) == 1:
                candidate = name_candidates[0]
                print(
                    f"ORPHAN {profile_label}: candidato por nombre user #{candidate['id']} "
                    f"({candidate['email']}); confirmar manualmente."
                )
            elif len(name_candidates) > 1:
                candidate_ids = ", ".join(str(user["id"]) for user in name_candidates)
                print(
                    f"ORPHAN {profile_label}: multiples candidatos por nombre "
                    f"(users {candidate_ids}); reparacion manual."
                )
            else:
                print(f"ORPHAN {profile_label}: sin candidato seguro; reparacion manual.")

        connection.commit()
        print(f"Asociados automaticamente: {linked}. Pendientes manuales: {pending}.")


if __name__ == "__main__":
    main()

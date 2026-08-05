"""contract reviews and neutral reputation integrity

Revision ID: 20260726_06
Revises: 20260726_05
Create Date: 2026-08-04
"""

import hashlib
import json

from alembic import op
import sqlalchemy as sa

from app.domain.legacy_review_migration_adapter import (
    classify_legacy_review_rows,
)


revision = "20260726_06"
down_revision = "20260726_05"
branch_labels = None
depends_on = None


MIGRATION_MARKER = "20260726_06"

REVIEW_GUARD_FUNCTION = "trax_guard_contract_review_write_v1"
REVIEW_GUARD_TRIGGER = "trg_reviews_contract_integrity_v1"
REVIEW_INSERT_TRIGGER = "trg_reviews_contract_integrity_insert_v1"
REVIEW_UPDATE_TRIGGER = "trg_reviews_contract_integrity_update_v1"

REPUTATION_GUARD_FUNCTION = "trax_guard_reputation_event_write_v1"
REPUTATION_GUARD_TRIGGER = "trg_reputation_events_integrity_v1"
REPUTATION_INSERT_TRIGGER = "trg_reputation_events_integrity_insert_v1"
REPUTATION_UPDATE_TRIGGER = "trg_reputation_events_integrity_update_v1"

REVIEW_NEW_COLUMNS = {
    "contract_id",
    "comment_public",
    "origin",
    "verification_status",
    "comment_visibility_status",
    "rating_eligibility_status",
    "correlation_id",
    "payload_hash",
    "legacy_metadata_json",
    "moderated_by_user_id",
    "moderated_at",
    "moderation_reason",
}
REPUTATION_NEW_COLUMNS = {
    "review_id",
    "contract_id",
    "source_type",
    "event_type",
    "event_value",
    "origin",
    "correlation_id",
}

OWN_OBJECT_NAMES = {
    "uq_reviews_contract_id",
    "ck_reviews_origin",
    "ck_reviews_verification_status",
    "ck_reviews_comment_visibility_status",
    "ck_reviews_rating_eligibility_status",
    "ck_reviews_contractual_integrity",
    "ck_reviews_rating_eligible_integrity",
    "fk_reviews_contract_id",
    "fk_reviews_moderated_by_user_id",
    "ix_reviews_contract_id",
    "ix_reviews_correlation_id",
    "uq_reputation_events_review_id",
    "ck_reputation_events_source_type",
    "ck_reputation_events_origin",
    "ck_reputation_events_contract_review_integrity",
    "fk_reputation_events_review_id",
    "fk_reputation_events_contract_id",
    "ix_reputation_events_contract_id",
    "ix_reputation_events_correlation_id",
    REVIEW_GUARD_TRIGGER,
    REVIEW_INSERT_TRIGGER,
    REVIEW_UPDATE_TRIGGER,
    REPUTATION_GUARD_TRIGGER,
    REPUTATION_INSERT_TRIGGER,
    REPUTATION_UPDATE_TRIGGER,
}


def _json_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat(timespec="microseconds")
    return value


def _checksum(rows, fields):
    payload = [
        {field: _json_value(row[field]) for field in fields}
        for row in sorted(rows, key=lambda item: item["id"])
    ]
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


REVIEW_SOURCE_FIELDS = (
    "id",
    "cliente_id",
    "professional_id",
    "rating",
    "comentario",
    "estado",
    "created_at",
)
EVENT_SOURCE_FIELDS = (
    "id",
    "user_id",
    "tipo_evento",
    "puntos",
    "descripcion",
    "created_at",
)


def _trigger_names(bind):
    if bind.dialect.name == "postgresql":
        return {
            row[0]
            for row in bind.execute(
                sa.text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE NOT tgisinternal"
                )
            )
        }
    if bind.dialect.name == "sqlite":
        return {
            row[0]
            for row in bind.execute(
                sa.text(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                )
            )
        }
    return set()


def _object_names(inspector, table_name):
    names = {
        item.get("name")
        for getter in (
            inspector.get_indexes,
            inspector.get_unique_constraints,
            inspector.get_check_constraints,
            inspector.get_foreign_keys,
        )
        for item in getter(table_name)
        if item.get("name")
    }
    return names


def _rows_for_upgrade(bind):
    reviews = bind.execute(
        sa.text(
            "SELECT id, cliente_id, professional_id, rating, comentario, "
            "estado, created_at FROM reviews ORDER BY id"
        ).columns(
            id=sa.Integer(),
            cliente_id=sa.Integer(),
            professional_id=sa.Integer(),
            rating=sa.Integer(),
            comentario=sa.Text(),
            estado=sa.String(50),
            created_at=sa.DateTime(),
        )
    ).mappings().all()
    contracts = bind.execute(
        sa.text(
            "SELECT id, cliente_id, professional_id, estado, "
            "fecha_creacion, confirmed_at FROM contract_requests ORDER BY id"
        ).columns(
            id=sa.Integer(),
            cliente_id=sa.Integer(),
            professional_id=sa.Integer(),
            estado=sa.String(50),
            fecha_creacion=sa.DateTime(),
            confirmed_at=sa.DateTime(),
        )
    ).mappings().all()
    events = bind.execute(
        sa.text(
            "SELECT id, user_id, tipo_evento, puntos, descripcion, "
            "created_at FROM reputation_events ORDER BY id"
        ).columns(
            id=sa.Integer(),
            user_id=sa.Integer(),
            tipo_evento=sa.String(80),
            puntos=sa.Integer(),
            descripcion=sa.Text(),
            created_at=sa.DateTime(),
        )
    ).mappings().all()
    return reviews, contracts, events


def _preflight_upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    required_tables = {
        "reviews",
        "reputation_events",
        "contract_requests",
        "professionals",
        "users",
    }
    missing_tables = required_tables - set(inspector.get_table_names())
    if missing_tables:
        raise RuntimeError(
            "Upgrade bloqueado: faltan tablas requeridas: "
            + ", ".join(sorted(missing_tables))
        )

    review_columns = {
        column["name"]: column
        for column in inspector.get_columns("reviews")
    }
    event_columns = {
        column["name"]: column
        for column in inspector.get_columns("reputation_events")
    }
    required_review_columns = set(REVIEW_SOURCE_FIELDS)
    required_event_columns = set(EVENT_SOURCE_FIELDS)
    if not required_review_columns.issubset(review_columns):
        raise RuntimeError("Upgrade bloqueado: estructura legacy de reviews incompleta.")
    if not required_event_columns.issubset(event_columns):
        raise RuntimeError(
            "Upgrade bloqueado: estructura legacy de reputation_events incompleta."
        )
    if REVIEW_NEW_COLUMNS & set(review_columns):
        raise RuntimeError("Upgrade bloqueado: reviews contiene columnas parciales de 20260726_06.")
    if REPUTATION_NEW_COLUMNS & set(event_columns):
        raise RuntimeError(
            "Upgrade bloqueado: reputation_events contiene columnas parciales de 20260726_06."
        )
    if review_columns["rating"]["nullable"]:
        raise RuntimeError("Upgrade bloqueado: reviews.rating no coincide con 20260726_05.")
    if event_columns["puntos"]["nullable"]:
        raise RuntimeError(
            "Upgrade bloqueado: reputation_events.puntos no coincide con 20260726_05."
        )

    existing_objects = (
        _object_names(inspector, "reviews")
        | _object_names(inspector, "reputation_events")
        | _trigger_names(bind)
    )
    collisions = OWN_OBJECT_NAMES & existing_objects
    if collisions:
        raise RuntimeError(
            "Upgrade bloqueado: objetos fisicos reservados ya existen: "
            + ", ".join(sorted(collisions))
        )

    reviews, contracts, events = _rows_for_upgrade(bind)
    user_ids = {
        row[0]
        for row in bind.execute(sa.text("SELECT id FROM users"))
    }
    professional_ids = {
        row[0]
        for row in bind.execute(sa.text("SELECT id FROM professionals"))
    }
    orphan = next(
        (
            row["id"]
            for row in reviews
            if row["cliente_id"] not in user_ids
            or row["professional_id"] not in professional_ids
        ),
        None,
    )
    if orphan is not None:
        raise RuntimeError(
            "Upgrade bloqueado: review con identidad huerfana "
            f"(id={orphan})."
        )

    decisions = classify_legacy_review_rows(reviews, contracts)
    decision_by_id = {decision.review_id: decision for decision in decisions}
    plan = []
    for row in reviews:
        decision = decision_by_id[row["id"]]
        linked = decision.contract_id is not None
        valid_rating = row["rating"] in (1, 2, 3, 4, 5)
        visibility = {
            "VISIBLE": "VISIBLE",
            "OCULTA": "HIDDEN",
            "REPORTADA": "PENDING_MODERATION",
        }.get(row["estado"], "HIDDEN")
        derived = {
            "contract_id": decision.contract_id,
            "verification_status": "VERIFIED" if linked else "UNVERIFIED",
            "comment_public": row["comentario"],
            "comment_visibility_status": visibility,
            "rating_eligibility_status": (
                "ELIGIBLE" if linked and valid_rating else "EXCLUDED"
            ),
        }
        metadata = {
            "migration": MIGRATION_MARKER,
            "classification_code": decision.classification_code,
            "original_rating": row["rating"],
            "source_row_checksum": _checksum([row], REVIEW_SOURCE_FIELDS),
            "derived": derived,
        }
        plan.append(
            {
                "review_id": row["id"],
                "contract_id": decision.contract_id,
                "rating": row["rating"] if valid_rating else None,
                "comment_public": row["comentario"],
                "verification_status": derived["verification_status"],
                "comment_visibility_status": visibility,
                "rating_eligibility_status": derived[
                    "rating_eligibility_status"
                ],
                "legacy_metadata_json": metadata,
            }
        )
    return {
        "reviews": reviews,
        "events": events,
        "review_checksum": _checksum(reviews, REVIEW_SOURCE_FIELDS),
        "event_checksum": _checksum(events, EVENT_SOURCE_FIELDS),
        "plan": plan,
    }


def _add_columns():
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.add_column(sa.Column("contract_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("comment_public", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("origin", sa.String(20), nullable=True))
        batch_op.add_column(
            sa.Column("verification_status", sa.String(20), nullable=True)
        )
        batch_op.add_column(
            sa.Column("comment_visibility_status", sa.String(30), nullable=True)
        )
        batch_op.add_column(
            sa.Column("rating_eligibility_status", sa.String(20), nullable=True)
        )
        batch_op.add_column(sa.Column("correlation_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("payload_hash", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("legacy_metadata_json", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("moderated_by_user_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("moderated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("moderation_reason", sa.String(255), nullable=True)
        )
        batch_op.alter_column(
            "rating",
            existing_type=sa.Integer(),
            nullable=True,
        )

    with op.batch_alter_table("reputation_events") as batch_op:
        batch_op.add_column(sa.Column("review_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("contract_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("source_type", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("event_type", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("event_value", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("origin", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("correlation_id", sa.String(36), nullable=True))
        batch_op.alter_column(
            "puntos",
            existing_type=sa.Integer(),
            nullable=True,
        )


def _apply_legacy_plan(preflight):
    bind = op.get_bind()
    review_update = sa.text(
        "UPDATE reviews SET contract_id=:contract_id, rating=:rating, "
        "comment_public=:comment_public, origin='LEGACY', "
        "verification_status=:verification_status, "
        "comment_visibility_status=:comment_visibility_status, "
        "rating_eligibility_status=:rating_eligibility_status, "
        "legacy_metadata_json=:legacy_metadata_json WHERE id=:review_id"
    ).bindparams(
        sa.bindparam("legacy_metadata_json", type_=sa.JSON())
    )
    for item in preflight["plan"]:
        bind.execute(review_update, item)
    bind.execute(
        sa.text(
            "UPDATE reputation_events SET source_type='LEGACY_EVENT', "
            "origin='LEGACY'"
        )
    )

    migrated = bind.execute(
        sa.text(
            "SELECT id, cliente_id, professional_id, rating, comentario, "
            "estado, created_at, legacy_metadata_json FROM reviews ORDER BY id"
        ).columns(
            id=sa.Integer(),
            cliente_id=sa.Integer(),
            professional_id=sa.Integer(),
            rating=sa.Integer(),
            comentario=sa.Text(),
            estado=sa.String(50),
            created_at=sa.DateTime(),
            legacy_metadata_json=sa.JSON(),
        )
    ).mappings().all()
    restored = []
    for row in migrated:
        metadata = row["legacy_metadata_json"]
        if not isinstance(metadata, dict) or metadata.get("migration") != MIGRATION_MARKER:
            raise RuntimeError("Upgrade bloqueado: metadata de reconciliacion invalida.")
        restored.append(
            {
                **row,
                "rating": metadata["original_rating"],
            }
        )
    if _checksum(restored, REVIEW_SOURCE_FIELDS) != preflight["review_checksum"]:
        raise RuntimeError("Upgrade bloqueado: checksum de reviews no reconcilia.")

    _, _, events = _rows_for_upgrade(bind)
    if _checksum(events, EVENT_SOURCE_FIELDS) != preflight["event_checksum"]:
        raise RuntimeError(
            "Upgrade bloqueado: checksum de reputation_events no reconcilia."
        )


def _create_constraints_and_indexes():
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.create_foreign_key(
            "fk_reviews_contract_id",
            "contract_requests",
            ["contract_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_reviews_moderated_by_user_id",
            "users",
            ["moderated_by_user_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_reviews_contract_id",
            ["contract_id"],
        )
        batch_op.create_check_constraint(
            "ck_reviews_origin",
            "origin IS NULL OR origin IN ('CONTRACTUAL', 'LEGACY')",
        )
        batch_op.create_check_constraint(
            "ck_reviews_verification_status",
            "verification_status IS NULL OR verification_status IN ('VERIFIED', 'UNVERIFIED')",
        )
        batch_op.create_check_constraint(
            "ck_reviews_comment_visibility_status",
            "comment_visibility_status IS NULL OR comment_visibility_status IN "
            "('VISIBLE', 'PENDING_MODERATION', 'HIDDEN', 'REDACTED')",
        )
        batch_op.create_check_constraint(
            "ck_reviews_rating_eligibility_status",
            "rating_eligibility_status IS NULL OR rating_eligibility_status IN ('ELIGIBLE', 'EXCLUDED')",
        )
        batch_op.create_check_constraint(
            "ck_reviews_contractual_integrity",
            "origin <> 'CONTRACTUAL' OR (contract_id IS NOT NULL AND "
            "verification_status = 'VERIFIED' AND rating BETWEEN 1 AND 5 AND "
            "correlation_id IS NOT NULL AND payload_hash IS NOT NULL)",
        )
        batch_op.create_check_constraint(
            "ck_reviews_rating_eligible_integrity",
            "rating_eligibility_status <> 'ELIGIBLE' OR ("
            "verification_status = 'VERIFIED' AND contract_id IS NOT NULL "
            "AND rating BETWEEN 1 AND 5)",
        )
        batch_op.create_index("ix_reviews_contract_id", ["contract_id"])
        batch_op.create_index("ix_reviews_correlation_id", ["correlation_id"])

    with op.batch_alter_table("reputation_events") as batch_op:
        batch_op.create_foreign_key(
            "fk_reputation_events_review_id",
            "reviews",
            ["review_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_reputation_events_contract_id",
            "contract_requests",
            ["contract_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_reputation_events_review_id",
            ["review_id"],
        )
        batch_op.create_check_constraint(
            "ck_reputation_events_source_type",
            "source_type IS NULL OR source_type IN ('CONTRACT_REVIEW', 'LEGACY_EVENT')",
        )
        batch_op.create_check_constraint(
            "ck_reputation_events_origin",
            "origin IS NULL OR origin IN ('CONTRACTUAL', 'LEGACY')",
        )
        batch_op.create_check_constraint(
            "ck_reputation_events_contract_review_integrity",
            "source_type <> 'CONTRACT_REVIEW' OR (review_id IS NOT NULL AND "
            "contract_id IS NOT NULL AND user_id IS NOT NULL AND "
            "correlation_id IS NOT NULL AND event_type = 'REVIEW_RECORDED' "
            "AND event_value BETWEEN 1 AND 5 AND origin = 'CONTRACTUAL' "
            "AND puntos IS NULL)",
        )
        batch_op.create_index(
            "ix_reputation_events_contract_id",
            ["contract_id"],
        )
        batch_op.create_index(
            "ix_reputation_events_correlation_id",
            ["correlation_id"],
        )


def _create_postgresql_triggers():
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {REVIEW_GUARD_FUNCTION}()
            RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE
                contract_row contract_requests%ROWTYPE;
                professional_user INTEGER;
            BEGIN
                IF TG_OP = 'INSERT' AND NEW.origin = 'LEGACY' THEN
                    RAISE EXCEPTION 'new LEGACY reviews are forbidden'
                        USING ERRCODE = '23514';
                END IF;
                IF TG_OP = 'UPDATE' AND (
                    NEW.contract_id IS DISTINCT FROM OLD.contract_id OR
                    NEW.cliente_id IS DISTINCT FROM OLD.cliente_id OR
                    NEW.professional_id IS DISTINCT FROM OLD.professional_id OR
                    NEW.rating IS DISTINCT FROM OLD.rating OR
                    NEW.comentario IS DISTINCT FROM OLD.comentario OR
                    NEW.origin IS DISTINCT FROM OLD.origin OR
                    NEW.payload_hash IS DISTINCT FROM OLD.payload_hash OR
                    NEW.created_at IS DISTINCT FROM OLD.created_at
                ) THEN
                    RAISE EXCEPTION 'review causal fields are immutable'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.origin = 'CONTRACTUAL' THEN
                    SELECT * INTO contract_row FROM contract_requests
                    WHERE id = NEW.contract_id;
                    IF NOT FOUND OR contract_row.estado <> 'CONFIRMADA'
                       OR contract_row.cliente_id <> NEW.cliente_id
                       OR contract_row.professional_id <> NEW.professional_id THEN
                        RAISE EXCEPTION 'contract review identity or state is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                    SELECT user_id INTO professional_user FROM professionals
                    WHERE id = NEW.professional_id;
                    IF professional_user IS NULL
                       OR professional_user <> contract_row.professional_user_id THEN
                        RAISE EXCEPTION 'contract professional identity is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER {REVIEW_GUARD_TRIGGER} BEFORE INSERT OR UPDATE "
            f"ON reviews FOR EACH ROW EXECUTE FUNCTION {REVIEW_GUARD_FUNCTION}()"
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {REPUTATION_GUARD_FUNCTION}()
            RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE
                review_row reviews%ROWTYPE;
                professional_user INTEGER;
            BEGIN
                IF TG_OP = 'INSERT' AND (
                    NEW.source_type = 'LEGACY_EVENT' OR NEW.puntos IS NOT NULL
                ) THEN
                    RAISE EXCEPTION 'new legacy or points reputation rows are forbidden'
                        USING ERRCODE = '23514';
                END IF;
                IF TG_OP = 'UPDATE' AND (
                    NEW.review_id IS DISTINCT FROM OLD.review_id OR
                    NEW.contract_id IS DISTINCT FROM OLD.contract_id OR
                    NEW.user_id IS DISTINCT FROM OLD.user_id OR
                    NEW.source_type IS DISTINCT FROM OLD.source_type OR
                    NEW.event_type IS DISTINCT FROM OLD.event_type OR
                    NEW.event_value IS DISTINCT FROM OLD.event_value OR
                    NEW.origin IS DISTINCT FROM OLD.origin OR
                    NEW.correlation_id IS DISTINCT FROM OLD.correlation_id OR
                    NEW.puntos IS DISTINCT FROM OLD.puntos OR
                    NEW.created_at IS DISTINCT FROM OLD.created_at
                ) THEN
                    RAISE EXCEPTION 'reputation event causal fields are immutable'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.source_type = 'CONTRACT_REVIEW' THEN
                    SELECT * INTO review_row FROM reviews WHERE id = NEW.review_id;
                    IF NOT FOUND OR review_row.origin <> 'CONTRACTUAL'
                       OR review_row.contract_id <> NEW.contract_id
                       OR review_row.correlation_id <> NEW.correlation_id
                       OR review_row.rating <> NEW.event_value THEN
                        RAISE EXCEPTION 'reputation event review identity is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                    SELECT user_id INTO professional_user FROM professionals
                    WHERE id = review_row.professional_id;
                    IF professional_user IS NULL OR professional_user <> NEW.user_id THEN
                        RAISE EXCEPTION 'reputation event professional is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                    IF NEW.puntos IS NOT NULL THEN
                        RAISE EXCEPTION 'contract review points are forbidden'
                            USING ERRCODE = '23514';
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER {REPUTATION_GUARD_TRIGGER} BEFORE INSERT OR UPDATE "
            "ON reputation_events FOR EACH ROW EXECUTE FUNCTION "
            f"{REPUTATION_GUARD_FUNCTION}()"
        )
    )


def _create_sqlite_triggers():
    review_identity = """
        NEW.origin = 'CONTRACTUAL' AND NOT EXISTS (
            SELECT 1 FROM contract_requests AS contract_row
            JOIN professionals AS professional_row
              ON professional_row.id = contract_row.professional_id
            WHERE contract_row.id = NEW.contract_id
              AND contract_row.estado = 'CONFIRMADA'
              AND contract_row.cliente_id = NEW.cliente_id
              AND contract_row.professional_id = NEW.professional_id
              AND professional_row.user_id IS NOT NULL
              AND professional_row.user_id = contract_row.professional_user_id
        )
    """
    op.execute(sa.text(f"""
        CREATE TRIGGER {REVIEW_INSERT_TRIGGER}
        BEFORE INSERT ON reviews FOR EACH ROW
        WHEN NEW.origin = 'LEGACY' OR ({review_identity})
        BEGIN
            SELECT RAISE(ABORT, 'contract review insert is invalid');
        END
    """))
    op.execute(sa.text(f"""
        CREATE TRIGGER {REVIEW_UPDATE_TRIGGER}
        BEFORE UPDATE ON reviews FOR EACH ROW
        WHEN NOT (NEW.contract_id IS OLD.contract_id)
          OR NOT (NEW.cliente_id IS OLD.cliente_id)
          OR NOT (NEW.professional_id IS OLD.professional_id)
          OR NOT (NEW.rating IS OLD.rating)
          OR NOT (NEW.comentario IS OLD.comentario)
          OR NOT (NEW.origin IS OLD.origin)
          OR NOT (NEW.payload_hash IS OLD.payload_hash)
          OR NOT (NEW.created_at IS OLD.created_at)
          OR ({review_identity})
        BEGIN
            SELECT RAISE(ABORT, 'review causal fields are immutable or invalid');
        END
    """))

    event_identity = """
        NEW.source_type = 'CONTRACT_REVIEW' AND NOT EXISTS (
            SELECT 1 FROM reviews AS review_row
            JOIN professionals AS professional_row
              ON professional_row.id = review_row.professional_id
            WHERE review_row.id = NEW.review_id
              AND review_row.origin = 'CONTRACTUAL'
              AND review_row.contract_id = NEW.contract_id
              AND review_row.correlation_id = NEW.correlation_id
              AND review_row.rating = NEW.event_value
              AND professional_row.user_id IS NOT NULL
              AND professional_row.user_id = NEW.user_id
              AND NEW.puntos IS NULL
        )
    """
    op.execute(sa.text(f"""
        CREATE TRIGGER {REPUTATION_INSERT_TRIGGER}
        BEFORE INSERT ON reputation_events FOR EACH ROW
        WHEN NEW.source_type = 'LEGACY_EVENT'
          OR NEW.puntos IS NOT NULL
          OR ({event_identity})
        BEGIN
            SELECT RAISE(ABORT, 'reputation event insert is invalid');
        END
    """))
    op.execute(sa.text(f"""
        CREATE TRIGGER {REPUTATION_UPDATE_TRIGGER}
        BEFORE UPDATE ON reputation_events FOR EACH ROW
        WHEN NOT (NEW.review_id IS OLD.review_id)
          OR NOT (NEW.contract_id IS OLD.contract_id)
          OR NOT (NEW.user_id IS OLD.user_id)
          OR NOT (NEW.source_type IS OLD.source_type)
          OR NOT (NEW.event_type IS OLD.event_type)
          OR NOT (NEW.event_value IS OLD.event_value)
          OR NOT (NEW.origin IS OLD.origin)
          OR NOT (NEW.correlation_id IS OLD.correlation_id)
          OR NOT (NEW.puntos IS OLD.puntos)
          OR NOT (NEW.created_at IS OLD.created_at)
          OR ({event_identity})
        BEGIN
            SELECT RAISE(ABORT, 'reputation event causal fields are immutable or invalid');
        END
    """))


def _create_triggers():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        _create_postgresql_triggers()
    elif dialect == "sqlite":
        _create_sqlite_triggers()
    else:
        raise RuntimeError(f"Dialecto no soportado para integridad fisica: {dialect}")


def upgrade():
    preflight = _preflight_upgrade()
    _add_columns()
    _apply_legacy_plan(preflight)
    _create_constraints_and_indexes()
    _create_triggers()


def _read_downgrade_reviews(bind):
    return bind.execute(
        sa.text(
            "SELECT id, cliente_id, professional_id, rating, comentario, "
            "estado, created_at, contract_id, comment_public, origin, "
            "verification_status, comment_visibility_status, "
            "rating_eligibility_status, legacy_metadata_json, "
            "moderated_by_user_id, moderated_at, moderation_reason "
            "FROM reviews ORDER BY id"
        ).columns(
            id=sa.Integer(),
            cliente_id=sa.Integer(),
            professional_id=sa.Integer(),
            rating=sa.Integer(),
            comentario=sa.Text(),
            estado=sa.String(50),
            created_at=sa.DateTime(),
            contract_id=sa.Integer(),
            comment_public=sa.Text(),
            origin=sa.String(20),
            verification_status=sa.String(20),
            comment_visibility_status=sa.String(30),
            rating_eligibility_status=sa.String(20),
            legacy_metadata_json=sa.JSON(),
            moderated_by_user_id=sa.Integer(),
            moderated_at=sa.DateTime(),
            moderation_reason=sa.String(255),
        )
    ).mappings().all()


def _preflight_downgrade():
    bind = op.get_bind()
    reviews = _read_downgrade_reviews(bind)
    if any(row["origin"] == "CONTRACTUAL" for row in reviews):
        raise RuntimeError("Downgrade bloqueado: existen reviews contractuales.")
    contractual_events = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM reputation_events "
            "WHERE source_type='CONTRACT_REVIEW'"
        )
    ).scalar_one()
    if contractual_events:
        raise RuntimeError(
            "Downgrade bloqueado: existen eventos reputacionales contractuales."
        )

    restored = []
    for row in reviews:
        metadata = row["legacy_metadata_json"]
        if not isinstance(metadata, dict) or metadata.get("migration") != MIGRATION_MARKER:
            raise RuntimeError(
                f"Downgrade bloqueado: metadata legacy ausente (review={row['id']})."
            )
        if (
            row["moderated_by_user_id"] is not None
            or row["moderated_at"] is not None
            or row["moderation_reason"] is not None
        ):
            raise RuntimeError(
                f"Downgrade bloqueado: existe moderacion posterior (review={row['id']})."
            )
        derived = metadata.get("derived") or {}
        for field in (
            "contract_id",
            "comment_public",
            "verification_status",
            "comment_visibility_status",
            "rating_eligibility_status",
        ):
            if row[field] != derived.get(field):
                raise RuntimeError(
                    f"Downgrade bloqueado: review legacy modificada (review={row['id']})."
                )
        original_rating = metadata.get("original_rating")
        if original_rating is None:
            raise RuntimeError(
                f"Downgrade bloqueado: rating original ausente (review={row['id']})."
            )
        restored_row = {**row, "rating": original_rating}
        if (
            _checksum([restored_row], REVIEW_SOURCE_FIELDS)
            != metadata.get("source_row_checksum")
        ):
            raise RuntimeError(
                f"Downgrade bloqueado: checksum legacy invalido (review={row['id']})."
            )
        restored.append({"review_id": row["id"], "rating": original_rating})
    return restored


def _drop_triggers():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {REPUTATION_GUARD_TRIGGER} ON reputation_events"))
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {REPUTATION_GUARD_FUNCTION}()"))
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {REVIEW_GUARD_TRIGGER} ON reviews"))
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {REVIEW_GUARD_FUNCTION}()"))
    elif bind.dialect.name == "sqlite":
        for name in (
            REPUTATION_UPDATE_TRIGGER,
            REPUTATION_INSERT_TRIGGER,
            REVIEW_UPDATE_TRIGGER,
            REVIEW_INSERT_TRIGGER,
        ):
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS {name}"))


def _drop_schema():
    with op.batch_alter_table("reputation_events") as batch_op:
        batch_op.drop_index("ix_reputation_events_correlation_id")
        batch_op.drop_index("ix_reputation_events_contract_id")
        batch_op.drop_constraint("ck_reputation_events_contract_review_integrity", type_="check")
        batch_op.drop_constraint("ck_reputation_events_origin", type_="check")
        batch_op.drop_constraint("ck_reputation_events_source_type", type_="check")
        batch_op.drop_constraint("uq_reputation_events_review_id", type_="unique")
        batch_op.drop_constraint("fk_reputation_events_contract_id", type_="foreignkey")
        batch_op.drop_constraint("fk_reputation_events_review_id", type_="foreignkey")
        for column in (
            "correlation_id",
            "origin",
            "event_value",
            "event_type",
            "source_type",
            "contract_id",
            "review_id",
        ):
            batch_op.drop_column(column)
        batch_op.alter_column("puntos", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_index("ix_reviews_correlation_id")
        batch_op.drop_index("ix_reviews_contract_id")
        batch_op.drop_constraint("ck_reviews_rating_eligible_integrity", type_="check")
        batch_op.drop_constraint("ck_reviews_contractual_integrity", type_="check")
        batch_op.drop_constraint("ck_reviews_rating_eligibility_status", type_="check")
        batch_op.drop_constraint("ck_reviews_comment_visibility_status", type_="check")
        batch_op.drop_constraint("ck_reviews_verification_status", type_="check")
        batch_op.drop_constraint("ck_reviews_origin", type_="check")
        batch_op.drop_constraint("uq_reviews_contract_id", type_="unique")
        batch_op.drop_constraint("fk_reviews_moderated_by_user_id", type_="foreignkey")
        batch_op.drop_constraint("fk_reviews_contract_id", type_="foreignkey")
        for column in (
            "moderation_reason",
            "moderated_at",
            "moderated_by_user_id",
            "legacy_metadata_json",
            "payload_hash",
            "correlation_id",
            "rating_eligibility_status",
            "comment_visibility_status",
            "verification_status",
            "origin",
            "comment_public",
            "contract_id",
        ):
            batch_op.drop_column(column)
        batch_op.alter_column("rating", existing_type=sa.Integer(), nullable=False)


def downgrade():
    restored = _preflight_downgrade()
    bind = op.get_bind()
    _drop_triggers()
    for item in restored:
        bind.execute(
            sa.text("UPDATE reviews SET rating=:rating WHERE id=:review_id"),
            item,
        )
    if bind.execute(sa.text("SELECT COUNT(*) FROM reviews WHERE rating IS NULL")).scalar_one():
        raise RuntimeError("Downgrade bloqueado: ratings legacy no reconciliados.")
    _drop_schema()

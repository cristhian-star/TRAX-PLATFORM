"""harden contract review discriminators

Revision ID: 20260726_07
Revises: 20260726_06
Create Date: 2026-08-04
"""

import importlib

from alembic import op
import sqlalchemy as sa

from app.domain.legacy_review_migration_adapter import (
    classify_legacy_review_rows_fail_closed,
)


revision = "20260726_07"
down_revision = "20260726_06"
branch_labels = None
depends_on = None


REVIEW_REQUIRED_CHECK = "ck_reviews_origin_required_v2"
EVENT_REQUIRED_CHECK = "ck_reputation_events_discriminators_required_v2"

REVIEW_FUNCTION = "trax_guard_contract_review_write_v2"
REVIEW_TRIGGER = "trg_reviews_contract_integrity_v2"
EVENT_FUNCTION = "trax_guard_reputation_event_write_v2"
EVENT_TRIGGER = "trg_reputation_events_integrity_v2"

V1_REVIEW_FUNCTION = "trax_guard_contract_review_write_v1"
V1_REVIEW_TRIGGER = "trg_reviews_contract_integrity_v1"
V1_REVIEW_INSERT_TRIGGER = "trg_reviews_contract_integrity_insert_v1"
V1_REVIEW_UPDATE_TRIGGER = "trg_reviews_contract_integrity_update_v1"
V1_EVENT_FUNCTION = "trax_guard_reputation_event_write_v1"
V1_EVENT_TRIGGER = "trg_reputation_events_integrity_v1"
V1_EVENT_INSERT_TRIGGER = "trg_reputation_events_integrity_insert_v1"
V1_EVENT_UPDATE_TRIGGER = "trg_reputation_events_integrity_update_v1"


def _trigger_names(bind):
    if bind.dialect.name == "postgresql":
        return {
            row[0]
            for row in bind.execute(
                sa.text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
            )
        }
    if bind.dialect.name == "sqlite":
        return {
            row[0]
            for row in bind.execute(
                sa.text("SELECT name FROM sqlite_master WHERE type='trigger'")
            )
        }
    raise RuntimeError(
        f"Dialecto no soportado para integridad fisica: {bind.dialect.name}"
    )


def _check_names(bind, table_name):
    return {
        item.get("name")
        for item in sa.inspect(bind).get_check_constraints(table_name)
        if item.get("name")
    }


def _legacy_reclassification_plan(bind):
    reviews = bind.execute(
        sa.text(
            "SELECT id, cliente_id, professional_id, rating, created_at, "
            "comment_public, comment_visibility_status, legacy_metadata_json "
            "FROM reviews WHERE origin='LEGACY' ORDER BY id"
        ).columns(legacy_metadata_json=sa.JSON())
    ).mappings().all()
    contracts = bind.execute(
        sa.text(
            "SELECT contract_row.id, contract_row.cliente_id, "
            "contract_row.professional_id, contract_row.professional_user_id, "
            "professional_row.user_id AS profile_user_id, contract_row.estado, "
            "contract_row.fecha_creacion, contract_row.confirmed_at "
            "FROM contract_requests AS contract_row "
            "LEFT JOIN professionals AS professional_row "
            "ON professional_row.id=contract_row.professional_id "
            "ORDER BY contract_row.id"
        )
    ).mappings().all()
    source_rows = []
    metadata_by_id = {}
    for row in reviews:
        metadata = row["legacy_metadata_json"]
        if not isinstance(metadata, dict) or metadata.get("migration") != "20260726_06":
            raise RuntimeError(
                "Upgrade bloqueado: metadata legacy no reconciliable "
                f"(review={row['id']})."
            )
        metadata_by_id[row["id"]] = metadata
        source_rows.append(
            {
                "id": row["id"],
                "cliente_id": row["cliente_id"],
                "professional_id": row["professional_id"],
                "rating": metadata.get("original_rating"),
                "created_at": row["created_at"],
            }
        )

    decisions = classify_legacy_review_rows_fail_closed(source_rows, contracts)
    rows_by_id = {row["id"]: row for row in reviews}
    plan = []
    for decision in decisions:
        row = rows_by_id[decision.review_id]
        metadata = dict(metadata_by_id[decision.review_id])
        linked = decision.contract_id is not None
        original_rating = metadata.get("original_rating")
        valid_rating = (
            isinstance(original_rating, int)
            and not isinstance(original_rating, bool)
            and original_rating in (1, 2, 3, 4, 5)
        )
        derived = dict(metadata.get("derived") or {})
        derived.update(
            {
                "contract_id": decision.contract_id,
                "comment_public": row["comment_public"],
                "verification_status": "VERIFIED" if linked else "UNVERIFIED",
                "comment_visibility_status": row["comment_visibility_status"],
                "rating_eligibility_status": (
                    "ELIGIBLE" if linked and valid_rating else "EXCLUDED"
                ),
            }
        )
        metadata["classification_code"] = decision.classification_code
        metadata["derived"] = derived
        plan.append(
            {
                "id": decision.review_id,
                "contract_id": decision.contract_id,
                "rating": original_rating if valid_rating else None,
                "verification_status": derived["verification_status"],
                "rating_eligibility_status": derived[
                    "rating_eligibility_status"
                ],
                "metadata": metadata,
            }
        )
    return plan


def _preflight_upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    required_tables = {
        "reviews",
        "reputation_events",
        "contract_requests",
        "professionals",
    }
    missing = required_tables - set(inspector.get_table_names())
    if missing:
        raise RuntimeError(
            "Upgrade bloqueado: faltan tablas requeridas: "
            + ", ".join(sorted(missing))
        )

    expected_v1 = (
        {V1_REVIEW_TRIGGER, V1_EVENT_TRIGGER}
        if bind.dialect.name == "postgresql"
        else {
            V1_REVIEW_INSERT_TRIGGER,
            V1_REVIEW_UPDATE_TRIGGER,
            V1_EVENT_INSERT_TRIGGER,
            V1_EVENT_UPDATE_TRIGGER,
        }
    )
    triggers = _trigger_names(bind)
    if not expected_v1.issubset(triggers):
        raise RuntimeError(
            "Upgrade bloqueado: defensas de 20260726_06 incompletas: "
            + ", ".join(sorted(expected_v1 - triggers))
        )
    reserved = {REVIEW_TRIGGER, EVENT_TRIGGER} & triggers
    if reserved:
        raise RuntimeError(
            "Upgrade bloqueado: triggers v2 ya existen fuera de Alembic: "
            + ", ".join(sorted(reserved))
        )
    if REVIEW_REQUIRED_CHECK in _check_names(bind, "reviews"):
        raise RuntimeError("Upgrade bloqueado: check v2 de reviews ya existe.")
    if EVENT_REQUIRED_CHECK in _check_names(bind, "reputation_events"):
        raise RuntimeError(
            "Upgrade bloqueado: check v2 de reputation_events ya existe."
        )

    invalid_review = bind.execute(
        sa.text(
            "SELECT id FROM reviews "
            "WHERE origin IS NULL OR origin NOT IN ('CONTRACTUAL', 'LEGACY') "
            "ORDER BY id LIMIT 1"
        )
    ).scalar()
    if invalid_review is not None:
        raise RuntimeError(
            "Upgrade bloqueado: review con origin nulo o desconocido "
            f"(id={invalid_review})."
        )
    invalid_event = bind.execute(
        sa.text(
            "SELECT id FROM reputation_events WHERE source_type IS NULL "
            "OR source_type NOT IN ('CONTRACT_REVIEW', 'LEGACY_EVENT') "
            "OR origin IS NULL OR origin NOT IN ('CONTRACTUAL', 'LEGACY') "
            "ORDER BY id LIMIT 1"
        )
    ).scalar()
    if invalid_event is not None:
        raise RuntimeError(
            "Upgrade bloqueado: evento con discriminador nulo o desconocido "
            f"(id={invalid_event})."
        )
    return _legacy_reclassification_plan(bind)


def _apply_legacy_reclassification(plan):
    statement = sa.text(
        "UPDATE reviews SET contract_id=:contract_id, rating=:rating, "
        "verification_status=:verification_status, "
        "rating_eligibility_status=:rating_eligibility_status, "
        "legacy_metadata_json=:metadata WHERE id=:id AND origin='LEGACY'"
    ).bindparams(sa.bindparam("metadata", type_=sa.JSON()))
    bind = op.get_bind()
    for item in plan:
        result = bind.execute(statement, item)
        if result.rowcount != 1:
            raise RuntimeError(
                "Upgrade abortado: review legacy cambio durante la reparacion "
                f"(id={item['id']})."
            )


def _drop_v1_guards():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text(f"DROP TRIGGER {V1_EVENT_TRIGGER} ON reputation_events"))
        op.execute(sa.text(f"DROP FUNCTION {V1_EVENT_FUNCTION}()"))
        op.execute(sa.text(f"DROP TRIGGER {V1_REVIEW_TRIGGER} ON reviews"))
        op.execute(sa.text(f"DROP FUNCTION {V1_REVIEW_FUNCTION}()"))
    else:
        for name in (
            V1_EVENT_UPDATE_TRIGGER,
            V1_EVENT_INSERT_TRIGGER,
            V1_REVIEW_UPDATE_TRIGGER,
            V1_REVIEW_INSERT_TRIGGER,
        ):
            op.execute(sa.text(f"DROP TRIGGER {name}"))


def _create_checks():
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.create_check_constraint(
            REVIEW_REQUIRED_CHECK,
            "origin IS NOT NULL",
        )
    with op.batch_alter_table("reputation_events") as batch_op:
        batch_op.create_check_constraint(
            EVENT_REQUIRED_CHECK,
            "source_type IS NOT NULL AND origin IS NOT NULL",
        )


def _create_postgresql_guards():
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {REVIEW_FUNCTION}()
            RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE
                contract_row contract_requests%ROWTYPE;
                professional_user INTEGER;
            BEGIN
                IF TG_OP = 'INSERT' AND NEW.origin IS DISTINCT FROM 'CONTRACTUAL' THEN
                    RAISE EXCEPTION 'new reviews must be CONTRACTUAL'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.origin IS NULL
                   OR NEW.origin NOT IN ('CONTRACTUAL', 'LEGACY') THEN
                    RAISE EXCEPTION 'review origin is invalid'
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
                       OR contract_row.professional_user_id IS NULL
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
            f"CREATE TRIGGER {REVIEW_TRIGGER} BEFORE INSERT OR UPDATE ON reviews "
            f"FOR EACH ROW EXECUTE FUNCTION {REVIEW_FUNCTION}()"
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {EVENT_FUNCTION}()
            RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE
                review_row reviews%ROWTYPE;
                professional_user INTEGER;
            BEGIN
                IF TG_OP = 'INSERT' AND (
                    NEW.source_type IS DISTINCT FROM 'CONTRACT_REVIEW' OR
                    NEW.origin IS DISTINCT FROM 'CONTRACTUAL' OR
                    NEW.event_type IS DISTINCT FROM 'REVIEW_RECORDED' OR
                    NEW.event_value IS NULL OR NEW.event_value NOT BETWEEN 1 AND 5 OR
                    NEW.puntos IS NOT NULL
                ) THEN
                    RAISE EXCEPTION 'new reputation event discriminators are invalid'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.source_type IS NULL
                   OR NEW.source_type NOT IN ('CONTRACT_REVIEW', 'LEGACY_EVENT')
                   OR NEW.origin IS NULL
                   OR NEW.origin NOT IN ('CONTRACTUAL', 'LEGACY') THEN
                    RAISE EXCEPTION 'reputation event discriminator is invalid'
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
                    IF NEW.origin IS DISTINCT FROM 'CONTRACTUAL'
                       OR NEW.event_type IS DISTINCT FROM 'REVIEW_RECORDED'
                       OR NEW.event_value IS NULL
                       OR NEW.event_value NOT BETWEEN 1 AND 5
                       OR NEW.puntos IS NOT NULL THEN
                        RAISE EXCEPTION 'contract review event facts are invalid'
                            USING ERRCODE = '23514';
                    END IF;
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
                END IF;
                RETURN NEW;
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            f"CREATE TRIGGER {EVENT_TRIGGER} BEFORE INSERT OR UPDATE "
            "ON reputation_events FOR EACH ROW EXECUTE FUNCTION "
            f"{EVENT_FUNCTION}()"
        )
    )


def _create_sqlite_guards():
    review_invalid = """
        NEW.origin <> 'CONTRACTUAL' OR NEW.origin IS NULL OR NOT EXISTS (
            SELECT 1 FROM contract_requests AS contract_row
            JOIN professionals AS professional_row
              ON professional_row.id = contract_row.professional_id
            WHERE contract_row.id = NEW.contract_id
              AND contract_row.estado = 'CONFIRMADA'
              AND contract_row.cliente_id = NEW.cliente_id
              AND contract_row.professional_id = NEW.professional_id
              AND professional_row.user_id IS NOT NULL
              AND contract_row.professional_user_id IS NOT NULL
              AND professional_row.user_id = contract_row.professional_user_id
        )
    """
    op.execute(sa.text(f"""
        CREATE TRIGGER {REVIEW_TRIGGER}
        BEFORE INSERT ON reviews FOR EACH ROW
        WHEN {review_invalid}
        BEGIN
            SELECT RAISE(ABORT, 'contract review insert is invalid');
        END
    """))
    op.execute(sa.text(f"""
        CREATE TRIGGER {REVIEW_TRIGGER}_update
        BEFORE UPDATE ON reviews FOR EACH ROW
        WHEN NOT (NEW.contract_id IS OLD.contract_id)
          OR NOT (NEW.cliente_id IS OLD.cliente_id)
          OR NOT (NEW.professional_id IS OLD.professional_id)
          OR NOT (NEW.rating IS OLD.rating)
          OR NOT (NEW.comentario IS OLD.comentario)
          OR NOT (NEW.origin IS OLD.origin)
          OR NOT (NEW.payload_hash IS OLD.payload_hash)
          OR NOT (NEW.created_at IS OLD.created_at)
          OR NEW.origin IS NULL
          OR NEW.origin NOT IN ('CONTRACTUAL', 'LEGACY')
          OR (NEW.origin = 'CONTRACTUAL' AND NOT EXISTS (
              SELECT 1 FROM contract_requests AS contract_row
              JOIN professionals AS professional_row
                ON professional_row.id = contract_row.professional_id
              WHERE contract_row.id = NEW.contract_id
                AND contract_row.estado = 'CONFIRMADA'
                AND contract_row.cliente_id = NEW.cliente_id
                AND contract_row.professional_id = NEW.professional_id
                AND professional_row.user_id IS NOT NULL
                AND contract_row.professional_user_id IS NOT NULL
                AND professional_row.user_id = contract_row.professional_user_id
          ))
        BEGIN
            SELECT RAISE(ABORT, 'review causal fields are immutable or invalid');
        END
    """))

    event_invalid = """
        NEW.source_type <> 'CONTRACT_REVIEW'
        OR NEW.source_type IS NULL
        OR NEW.origin <> 'CONTRACTUAL'
        OR NEW.origin IS NULL
        OR NEW.event_type <> 'REVIEW_RECORDED'
        OR NEW.event_type IS NULL
        OR NEW.event_value IS NULL
        OR NEW.event_value NOT BETWEEN 1 AND 5
        OR NEW.puntos IS NOT NULL
        OR NOT EXISTS (
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
        )
    """
    op.execute(sa.text(f"""
        CREATE TRIGGER {EVENT_TRIGGER}
        BEFORE INSERT ON reputation_events FOR EACH ROW
        WHEN {event_invalid}
        BEGIN
            SELECT RAISE(ABORT, 'reputation event insert is invalid');
        END
    """))
    op.execute(sa.text(f"""
        CREATE TRIGGER {EVENT_TRIGGER}_update
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
          OR NEW.source_type IS NULL
          OR NEW.source_type NOT IN ('CONTRACT_REVIEW', 'LEGACY_EVENT')
          OR NEW.origin IS NULL
          OR NEW.origin NOT IN ('CONTRACTUAL', 'LEGACY')
          OR (NEW.source_type = 'CONTRACT_REVIEW' AND ({event_invalid}))
        BEGIN
            SELECT RAISE(ABORT, 'reputation event causal fields are immutable or invalid');
        END
    """))


def _create_v2_guards():
    if op.get_bind().dialect.name == "postgresql":
        _create_postgresql_guards()
    else:
        _create_sqlite_guards()


def _drop_v2_guards():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text(f"DROP TRIGGER {EVENT_TRIGGER} ON reputation_events"))
        op.execute(sa.text(f"DROP FUNCTION {EVENT_FUNCTION}()"))
        op.execute(sa.text(f"DROP TRIGGER {REVIEW_TRIGGER} ON reviews"))
        op.execute(sa.text(f"DROP FUNCTION {REVIEW_FUNCTION}()"))
    else:
        for name in (
            f"{EVENT_TRIGGER}_update",
            EVENT_TRIGGER,
            f"{REVIEW_TRIGGER}_update",
            REVIEW_TRIGGER,
        ):
            op.execute(sa.text(f"DROP TRIGGER {name}"))


def _drop_checks():
    with op.batch_alter_table("reputation_events") as batch_op:
        batch_op.drop_constraint(EVENT_REQUIRED_CHECK, type_="check")
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_constraint(REVIEW_REQUIRED_CHECK, type_="check")


def _preflight_downgrade():
    bind = op.get_bind()
    expected = (
        {REVIEW_TRIGGER, EVENT_TRIGGER}
        if bind.dialect.name == "postgresql"
        else {
            REVIEW_TRIGGER,
            f"{REVIEW_TRIGGER}_update",
            EVENT_TRIGGER,
            f"{EVENT_TRIGGER}_update",
        }
    )
    triggers = _trigger_names(bind)
    missing = expected - triggers
    if missing:
        raise RuntimeError(
            "Downgrade bloqueado antes de mutar: defensas v2 incompletas: "
            + ", ".join(sorted(missing))
        )
    if REVIEW_REQUIRED_CHECK not in _check_names(bind, "reviews"):
        raise RuntimeError(
            "Downgrade bloqueado antes de mutar: falta check v2 de reviews."
        )
    if EVENT_REQUIRED_CHECK not in _check_names(bind, "reputation_events"):
        raise RuntimeError(
            "Downgrade bloqueado antes de mutar: falta check v2 de eventos."
        )


def upgrade():
    legacy_plan = _preflight_upgrade()
    _drop_v1_guards()
    _apply_legacy_reclassification(legacy_plan)
    _create_checks()
    _create_v2_guards()


def downgrade():
    _preflight_downgrade()
    _drop_v2_guards()
    _drop_checks()
    previous = importlib.import_module(
        "migrations.versions.20260726_06_contract_reviews_reputation_integrity"
    )
    previous._create_triggers()

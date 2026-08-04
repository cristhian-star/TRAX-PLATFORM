"""protect negotiation snapshots and acceptance identities

Revision ID: 20260726_05
Revises: 20260726_04
Create Date: 2026-07-26
"""

import hashlib
import json
from datetime import timezone
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "20260726_05"
down_revision = "20260726_04"
branch_labels = None
depends_on = None


SNAPSHOT_TRIGGER = "trg_contract_negotiation_versions_immutable"
SNAPSHOT_FUNCTION = "trax_guard_contract_negotiation_version_update"
ACCEPTANCE_TRIGGER = "trg_negotiation_acceptances_coherent"
ACCEPTANCE_FUNCTION = "trax_guard_negotiation_acceptance"
SQLITE_ACCEPTANCE_INSERT_TRIGGER = (
    "trg_negotiation_acceptances_coherent_insert"
)
SQLITE_ACCEPTANCE_UPDATE_TRIGGER = (
    "trg_negotiation_acceptances_coherent_update"
)


def _hash_payload(payload):
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _canonical_datetime(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat(timespec="microseconds")


def _snapshot_hashes(row):
    legacy_payload = {
        "description": row.description,
        "scope": row.scope,
        "external_price": row.external_price,
        "estimated_start_at": row.estimated_start_at,
        "estimated_end_at": row.estimated_end_at,
        "observations": row.observations,
    }
    canonical_payload = {
        **legacy_payload,
        "external_price": format(
            Decimal(str(row.external_price)).quantize(Decimal("0.01")),
            "f",
        ),
        "estimated_start_at": _canonical_datetime(row.estimated_start_at),
        "estimated_end_at": _canonical_datetime(row.estimated_end_at),
    }
    return _hash_payload(legacy_payload), _hash_payload(canonical_payload)


def _preflight_and_normalize_existing_rows():
    bind = op.get_bind()
    snapshots = bind.execute(
        sa.text(
            "SELECT id, description, scope, external_price, "
            "estimated_start_at, estimated_end_at, observations, payload_hash "
            "FROM contract_negotiation_versions ORDER BY id"
        ).columns(
            id=sa.Integer(),
            description=sa.Text(),
            scope=sa.Text(),
            external_price=sa.Numeric(10, 2),
            estimated_start_at=sa.DateTime(),
            estimated_end_at=sa.DateTime(),
            observations=sa.Text(),
            payload_hash=sa.String(64),
        )
    ).all()
    normalizations = []
    for row in snapshots:
        legacy_hash, canonical_hash = _snapshot_hashes(row)
        if row.payload_hash == canonical_hash:
            continue
        if row.payload_hash == legacy_hash:
            normalizations.append(
                {"snapshot_id": row.id, "payload_hash": canonical_hash}
            )
            continue
        raise RuntimeError(
            "Upgrade bloqueado: snapshot de negociacion con hash incoherente "
            f"(id={row.id})."
        )

    incoherent_acceptance = bind.execute(
        sa.text(
            """
            SELECT acceptance.id
            FROM negotiation_acceptances AS acceptance
            LEFT JOIN contract_negotiations AS negotiation
              ON negotiation.id = acceptance.negotiation_id
            LEFT JOIN contract_negotiation_versions AS version
              ON version.id = acceptance.negotiation_version_id
            LEFT JOIN users AS actor
              ON actor.id = acceptance.actor_user_id
            WHERE negotiation.id IS NULL
               OR version.id IS NULL
               OR version.negotiation_id <> acceptance.negotiation_id
               OR actor.id IS NULL
               OR (
                    acceptance.party = 'CLIENT'
                    AND (
                        acceptance.actor_user_id <> negotiation.cliente_id
                        OR actor.rol <> 'CLIENTE'
                    )
               )
               OR (
                    acceptance.party = 'PROFESSIONAL'
                    AND (
                        acceptance.actor_user_id
                            <> negotiation.professional_user_id
                        OR actor.rol <> 'PROFESIONAL'
                    )
               )
               OR acceptance.party NOT IN ('CLIENT', 'PROFESSIONAL')
            LIMIT 1
            """
        )
    ).scalar()
    if incoherent_acceptance is not None:
        raise RuntimeError(
            "Upgrade bloqueado: aceptacion de negociacion incoherente "
            f"(id={incoherent_acceptance})."
        )

    for normalization in normalizations:
        bind.execute(
            sa.text(
                "UPDATE contract_negotiation_versions "
                "SET payload_hash = :payload_hash WHERE id = :snapshot_id"
            ),
            normalization,
        )


def _create_postgresql_guards():
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {SNAPSHOT_FUNCTION}()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION
                    'contract_negotiation_versions snapshots are immutable'
                    USING ERRCODE = '23514';
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE TRIGGER {SNAPSHOT_TRIGGER}
            BEFORE UPDATE ON contract_negotiation_versions
            FOR EACH ROW EXECUTE FUNCTION {SNAPSHOT_FUNCTION}()
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {ACCEPTANCE_FUNCTION}()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            DECLARE
                negotiation_row contract_negotiations%ROWTYPE;
                version_row contract_negotiation_versions%ROWTYPE;
                actor_role VARCHAR(20);
                actor_state VARCHAR(20);
            BEGIN
                SELECT * INTO version_row
                FROM contract_negotiation_versions
                WHERE id = NEW.negotiation_version_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'acceptance version does not exist'
                        USING ERRCODE = '23503';
                END IF;

                SELECT * INTO negotiation_row
                FROM contract_negotiations
                WHERE id = NEW.negotiation_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'acceptance negotiation does not exist'
                        USING ERRCODE = '23503';
                END IF;

                IF version_row.negotiation_id <> NEW.negotiation_id
                   OR version_row.version_no
                        <> negotiation_row.current_terms_version THEN
                    RAISE EXCEPTION
                        'acceptance must reference the current negotiation version'
                        USING ERRCODE = '23514';
                END IF;

                SELECT rol, estado INTO actor_role, actor_state
                FROM users
                WHERE id = NEW.actor_user_id;
                IF NOT FOUND OR actor_state <> 'ACTIVO' THEN
                    RAISE EXCEPTION 'acceptance actor must be active'
                        USING ERRCODE = '23514';
                END IF;

                IF NEW.party = 'CLIENT' THEN
                    IF NEW.actor_user_id <> negotiation_row.cliente_id
                       OR actor_role <> 'CLIENTE' THEN
                        RAISE EXCEPTION
                            'CLIENT acceptance actor identity is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                ELSIF NEW.party = 'PROFESSIONAL' THEN
                    IF NEW.actor_user_id
                            <> negotiation_row.professional_user_id
                       OR actor_role <> 'PROFESIONAL' THEN
                        RAISE EXCEPTION
                            'PROFESSIONAL acceptance actor identity is invalid'
                            USING ERRCODE = '23514';
                    END IF;
                ELSE
                    RAISE EXCEPTION 'acceptance party is invalid'
                        USING ERRCODE = '23514';
                END IF;
                RETURN NEW;
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE TRIGGER {ACCEPTANCE_TRIGGER}
            BEFORE INSERT OR UPDATE ON negotiation_acceptances
            FOR EACH ROW EXECUTE FUNCTION {ACCEPTANCE_FUNCTION}()
            """
        )
    )


def _create_sqlite_guards():
    op.execute(
        sa.text(
            f"""
            CREATE TRIGGER {SNAPSHOT_TRIGGER}
            BEFORE UPDATE ON contract_negotiation_versions
            FOR EACH ROW
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'contract_negotiation_versions snapshots are immutable'
                );
            END
            """
        )
    )
    condition = """
        NOT EXISTS (
            SELECT 1
            FROM contract_negotiation_versions AS version_row
            JOIN contract_negotiations AS negotiation_row
              ON negotiation_row.id = NEW.negotiation_id
            JOIN users AS actor_row
              ON actor_row.id = NEW.actor_user_id
            WHERE version_row.id = NEW.negotiation_version_id
              AND version_row.negotiation_id = NEW.negotiation_id
              AND version_row.version_no
                    = negotiation_row.current_terms_version
              AND actor_row.estado = 'ACTIVO'
              AND (
                    (
                        NEW.party = 'CLIENT'
                        AND NEW.actor_user_id = negotiation_row.cliente_id
                        AND actor_row.rol = 'CLIENTE'
                    )
                    OR
                    (
                        NEW.party = 'PROFESSIONAL'
                        AND NEW.actor_user_id
                            = negotiation_row.professional_user_id
                        AND actor_row.rol = 'PROFESIONAL'
                    )
              )
        )
    """
    for trigger_name, operation in (
        (SQLITE_ACCEPTANCE_INSERT_TRIGGER, "INSERT"),
        (SQLITE_ACCEPTANCE_UPDATE_TRIGGER, "UPDATE"),
    ):
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER {trigger_name}
                BEFORE {operation} ON negotiation_acceptances
                FOR EACH ROW
                WHEN {condition}
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'negotiation acceptance identity is incoherent'
                    );
                END
                """
            )
        )


def upgrade():
    _preflight_and_normalize_existing_rows()
    with op.batch_alter_table("contract_negotiation_versions") as batch_op:
        batch_op.create_unique_constraint(
            "uq_contract_negotiation_versions_id_negotiation",
            ["id", "negotiation_id"],
        )
    with op.batch_alter_table("negotiation_acceptances") as batch_op:
        batch_op.create_foreign_key(
            "fk_negotiation_acceptances_version_negotiation",
            "contract_negotiation_versions",
            ["negotiation_version_id", "negotiation_id"],
            ["id", "negotiation_id"],
            ondelete="RESTRICT",
        )

    if op.get_bind().dialect.name == "postgresql":
        _create_postgresql_guards()
    elif op.get_bind().dialect.name == "sqlite":
        _create_sqlite_guards()


def downgrade():
    bind = op.get_bind()
    version_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM contract_negotiation_versions")
    ).scalar()
    acceptance_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM negotiation_acceptances")
    ).scalar()
    if version_count or acceptance_count:
        raise RuntimeError(
            "Downgrade bloqueado: existen snapshots o aceptaciones protegidos."
        )

    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                f"DROP TRIGGER IF EXISTS {ACCEPTANCE_TRIGGER} "
                "ON negotiation_acceptances"
            )
        )
        op.execute(
            sa.text(
                f"DROP FUNCTION IF EXISTS {ACCEPTANCE_FUNCTION}()"
            )
        )
        op.execute(
            sa.text(
                f"DROP TRIGGER IF EXISTS {SNAPSHOT_TRIGGER} "
                "ON contract_negotiation_versions"
            )
        )
        op.execute(
            sa.text(f"DROP FUNCTION IF EXISTS {SNAPSHOT_FUNCTION}()")
        )
    elif bind.dialect.name == "sqlite":
        for trigger_name in (
            SQLITE_ACCEPTANCE_INSERT_TRIGGER,
            SQLITE_ACCEPTANCE_UPDATE_TRIGGER,
            SNAPSHOT_TRIGGER,
        ):
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS {trigger_name}"))

    with op.batch_alter_table("negotiation_acceptances") as batch_op:
        batch_op.drop_constraint(
            "fk_negotiation_acceptances_version_negotiation",
            type_="foreignkey",
        )
    with op.batch_alter_table("contract_negotiation_versions") as batch_op:
        batch_op.drop_constraint(
            "uq_contract_negotiation_versions_id_negotiation",
            type_="unique",
        )

"""sprint 7 contracting core phase 1

Revision ID: 20260726_01
Revises: 20260723_01
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_01"
down_revision = "20260723_01"
branch_labels = None
depends_on = None


def _column_names(inspector, table_name):
    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _index_names(inspector, table_name):
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _constraint_names(inspector, table_name, kind):
    if kind == "unique":
        return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}
    if kind == "check":
        return {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}
    if kind == "foreignkey":
        return {constraint["name"] for constraint in inspector.get_foreign_keys(table_name)}
    return set()


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("budget_requests"):
        op.execute("UPDATE budget_requests SET estado = 'CERRADA' WHERE estado = 'CERRADO'")

    proposal_columns = _column_names(inspector, "proposal_requests")
    if "hiring_mode" not in proposal_columns:
        with op.batch_alter_table("proposal_requests") as batch_op:
            batch_op.add_column(
                sa.Column("hiring_mode", sa.String(length=20), nullable=False, server_default="SINGLE")
            )
    op.execute("UPDATE proposal_requests SET hiring_mode = 'SINGLE' WHERE hiring_mode IS NULL")

    audit_columns = _column_names(inspector, "audit_logs")
    with op.batch_alter_table("audit_logs") as batch_op:
        if "entity_type" not in audit_columns:
            batch_op.add_column(sa.Column("entity_type", sa.String(length=80), nullable=True))
        if "entity_id" not in audit_columns:
            batch_op.add_column(sa.Column("entity_id", sa.Integer(), nullable=True))
        if "contract_id" not in audit_columns:
            batch_op.add_column(sa.Column("contract_id", sa.Integer(), nullable=True))
        if "event_id" not in audit_columns:
            batch_op.add_column(sa.Column("event_id", sa.Integer(), nullable=True))
        if "idempotency_key" not in audit_columns:
            batch_op.add_column(sa.Column("idempotency_key", sa.String(length=160), nullable=True))

    contract_columns = _column_names(inspector, "contract_requests")
    with op.batch_alter_table("contract_requests") as batch_op:
        if "source_type" not in contract_columns:
            batch_op.add_column(sa.Column("source_type", sa.String(length=50), nullable=True))
        if "source_id" not in contract_columns:
            batch_op.add_column(sa.Column("source_id", sa.Integer(), nullable=True))
        if "budget_offer_id" not in contract_columns:
            batch_op.add_column(sa.Column("budget_offer_id", sa.Integer(), nullable=True))
        if "proposal_application_id" not in contract_columns:
            batch_op.add_column(sa.Column("proposal_application_id", sa.Integer(), nullable=True))
        if "created_from_event" not in contract_columns:
            batch_op.add_column(sa.Column("created_from_event", sa.String(length=80), nullable=True))

    op.execute("UPDATE contract_requests SET source_type = 'DIRECT' WHERE source_type IS NULL")

    with op.batch_alter_table("contract_requests") as batch_op:
        batch_op.alter_column("source_type", existing_type=sa.String(length=50), nullable=False)
        existing_checks = _constraint_names(inspector, "contract_requests", "check")
        if "ck_contract_requests_source_type" not in existing_checks:
            batch_op.create_check_constraint(
                "ck_contract_requests_source_type",
                "source_type in ('DIRECT', 'BUDGET', 'PROPOSAL', 'EMERGENCY')",
            )
        if "ck_contract_requests_source_consistency" not in existing_checks:
            batch_op.create_check_constraint(
                "ck_contract_requests_source_consistency",
                "("
                "source_type = 'DIRECT' AND budget_offer_id IS NULL AND proposal_application_id IS NULL"
                ") OR ("
                "source_type = 'BUDGET' AND budget_offer_id IS NOT NULL AND proposal_application_id IS NULL AND source_id = budget_offer_id"
                ") OR ("
                "source_type = 'PROPOSAL' AND proposal_application_id IS NOT NULL AND budget_offer_id IS NULL AND source_id = proposal_application_id"
                ") OR ("
                "source_type = 'EMERGENCY' AND budget_offer_id IS NULL AND proposal_application_id IS NULL"
                ")",
            )
        if "budget_offer_id" not in contract_columns:
            batch_op.create_foreign_key(
                "fk_contract_requests_budget_offer_id_budget_offers",
                "budget_offers",
                ["budget_offer_id"],
                ["id"],
            )
            batch_op.create_unique_constraint(
                "uq_contract_requests_budget_offer_id",
                ["budget_offer_id"],
            )
        if "proposal_application_id" not in contract_columns:
            batch_op.create_foreign_key(
                "fk_contract_requests_proposal_app_id",
                "proposal_applications",
                ["proposal_application_id"],
                ["id"],
            )
            batch_op.create_unique_constraint(
                "uq_contract_requests_proposal_application_id",
                ["proposal_application_id"],
            )

    contract_indexes = _index_names(inspector, "contract_requests")
    if "ix_contract_requests_source_type" not in contract_indexes:
        op.create_index("ix_contract_requests_source_type", "contract_requests", ["source_type"])
    if "ix_contract_requests_source_id" not in contract_indexes:
        op.create_index("ix_contract_requests_source_id", "contract_requests", ["source_id"])

    audit_indexes = _index_names(inspector, "audit_logs")
    if "ix_audit_logs_entity_type" not in audit_indexes:
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    if "ix_audit_logs_entity_id" not in audit_indexes:
        op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    if "ix_audit_logs_contract_id" not in audit_indexes:
        op.create_index("ix_audit_logs_contract_id", "audit_logs", ["contract_id"])
    if "ix_audit_logs_event_id" not in audit_indexes:
        op.create_index("ix_audit_logs_event_id", "audit_logs", ["event_id"])
    if "ix_audit_logs_idempotency_key" not in audit_indexes:
        op.create_index("ix_audit_logs_idempotency_key", "audit_logs", ["idempotency_key"])

    if not inspector.has_table("contract_events"):
        op.create_table(
            "contract_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("contract_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("previous_status", sa.String(length=50), nullable=True),
            sa.Column("new_status", sa.String(length=50), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["contract_id"], ["contract_requests.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_contract_events_actor_user_id", "contract_events", ["actor_user_id"])
        op.create_index("ix_contract_events_contract_id", "contract_events", ["contract_id"])
        op.create_index("ix_contract_events_created_at", "contract_events", ["created_at"])
        op.create_index("ix_contract_events_event_type", "contract_events", ["event_type"])

    inspector = sa.inspect(bind)
    audit_columns = _column_names(inspector, "audit_logs")
    audit_fks = _constraint_names(inspector, "audit_logs", "foreignkey")
    with op.batch_alter_table("audit_logs") as batch_op:
        if "contract_id" in audit_columns and "fk_audit_logs_contract_id_contract_requests" not in audit_fks:
            batch_op.create_foreign_key(
                "fk_audit_logs_contract_id_contract_requests",
                "contract_requests",
                ["contract_id"],
                ["id"],
            )
        if "event_id" in audit_columns and "fk_audit_logs_event_id_contract_events" not in audit_fks:
            batch_op.create_foreign_key(
                "fk_audit_logs_event_id_contract_events",
                "contract_events",
                ["event_id"],
                ["id"],
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("audit_logs"):
        audit_fks = _constraint_names(inspector, "audit_logs", "foreignkey")
        with op.batch_alter_table("audit_logs") as batch_op:
            if "fk_audit_logs_event_id_contract_events" in audit_fks:
                batch_op.drop_constraint("fk_audit_logs_event_id_contract_events", type_="foreignkey")
            if "fk_audit_logs_contract_id_contract_requests" in audit_fks:
                batch_op.drop_constraint("fk_audit_logs_contract_id_contract_requests", type_="foreignkey")
        inspector = sa.inspect(bind)

    if inspector.has_table("contract_events"):
        event_count = bind.execute(sa.text("SELECT COUNT(*) FROM contract_events")).scalar()
        derived_count = bind.execute(sa.text("SELECT COUNT(*) FROM contract_requests WHERE source_type IN ('BUDGET', 'PROPOSAL')")).scalar()
        if event_count or derived_count:
            raise RuntimeError(
                "Downgrade bloqueado: existen contract_events o contratos derivados. "
                "Preservar trazabilidad antes de revertir esta migracion."
            )
        op.drop_index("ix_contract_events_event_type", table_name="contract_events")
        op.drop_index("ix_contract_events_created_at", table_name="contract_events")
        op.drop_index("ix_contract_events_contract_id", table_name="contract_events")
        op.drop_index("ix_contract_events_actor_user_id", table_name="contract_events")
        op.drop_table("contract_events")

    existing_indexes = _index_names(inspector, "contract_requests")
    if "ix_contract_requests_source_id" in existing_indexes:
        op.drop_index("ix_contract_requests_source_id", table_name="contract_requests")
    if "ix_contract_requests_source_type" in existing_indexes:
        op.drop_index("ix_contract_requests_source_type", table_name="contract_requests")

    contract_columns = _column_names(inspector, "contract_requests")
    contract_checks = _constraint_names(inspector, "contract_requests", "check")
    contract_fks = _constraint_names(inspector, "contract_requests", "foreignkey")
    with op.batch_alter_table("contract_requests") as batch_op:
        if "ck_contract_requests_source_consistency" in contract_checks:
            batch_op.drop_constraint("ck_contract_requests_source_consistency", type_="check")
        if "ck_contract_requests_source_type" in contract_checks:
            batch_op.drop_constraint("ck_contract_requests_source_type", type_="check")
        if "proposal_application_id" in contract_columns:
            batch_op.drop_constraint("uq_contract_requests_proposal_application_id", type_="unique")
            for constraint_name in (
                "fk_contract_requests_proposal_app_id",
                "fk_contract_requests_proposal_application_id_proposal_applications",
            ):
                if constraint_name in contract_fks:
                    batch_op.drop_constraint(constraint_name, type_="foreignkey")
            batch_op.drop_column("proposal_application_id")
        if "budget_offer_id" in contract_columns:
            batch_op.drop_constraint("uq_contract_requests_budget_offer_id", type_="unique")
            batch_op.drop_constraint(
                "fk_contract_requests_budget_offer_id_budget_offers",
                type_="foreignkey",
            )
            batch_op.drop_column("budget_offer_id")
        if "created_from_event" in contract_columns:
            batch_op.drop_column("created_from_event")
        if "source_id" in contract_columns:
            batch_op.drop_column("source_id")
        if "source_type" in contract_columns:
            batch_op.drop_column("source_type")

    audit_indexes = _index_names(inspector, "audit_logs")
    for index_name in (
        "ix_audit_logs_idempotency_key",
        "ix_audit_logs_event_id",
        "ix_audit_logs_contract_id",
        "ix_audit_logs_entity_id",
        "ix_audit_logs_entity_type",
    ):
        if index_name in audit_indexes:
            op.drop_index(index_name, table_name="audit_logs")

    audit_columns = _column_names(inspector, "audit_logs")
    audit_fks = _constraint_names(inspector, "audit_logs", "foreignkey")
    with op.batch_alter_table("audit_logs") as batch_op:
        for column_name in ("idempotency_key", "event_id", "contract_id", "entity_id", "entity_type"):
            if column_name in audit_columns:
                batch_op.drop_column(column_name)

    proposal_columns = _column_names(inspector, "proposal_requests")
    if "hiring_mode" in proposal_columns:
        with op.batch_alter_table("proposal_requests") as batch_op:
            batch_op.drop_column("hiring_mode")

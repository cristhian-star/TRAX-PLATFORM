"""add Sprint 7 direct negotiation MVP

Revision ID: 20260726_04
Revises: 20260726_03
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_04"
down_revision = "20260726_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contract_negotiations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("professional_user_id", sa.Integer(), nullable=False),
        sa.Column("servicio", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column(
            "contracting_mode",
            sa.String(length=20),
            nullable=False,
            server_default="EXTERNAL",
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "current_terms_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column("agreed_terms_version", sa.Integer(), nullable=True),
        sa.Column("contract_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "state in ('OPEN', 'AGREED', 'CANCELLED', 'REJECTED', 'CONTRACTED')",
            name="ck_contract_negotiations_state",
        ),
        sa.CheckConstraint(
            "contracting_mode = 'EXTERNAL'",
            name="ck_contract_negotiations_contracting_mode",
        ),
        sa.CheckConstraint(
            "version >= 1 AND current_terms_version >= 1",
            name="ck_contract_negotiations_versions",
        ),
        sa.CheckConstraint(
            "agreed_terms_version IS NULL OR agreed_terms_version >= 1",
            name="ck_contract_negotiations_agreed_version",
        ),
        sa.CheckConstraint(
            "agreed_terms_version IS NULL "
            "OR agreed_terms_version = current_terms_version",
            name="ck_contract_negotiations_agreed_is_current",
        ),
        sa.CheckConstraint(
            "state NOT IN ('AGREED', 'CONTRACTED') "
            "OR agreed_terms_version IS NOT NULL",
            name="ck_contract_negotiations_agreed_state",
        ),
        sa.CheckConstraint(
            "(state = 'CONTRACTED' AND contract_id IS NOT NULL) "
            "OR (state <> 'CONTRACTED' AND contract_id IS NULL)",
            name="ck_contract_negotiations_contract_state",
        ),
        sa.CheckConstraint(
            "cliente_id <> professional_user_id",
            name="ck_contract_negotiations_distinct_parties",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["users.id"],
            name="fk_contract_negotiations_cliente_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professionals.id"],
            name="fk_contract_negotiations_professional_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["professional_user_id"],
            ["users.id"],
            name="fk_contract_negotiations_professional_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contract_requests.id"],
            name="fk_contract_negotiations_contract_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contract_id",
            name="uq_contract_negotiations_contract_id",
        ),
    )
    for name, columns in (
        ("ix_contract_negotiations_cliente_id", ["cliente_id"]),
        ("ix_contract_negotiations_professional_id", ["professional_id"]),
        (
            "ix_contract_negotiations_professional_user_id",
            ["professional_user_id"],
        ),
        ("ix_contract_negotiations_contract_id", ["contract_id"]),
    ):
        op.create_index(name, "contract_negotiations", columns)

    op.create_table(
        "contract_negotiation_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("negotiation_id", sa.Integer(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("external_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("estimated_start_at", sa.DateTime(), nullable=True),
        sa.Column("estimated_end_at", sa.DateTime(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "version_no >= 1",
            name="ck_contract_negotiation_versions_number",
        ),
        sa.CheckConstraint(
            "external_price >= 0",
            name="ck_contract_negotiation_versions_price",
        ),
        sa.CheckConstraint(
            "estimated_start_at IS NULL OR estimated_end_at IS NULL "
            "OR estimated_start_at <= estimated_end_at",
            name="ck_contract_negotiation_versions_dates",
        ),
        sa.ForeignKeyConstraint(
            ["negotiation_id"],
            ["contract_negotiations.id"],
            name="fk_contract_negotiation_versions_negotiation_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_contract_negotiation_versions_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "negotiation_id",
            "version_no",
            name="uq_contract_negotiation_versions_number",
        ),
    )
    op.create_index(
        "ix_contract_negotiation_versions_negotiation_id",
        "contract_negotiation_versions",
        ["negotiation_id"],
    )
    op.create_index(
        "ix_contract_negotiation_versions_actor_user_id",
        "contract_negotiation_versions",
        ["actor_user_id"],
    )

    op.create_table(
        "negotiation_acceptances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("negotiation_id", sa.Integer(), nullable=False),
        sa.Column("negotiation_version_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("party", sa.String(length=20), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "party in ('CLIENT', 'PROFESSIONAL')",
            name="ck_negotiation_acceptances_party",
        ),
        sa.ForeignKeyConstraint(
            ["negotiation_id"],
            ["contract_negotiations.id"],
            name="fk_negotiation_acceptances_negotiation_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["negotiation_version_id"],
            ["contract_negotiation_versions.id"],
            name="fk_negotiation_acceptances_version_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_negotiation_acceptances_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "negotiation_version_id",
            "party",
            name="uq_negotiation_acceptances_version_party",
        ),
    )
    for name, columns in (
        ("ix_negotiation_acceptances_negotiation_id", ["negotiation_id"]),
        (
            "ix_negotiation_acceptances_negotiation_version_id",
            ["negotiation_version_id"],
        ),
        ("ix_negotiation_acceptances_actor_user_id", ["actor_user_id"]),
    ):
        op.create_index(name, "negotiation_acceptances", columns)

    op.create_table(
        "negotiation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("negotiation_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("terms_version", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "event_type in ('CREATED', 'TERMS_PROPOSED', 'TERMS_ACCEPTED', "
            "'AGREED', 'CANCELLED', 'REJECTED', 'CONTRACT_CREATED')",
            name="ck_negotiation_events_type",
        ),
        sa.CheckConstraint(
            "sequence_no >= 1",
            name="ck_negotiation_events_sequence",
        ),
        sa.ForeignKeyConstraint(
            ["negotiation_id"],
            ["contract_negotiations.id"],
            name="fk_negotiation_events_negotiation_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_negotiation_events_actor_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "negotiation_id",
            "sequence_no",
            name="uq_negotiation_events_sequence",
        ),
        sa.UniqueConstraint(
            "negotiation_id",
            "idempotency_key",
            name="uq_negotiation_events_idempotency",
        ),
    )
    for name, columns in (
        ("ix_negotiation_events_negotiation_id", ["negotiation_id"]),
        ("ix_negotiation_events_actor_user_id", ["actor_user_id"]),
        ("ix_negotiation_events_correlation_id", ["correlation_id"]),
    ):
        op.create_index(name, "negotiation_events", columns)

    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(
            sa.Column("negotiation_event_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_audit_logs_negotiation_event_id",
            "negotiation_events",
            ["negotiation_event_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "ix_audit_logs_negotiation_event_id",
            ["negotiation_event_id"],
        )

    with op.batch_alter_table("activity_notifications") as batch_op:
        batch_op.add_column(
            sa.Column("negotiation_event_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_activity_notifications_negotiation_event_id",
            "negotiation_events",
            ["negotiation_event_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_activity_notifications_negotiation_delivery",
            ["user_id", "negotiation_event_id", "template_key", "channel"],
        )
        batch_op.create_index(
            "ix_activity_notifications_negotiation_event_id",
            ["negotiation_event_id"],
        )


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM contract_negotiations")).scalar():
        raise RuntimeError(
            "Downgrade bloqueado: existen negociaciones que no pueden eliminarse."
        )

    with op.batch_alter_table("activity_notifications") as batch_op:
        batch_op.drop_index("ix_activity_notifications_negotiation_event_id")
        batch_op.drop_constraint(
            "uq_activity_notifications_negotiation_delivery",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_activity_notifications_negotiation_event_id",
            type_="foreignkey",
        )
        batch_op.drop_column("negotiation_event_id")

    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.drop_index("ix_audit_logs_negotiation_event_id")
        batch_op.drop_constraint(
            "fk_audit_logs_negotiation_event_id",
            type_="foreignkey",
        )
        batch_op.drop_column("negotiation_event_id")

    op.drop_table("negotiation_events")
    op.drop_table("negotiation_acceptances")
    op.drop_table("contract_negotiation_versions")
    op.drop_table("contract_negotiations")

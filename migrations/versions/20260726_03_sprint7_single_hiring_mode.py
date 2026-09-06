"""block proposal hiring mode multiple during sprint 7 phase 2a

Revision ID: 20260726_03
Revises: 20260726_02
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_03"
down_revision = "20260726_02"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "ck_proposal_requests_hiring_mode_single_phase2a"


def _check_constraints():
    inspector = sa.inspect(op.get_bind())
    return {
        constraint["name"]
        for constraint in inspector.get_check_constraints("proposal_requests")
        if constraint.get("name")
    }


def upgrade():
    bind = op.get_bind()
    invalid_count = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM proposal_requests "
            "WHERE hiring_mode IS NOT NULL AND hiring_mode <> 'SINGLE'"
        )
    ).scalar()
    if invalid_count:
        raise RuntimeError(
            "Migracion bloqueada: existen proposal_requests con hiring_mode "
            "distinto de SINGLE"
        )

    bind.execute(
        sa.text(
            "UPDATE proposal_requests SET hiring_mode = 'SINGLE' "
            "WHERE hiring_mode IS NULL"
        )
    )

    with op.batch_alter_table("proposal_requests") as batch_op:
        batch_op.alter_column(
            "hiring_mode",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default="SINGLE",
        )
        if CONSTRAINT_NAME not in _check_constraints():
            batch_op.create_check_constraint(
                CONSTRAINT_NAME,
                "hiring_mode = 'SINGLE'",
            )


def downgrade():
    if CONSTRAINT_NAME in _check_constraints():
        with op.batch_alter_table("proposal_requests") as batch_op:
            batch_op.drop_constraint(CONSTRAINT_NAME, type_="check")
